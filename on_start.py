import tkinter as tk
from tkinter import messagebox
import node, gather
def on_start(root):
    url_label = tk.Label(root, text="URL:")
    url_label.grid(row=0, column=0, padx=10, pady=10)
    url_entry = tk.Entry(root)
    url_entry.grid(row=0, column=1, padx=10, pady=10)

    keyword_label = tk.Label(root, text="Email:")
    keyword_label.grid(row=1, column=0, padx=10, pady=10)
    keyword_entry = tk.Entry(root)
    keyword_entry.grid(row=1, column=1, padx=10, pady=10)

    def submit_form():
        first_url = url_entry.get()
        keywords = keyword_entry.get()
        if not first_url :
            messagebox.showwarning("Validation Error", "All fields are required!")
        
        else:
            if not keywords :
                keywords = ["essay", "video"]
            #define the keywords array
            #define the first node
            firstNode = node.Node(first_url, 0)
            gather.gather(firstNode, keywords)
            return 1

    submit_button = tk.Button(root, text="Go", command=submit_form)
    submit_button.grid(row=2, column=0, columnspan=2, pady=20)