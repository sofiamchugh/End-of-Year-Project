from tkinter import *
import customtkinter as ctk
from app.on_start import OnStartFrame
from app.sitemap import GatherFrame
from app.node import Node
import json
import time
from queue import Queue
import azure.batch as batch
from azure.storage.blob import BlobServiceClient
import azure.batch.batch_auth as batch_auth
import azure.batch.models as batch_models
from azure.batch.models import CreateTasksErrorException

import logging
from app.user_agent import UserAgent
from azure.azure_config import config, blob_to_data, init_batch_client, get_job_id, daemon_shutdown, create_task, submit_task
from util.util import make_safe_task_id, url_as_blob_name, clean_url
from app.job_manager import JobManager

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
            self.init_frames()
            self.data_queue = Queue()
            self.job_start_time = 0
            self.tasks_made = 0


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

    def orchestrate_workers(self, first_node):
        
        self.show_frame("Gathering")
        start_time = time.time()
        
        """Create a job with the JobManager class."""
        job_id = clean_url(first_node.url)
        job_manager = JobManager(self, job_id)
        job_manager.rules.init_from_url(first_node.url)
        job_manager.seen.add(first_node.url)

        """Create and submit first task - the rest will be handled recursively within the job manager."""
        first_task = job_manager.create_task(first_node)
        job_manager.submit_task(first_node.url, first_task) 

        """Periodically check if job is complete."""
        job_manager.check_if_finished(start_time, job_id)

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