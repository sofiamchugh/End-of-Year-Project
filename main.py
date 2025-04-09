from tkinter import *
import customtkinter as ctk
from on_start import OnStartFrame
from visuals import GatherFrame
from node import Node
import json
import time
from queue import Queue
import azure.batch as batch
from azure.storage.blob import BlobServiceClient
import azure.batch.batch_auth as batch_auth
import azure.batch.models as batch_models
import threading
from urllib.parse import urlparse, urlunparse
from concurrent.futures import ThreadPoolExecutor
from gather import link_exists, get_relevance, find_links
import logging
logging.basicConfig(filename="log.txt",
                    filemode='w',
                    format='%(message)s',
                    level=logging.DEBUG)

ctk.set_appearance_mode("light") 

#Load in variables for connecting to Azure
def load_config():
    with open('config.json') as f:
        config = json.load(f)
    return config
config = load_config()

#Initialize blob service client
blob_service_client = BlobServiceClient.from_connection_string(config["azure-storage-connection-string"])

class App(ctk.CTk):
    def __init__(self):
            super().__init__()
            self.title("Gather")
            self.geometry("800x600")
            self.container = ctk.CTkFrame(self)
            self.container.grid(row=0, column=0, sticky="nsew")
            self.grid_rowconfigure(0, weight=1)
            self.grid_columnconfigure(0, weight=1)
            self.current_frame = "OnStartFrame"
            self.frames = {}
            self.futures = set()
            self.data_queue = Queue()
            self.seen = set()
            self.lock = threading.Lock()
            self.executor = ThreadPoolExecutor(max_workers = 3)
            self.init_frames()
            self.nodes = []
            self.job_start_time = 0
            self.batch_client = self.init_batch_client()
    
    
    
    def check_if_finished(self):
        all_done = all(f.done() for f in self.futures.copy())
        if all_done:
            job_end_time = time.time()
            print(f"Job took {job_end_time - self.job_start_time} seconds. Processed {len(self.seen)}")
        # Do any post-processing here
        else:
            self.after(500, self.check_if_finished)

    def init_frames(self):
        """Each frame is a class that defines a Custom TKInter layout and the relevant functions."""
        self.frames["OnStart"] = OnStartFrame(parent=self.container, controller=self, data_queue=self.data_queue, seen=self.seen)
        self.frames["Gathering"] = GatherFrame(parent=self.container, controller=self, data_queue=self.data_queue)
        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame("OnStart")

    def show_frame(self, frame_name):
        """Change which layout is active."""
        frame = self.frames[frame_name]
        frame.tkraise()
        self.current_frame = frame_name

    def init_batch_client(self):
        """Initialize Azure Batch client."""
        credentials = batch_auth.SharedKeyCredentials(config["azure-batch-account-name"], config["azure-batch-account-key"])
        return batch.BatchServiceClient(credentials, config["azure-batch-account-url"])

    def download_blob(self, blob_name):
        """Download blobs from Azure and converts them to nodes to be displayed in-app. """

        blob_client = blob_service_client.get_blob_client(container=config["container-name"], blob=blob_name)
        downloaded_blob = blob_client.download_blob() #Download blob from Azure container
        node_data = json.loads(downloaded_blob.readall()) #Parse JSON object
        node = Node(node_data['url'], node_data['parent']) #Initialize Node object
        node.set_relevance(node_data['relevance']) 
        node.set_content(node_data['content'])
        self.data_queue.put(node) #Put node in queue to be added to graph

        #turn links into child nodes if they aren't already
        for link in node_data['links']:
            with self.lock:
                if(link_exists(link, self.seen)==False):
                    self.seen.add(link)
                    child = node.Node(link, node)
                    node.add_child(child)

        return node
    
    def gather(self, first_node, keywords, job_id):
    
        def create_task(node):
            """Creates the task that executes worker.py in an Azure VM node."""
            task_id = f"task-{node.url.replace('https://', '').replace('/', '_').replace('.', '-')}"
            command =  f"worker.py {node.url} {node.parent} {keywords}" #this is what gets passed to the VM
            return batch_models.TaskAddParameter(id=task_id, command_line=command)

        def process_children(node, task_list):
            """Recursively processes child nodes, starting with the root."""
            for child in node.children:
                task = create_task(child) 
                task_list.append(task)
                process_children(child, task_list)

        def download_blob_wrapper(task):
            """Some pre-processing before we can use executor.map to download blobs."""
            node_url = task.id.replace('task-', '').replace('_', '/').replace('-', '.') #reformat the URL into task ID
            blob_name = f"{node_url}.html" 
            return self.download_blob(blob_name)
        
        """Create a job and add it to our Azure Batch Client."""
        job = batch_models.JobAddParameter(
            id=job_id, pool_info=batch_models.PoolInformation(pool_id=config["pool-id"])
        )
        self.batch_client.job.add(job)
        
        """The root node needs to be populated before we can start the recursive process_children function"""
        first_blob_name = f"{first_node.url}.html"
        first_task = create_task(first_node)
        self.batch_client.task.add(job_id, first_task)
        first_node = self.download_blob(first_blob_name) #first_node now has children

        """The rest of the webpage is processed recursively."""
        tasks = [] 
        process_children(first_node, tasks)

        if tasks:
            self.batch_client.task.add_collection(job_id, tasks)

        with ThreadPoolExecutor(max_workers=5) as executor:
            nodes = list(executor.map(download_blob_wrapper, tasks))

    def on_closing(self):
        """Cleanup when closing window."""
        job_list = list(self.batch_client.job.list())  # Get all jobs

        for job in job_list:
            print(f"Deleting job: {job.id}") 
            self.batch_client.job.delete(job.id) #delete job when done

        for after_id in self.tk.call('after', 'info'):
            self.after_cancel(after_id) 
        self.unbind_all("<Destroy>") 
        self.quit()

"""App runs here"""
app = App()
app.protocol("WM_DELETE_WINDOW", app.on_closing)
app.mainloop()