import tkinter as tk
from tkinter import messagebox
import node, gather

class OnStartFrame(tk.Frame):
    def __init__(self, parent, controller, data_queue, seen):
        super().__init__(parent)
        self.controller = controller
        self.data_queue = data_queue
        self.seen = seen

        url_label = tk.Label(self, text="URL:")
        url_label.grid(row=0, column=0, padx=10, pady=10)
        self.url_entry = tk.Entry(self)
        self.url_entry.grid(row=0, column=1, padx=10, pady=10)

        keyword_label = tk.Label(self, text="Email:")
        keyword_label.grid(row=1, column=0, padx=10, pady=10)
        self.keyword_entry = tk.Entry(self)
        self.keyword_entry.grid(row=1, column=1, padx=10, pady=10)

        submit_button = tk.Button(self, text="Go", command=self.submit_form)
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
            firstNode = node.Node(first_url, 0)
            self.data_queue.put(firstNode)
            self.seen.add(firstNode)
            self.controller.gather(firstNode, keywords)
            self.controller.show_frame("Gathering")
            return 1

    