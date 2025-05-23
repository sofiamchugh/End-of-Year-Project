import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import networkx as nx
import customtkinter as ctk
import numpy as np
from click_functions import onClick, onHover


class GatherFrame(ctk.CTkFrame):
    def __init__(self, parent, controller, data_queue):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        self.data_queue = data_queue
        self.is_running = True
        self.G = nx.Graph()
        self.pos = {}
        self.fig, self.ax = plt.subplots(figsize=(6, 6))
        self.ax.set_axis_off()
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.ani = animation.FuncAnimation(self.fig, self.poll_data, interval=200, cache_frame_data=False)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.fig.canvas.mpl_connect("button_press_event", lambda event: onClick(event, self, self.ax, self.fig))
        self.fig.canvas.mpl_connect("motion_notify_event", lambda event: onHover(event, self, self.ax, self.fig))
        self.stop_button = ctk.CTkButton(self, text="Stop", command=self.stop_gathering)
        self.stop_button.pack(side=tk.BOTTOM, pady=10)

        
    def poll_data(self, frame=None):
        """
        Each node is added to a data queue when it has been fully processed. 
        This function renders nodes as part of the sitemap as they are added to the queue.
        """
        if not self.is_running:
            return
        try:
            nodes_count = len(self.G.nodes)
            if not self.data_queue.empty():
                print("Found node in data queue")
                data = self.data_queue.get_nowait() #get nodes from queue
                if data is None:
                    return
                if data.url is None:
                    return
                if data.url not in self.G.nodes: #double check there is no node with this URL already
                    self.G.add_node(data.url)
                    if (data.parent is not None): #this is just for the root node, which has no parent
                        self.G.add_edge(data.url, data.parent) #all other nodes should have edges
               
            #node_size = 100 for nodes 0-50, 70 for 50-100, 50 for 100-200, 30 for 200 onwards
            if nodes_count < 50:
                node_size = 100
            elif nodes_count < 100:
                node_size = 70
            elif nodes_count < 200:
                node_size = 50
            else:
                node_size = 30
        
            if len(self.G.nodes) > 0:
                if not self.pos:  
                    #we initialize the layout differently from how we update it
                    self.pos = nx.spring_layout(self.G, seed=42)
                
                if(nodes_count < len(self.G.nodes)):
                    #recalculate layout if new nodes have been added
                    self.pos = nx.spring_layout(self.G, pos=self.pos, iterations=5)
                
                #render changes
                self.ax.clear()

                nx.draw(self.G, self.pos, ax=self.ax, with_labels=False, node_color='orange', edge_color='gray', node_size = node_size)
                self.canvas.draw()


        except Exception as e:
                print(f"UI error {e}")

       
    def stop_gathering(self):
        """Stop the data gathering process and clear the queue."""
        self.is_running = False
        with self.data_queue.mutex:
            self.data_queue.queue.clear()
        self.ax.clear()
        self.controller.show_frame("OnStart")
        