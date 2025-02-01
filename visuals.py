import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import networkx as nx
import numpy as np
from click_functions import onClick, onHover


class GatherFrame(ttk.Frame):
    def __init__(self, parent, controller, data_queue):
        super().__init__(parent)
        self.controller = controller
        self.data_queue = data_queue
        self.is_running = True
        self.G = nx.Graph()
        self.pos = {}
        self.fig, self.ax = plt.subplots(figsize=(6, 6))
        self.ax.set_axis_off()
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.ani = animation.FuncAnimation(self.fig, self.poll_data, interval=200, cache_frame_data=False)  # Update every second
        self.fig.canvas.mpl_connect("button_press_event", lambda event: onClick(event, self))
        self.animated_nodes = {}
    def poll_data(self, frame=None):
        if not self.is_running:
            return
        try:
            nodesCount = len(self.G.nodes)
            while not self.data_queue.empty():
                data = self.data_queue.get_nowait()
                if data is None:
                    return
                if data.url not in self.G.nodes:
                    self.G.add_node(data.url)
                    if (data.parent != 0):
                        self.G.add_edge(data.url, data.parent.url)
                    self.animated_nodes[data.url] = True
                else:
                    self.animated_nodes[data.url] = False 
            if len(self.G.nodes) > 0:
                if not self.pos:  
                    #first time layout is calculated
                    self.pos = nx.spring_layout(self.G, seed=42)
                    print(f"Initial layout calculated: {self.pos}")
                if(nodesCount < len(self.G.nodes)):
                    #only recalculate layout if new nodes have been added
                    self.pos = nx.spring_layout(self.G, pos=self.pos, iterations=5)
                node_sizes = []
                for node in self.G.nodes:
                    if self.animated_nodes.get(node, False):
                        node_sizes.append(100 + 50 * np.sin(frame * 2 * np.pi / 50))
                        print(f"this one is animated {node}")
                    else:
                        node_sizes.append(100)
                print(node_sizes)
                self.ax.clear()
                nx.draw(self.G, self.pos, ax=self.ax, with_labels=False, node_color='lightblue', edge_color='gray', node_size = node_sizes)
                self.canvas.draw()
        except Exception as e:
                print(f"UI error {e}")

       
    def stop_gathering(self):
        """Stop the data gathering process and clear the queue."""
        self.is_running = False
        
        with self.data_queue.mutex:
            self.data_queue.queue.clear()