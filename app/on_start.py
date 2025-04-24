import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, ttk
import app.node as node
import validators
from util.util import process_url
from urllib.parse import urlparse
import time
import azure.batch.models as batch_models
from app.user_agent import UserAgent
    
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


        submit_button = ctk.CTkButton(self.inner_frame, text="Go", command=self.submit_form, width=50)
        submit_button.grid(row=0, column=2, columnspan=2, pady=20)

        self.url_entry.bind("<Control-z>", self.undo) 
        self.url_entry.bind("<Return>", self.submit_form) 
        self.url_entry.bind("<KeyRelease>", self.on_change)

    def undo(self, event=None):
        if self.text_history:
            self.text_history.pop()
            self.url_entry.delete(0, "end")

    def on_change(self, event=None):
        self.text_history.append(self.url_entry.get())

    def submit_form(self, event=None):
        first_url = self.url_entry.get()

        if not first_url : #check that a URL was provided
            messagebox.showwarning("Validation Error", "No URL found")
            return 0
        else:
            if not validators.url(first_url):
                messagebox.showwarning("Invalid URL", "Please enter a valid URL")
                return 0

        first_url = process_url(first_url)
        first_node = node.Node(first_url, None)
        self.controller.start_job(first_node)
        return 1

    