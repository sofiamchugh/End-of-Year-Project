import tkinter as tk
from tkinter import messagebox, ttk
import node, gather
from urllib.parse import urlparse

def get_homepage(url):
    """
    
    """
    try:
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid URL")
        # Construct the homepage URL
        homepage_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        return homepage_url
    except Exception as e:
        return f"Error: {e}"
    
class OnStartFrame(ttk.Frame):
    def __init__(self, parent, controller, data_queue, seen):
        super().__init__(parent)
        self.controller = controller
        self.data_queue = data_queue
        self.seen = seen

        url_label = ttk.Label(self, text="URL:")
        url_label.grid(row=0, column=0, padx=10, pady=10)
        self.url_entry = tk.Entry(self)
        self.url_entry.grid(row=0, column=1, padx=10, pady=10)

        keyword_label = ttk.Label(self, text="Email:")
        keyword_label.grid(row=1, column=0, padx=10, pady=10)
        self.keyword_entry = ttk.Entry(self)
        self.keyword_entry.grid(row=1, column=1, padx=10, pady=10)

        submit_button = ttk.Button(self, text="Go", command=self.submit_form)
        submit_button.grid(row=2, column=0, columnspan=2, pady=20)

    def submit_form(self):
        first_url = self.url_entry.get()
        keywords = self.keyword_entry.get()
        if not first_url :
            messagebox.showwarning("Validation Error", "All fields are required!")
        
        else:
            if not keywords :
                keywords = ["essay", "video"]
            #define the keywords array
            #define the first node
            homepage_url = get_homepage(first_url)
            firstNode = node.Node(first_url, 0)
            self.data_queue.put(firstNode)
            self.seen.add(first_url)
            self.controller.gather(firstNode, keywords, homepage_url)
            self.controller.show_frame("Gathering")
            return 1

    