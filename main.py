import tkinter as tk
from tkinter import *
import customtkinter as ctk
from on_start import OnStartFrame
from visuals import GatherFrame
import node
import json
import time
from queue import Queue
from bs4 import BeautifulSoup
import azure.batch as batch
from azure.storage.blob import BlobServiceClient
import azure.batch.batch_auth as batch_auth
import azure.batch.models as batch_models
import threading
from concurrent.futures import ThreadPoolExecutor
from gather import link_exists
from azure_config import command, load_config

ctk.set_appearance_mode("light")

config = load_config()

class App(ctk.CTk):
    def __init__(self):
            super().__init__()
            self.title("Gather")
            self.geometry("800x600")
            self.container = ctk.CTkFrame(self)
            self.container.grid(row=0, column=0, sticky="nsew")
            self.grid_rowconfigure(0, weight=1)
            self.grid_columnconfigure(0, weight=1)
            self.current_frame = "OnStart"
            self.frames = {}
            self.data_queue = Queue()
            self.seen = set()
            self.lock = threading.Lock()
            #self.executor = ThreadPoolExecutor(max_workers = 3)
            self.init_frames()
            self.nodes = []
            self.batch_client = self.init_batch_client()

    def init_frames(self):
          self.frames["OnStart"] = OnStartFrame(parent=self.container, controller=self, data_queue=self.data_queue, seen=self.seen)
          self.frames["Gathering"] = GatherFrame(parent=self.container, controller=self, data_queue=self.data_queue)
          for frame in self.frames.values():
                frame.grid(row=0, column=0, sticky="nsew")
          self.show_frame("OnStart")

    def show_frame(self, frame_name):
      frame = self.frames[frame_name]
      frame.tkraise()
      self.current_frame = frame_name

    def init_batch_client(self):
        """Initialize Azure Batch client"""
        credentials = batch_auth.SharedKeyCredentials(config["azure-batch-account-name"], config["azure-batch-account-key"])
        return batch.BatchServiceClient(credentials, config["azure-batch-account-url"])

    
    def download_blob(self, blob_name):
        """Downloads data from Azure Blob Storage"""

        blob_service_client = BlobServiceClient.from_connection_string(config["azure-storage-connection-string"])
        blob_client = blob_service_client.get_blob_client(container=config["container-name"], blob=blob_name)

        downloaded_blob = blob_client.download_blob()
        node_data = json.loads(downloaded_blob.readall())
        print(f"Downloaded node {node_data['url']}\n")
        node = node.Node(node_data['url'], node_data['parent'])
        node.set_relevance(node_data['relevance'])
        node.set_content(node_data['content'])
        self.data_queue.put(node)

        for link in node_data['links']:
            with self.lock:
                if(link_exists(link, self.seen)==False):
                    self.seen.add(link)
                    child = node.Node(link, node)
                    node.add_child(child)

        return node
    
    def gather(self, first_node, keywords, job_id, homepage_url):
    
        def create_task(node):
            task_id = f"task-{node.url.replace('https://', '').replace('/', '_').replace('.', '-')}"
            output_file = f"{task_id}.json"
            #command_line = command + f" {node.url} {node.parent} {keywords} {homepage_url} {output_file} )"
            return batch_models.TaskAddParameter(id=task_id, command_line=command)

        def process_children(node, task_list):
            for child in node.children:
                task = create_task(child)  # Create a task for this child
                task_list.append(task)
                process_children(child, task_list)

        def download_blob_wrapper(task):
            node_url = task.id.replace('task-', '').replace('_', '/').replace('-', '.')
            blob_name = f"{node_url}.html" 
            return self.download_blob(blob_name)
        

        job = batch_models.JobAddParameter(
            id=job_id, pool_info=batch_models.PoolInformation(pool_id=config["pool-id"])
        )
        
        self.batch_client.job.add(job)
        
        first_blob_name = f"{first_node.url}.html"
        first_task = create_task(first_node)
        self.batch_client.task.add(job_id, first_task)
        first_node = self.download_blob(first_blob_name)
        print("downloaded node 1")

        tasks = []
        process_children(first_node, tasks)

        if tasks:
            self.batch_client.task.add_collection(job_id, tasks)


        with ThreadPoolExecutor(max_workers=5) as executor:
            nodes = list(executor.map(download_blob_wrapper, tasks))

    def on_closing(self):
        #cleanup when closing window
        job_list = list(self.batch_client.job.list())  # Get all jobs

        for job in job_list:
            print(f"Deleting job: {job.id}")
            self.batch_client.job.delete(job.id)

        for after_id in self.tk.call('after', 'info'):
            self.after_cancel(after_id) 
        self.unbind_all("<Destroy>")
        self.quit()

app = App()
app.protocol("WM_DELETE_WINDOW", app.on_closing)
app.mainloop()