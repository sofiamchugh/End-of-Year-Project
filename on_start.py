import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, ttk
import node, gather
from gather import url_is_valid, process_url
from urllib.parse import urlparse
import time
import azure.batch.models as batch_models
    
def get_job_id(url, batch_client):
    """Names the job according to the supplied URL and checks that it does not exist already."""
    job_id = f"gather-job-{url.replace('https://', '').replace('/', '_').replace('.', '-')}"

    try:
        existing_job = batch_client.job.get(job_id)  # Check if job exists
        print(f"Deleting existing job: {job_id}")
        batch_client.job.delete(job_id)  # Delete the existing job
        while True:
            try:
                batch_client.job.get(job_id)  # Check if job still exists
                print(f"Waiting for job {job_id} to be deleted...")
                time.sleep(5)  # Wait before checking again
            except batch_models.BatchErrorException:
                print(f"Job {job_id} deleted successfully.")
                break
    except batch_models.BatchErrorException as e:
        if "The specified job does not exist" in str(e):
            pass  
        else:
            raise  

    return job_id


class KeywordEntryWidget(ctk.CTkFrame):
    """Custom CTK widget for adding and removing keywords."""
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.keywords  = []
        self.widgets = []
        self.entry = ctk.CTkEntry(self, placeholder_text="Add keywords")
        self.entry.bind("<KeyRelease>", self.check_input)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def check_input(self, event):
        text = self.entry.get()
        if text.endswith(", "):
            keyword = text[:-2].strip()
            if keyword:
                self.add_keyword(keyword)
                self.entry.delete(0, "end")

    def add_keyword(self, keyword):
        if keyword in self.keywords:
            return
        
        self.keywords.append(keyword)
        keyword_frame = ctk.CTkFrame(self, fg_color="darkgrey")
        keyword_frame.pack(side=tk.LEFT, padx=5, pady=2)

        keyword_label = ctk.CTkLabel(keyword_frame, text=keyword)
        keyword_label.pack(side=tk.LEFT, padx = 5)

        remove = ctk.CTkButton(keyword_frame, text="x", width=20, height=20, hover_color="red", command=lambda: self.remove_keyword(keyword, keyword_frame))
        remove.pack(side=tk.LEFT, padx=3)

        self.widgets.append(keyword_frame)

    def remove_keyword(self, keyword,keyword_frame):
        keyword_frame.destroy()
        self.keywords.remove(keyword)
        self.widgets.remove(keyword_frame)

    def get_keywords(self):
        if not self.keywords:
            text = self.entry.get()
            if not text:
                return None
            else:
                self.add_keyword(text)
                return self.keywords
        else:
            return self.keywords

class OnStartFrame(ctk.CTkFrame):
    """The frame for the layout that displays when app is first opened 
    or when a gathering process is stopped/finished."""
    def __init__(self, parent, controller, data_queue, seen):
        super().__init__(parent)

        self.text_history = []
        self.controller = controller
        self.data_queue = data_queue
        self.seen = seen

        self.grid(row=0, column=0, sticky="nsew")
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0,weight=1)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.inner_frame=ctk.CTkFrame(self)
        self.inner_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.inner_frame.rowconfigure(0, weight=0)
        self.inner_frame.rowconfigure(1, weight=0)
        self.inner_frame.columnconfigure(0, weight=1)
        self.inner_frame.columnconfigure(1, weight=1)
        self.inner_frame.columnconfigure(2, weight=1)

        self.url_entry = ctk.CTkEntry(self.inner_frame, placeholder_text="Enter a URL here")
        self.url_entry.grid(row=0, column=0, columnspan=2, padx=10, sticky="ew")

        self.keyword_entry = KeywordEntryWidget(self.inner_frame)
        self.keyword_entry.grid(row=1, column=0, columnspan=2, padx=10, sticky="ew")

        submit_button = ctk.CTkButton(self.inner_frame, text="Go", command=self.submit_form, width=50)
        submit_button.grid(row=0, column=2, columnspan=2, pady=20)

        self.url_entry.bind("<Control-z>", self.undo) 
        self.url_entry.bind("<Return>", self.submit_form) 
        self.keyword_entry.bind("<Return>", self.submit_form)
        self.url_entry.bind("<KeyRelease>", self.on_change)

    def undo(self, event=None):
        if self.text_history:
            self.text_history.pop()
            self.url_entry.delete(0, "end")

    def on_change(self, event=None):
        self.text_history.append(self.url_entry.get())

    def submit_form(self, event=None):
        first_url = self.url_entry.get()
        keywords = self.keyword_entry.get_keywords()

        if not first_url : #check that a URL was provided
            messagebox.showwarning("Validation Error", "All fields are required!")
            return 0
        else:
            if not url_is_valid(first_url):
                messagebox.showwarning("Invalid URL", "Please enter a valid URL")
                return 0
            #define the keywords array
            #define the first node
       # self.controller.show_frame("Gathering")
        first_url = process_url(first_url)
        first_node = node.Node(first_url, None)
        job_id = get_job_id(first_node.url, self.controller.batch_client)
        self.controller.gather(first_node, keywords)
        return 1

    