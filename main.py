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
import logging
from user_agent import UserAgent
from azure_config import config, blob_to_data, init_batch_client, get_job_id, url_as_blob_name

ctk.set_appearance_mode("light") 


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
            self.job_start_time = 0
            self.batch_client = init_batch_client()
            self.rules = UserAgent()


    def check_if_finished(self, start_time, job_id):
        all_done = all(f.done() for f in self.futures.copy())
        if all_done:
            job_end_time = time.time()
            print(f"Job took {job_end_time - start_time} seconds. Processed {len(self.seen)}")
            task_id = "shutdown"
            command_line = """/bin/bash -c'/mnt/batch/tasks/shared/venv/bin/python3 /mnt/batch/tasks/shared/repo/shutdown.py'"""
            task = batch_models.TaskAddParameter(id=task_id, command_line=command_line)
            self.batch_client.task.add(job_id, task)
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

    def update_crawl_delay(self, new_delay, crawl_delay):
        """This function ensures that if multiple workers with the same crawl_delay value 
        need to increase the delay, that this only updates the user agent rules once."""

        if new_delay > crawl_delay:
            current_delay = self.rules.crawl_delay
            with self.lock:
                if current_delay == crawl_delay:
                    self.rules.crawl_delay = new_delay

    def process_azure_info(self, blob_name):
        """Download blobs from Azure and converts them to nodes to be displayed in-app. """

        data = blob_to_data(blob_name) #downloads blob from azure
        node = Node(self, None)
        
        node.node_from_json(data, self.seen, self.lock, self.rules)
        print(f"adding {node.url} to data queue")
        self.data_queue.put(node) # Put node in queue to be added to graph

        new_delay = data["crawl_delay"] 
        return node, new_delay
    
    def orchestrate_workers(self, first_node, keywords):
        self.show_frame("Gathering")
        start_time = time.time()
        print(f"Starting orchestrator. Time: {start_time}\n")
        def create_task(node):
            """Creates the task that executes worker.py in an Azure VM node."""
            task_id = f"task-{node.url.replace('https://', '').replace('/', '_').replace('.', '-')}"
            crawl_delay = self.rules.crawl_delay
            command_line = f"""/bin/bash -c '
export PLAYWRIGHT_BROWSERS_PATH=/mnt/batch/tasks/shared/playwright-browsers && \
/mnt/batch/tasks/shared/venv/bin/python3 /mnt/batch/tasks/shared/repo/worker.py {node.url} {node.parent} {keywords} {crawl_delay}'
"""
            return batch_models.TaskAddParameter(id=task_id, command_line=command_line)

        def process_children(node, task_list):
            """Recursively processes child nodes, starting with the root."""
            for child in node.children:
                print(f"creating task for {child.url}")
                task = create_task(child) 
                task_list.append(task)
                process_children(child, task_list)

        def get_blob(task):
            """Some pre-processing before we can use executor.map to download blobs."""
            node_url = task.id.replace('task-', '').replace('_', '/').replace('-', '.') #reformat the URL into task ID
            blob_name = url_as_blob_name(node_url)
            node, new_delay = self.process_azure_info(blob_name)
            self.update_crawl_delay(new_delay, self.rules.crawl_delay)
            return node
        
        """Create a job and add it to our Azure Batch Client."""
        try: 
            job_id = get_job_id(first_node.url, self.batch_client)
            job = batch_models.JobAddParameter(
                id=job_id, pool_info=batch_models.PoolInformation(pool_id=config["pool-id"])
            )
            self.batch_client.job.add(job)
        except Exception as e:
            print(f"Failed to create job: {e}")
        
        """The root node needs to be populated before we can start the recursive process_children function"""
        first_blob_name = url_as_blob_name(first_node.url)
        self.seen.add(first_node.url)
        first_task = create_task(first_node)
        self.batch_client.task.add(job_id, first_task)
        first_node = self.process_azure_info(first_blob_name)[0] #first_node now has children

        """The rest of the webpage is processed recursively."""
        tasks = [] 
        process_children(first_node, tasks)

        if tasks:
            self.batch_client.task.add_collection(job_id, tasks)

        with self.executor as executor:
            self.futures = list(executor.map(get_blob, tasks))
        
        self.check_if_finished(start_time)

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
if __name__ =="__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()