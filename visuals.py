import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import networkx as nx


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
        self.ani = animation.FuncAnimation(self.fig, self.poll_data, interval=1000, cache_frame_data=False)  # Update every second
        
    def poll_data(self, frame=None):
        if not self.is_running:
            return
        try:
            while not self.data_queue.empty():
                print("polling!")
                data = self.data_queue.get_nowait()
                if data is None:
                    return
                self.G.add_node(data.url)
                print(f"Added node {data.url} to G")
                if (data.parent.url != 0):
                    self.G.add_edge(data.url, data.parent.url)
                    print(f"With edge {data.parent.url}")
            if len(self.G.nodes) > 0:
                print("drawing")
                if not self.pos:  # If pos is still empty (first time layout is calculated)
                    self.pos = nx.spring_layout(self.G, seed=42)
                    print(f"Initial layout calculated: {self.pos}")
                self.pos = nx.spring_layout(self.G, pos=self.pos, iterations=5)
                print(f"Positions of nodes: {self.pos}")
                self.ax.clear()
                nx.draw(self.G, self.pos, ax=self.ax, with_labels=False, node_color='lightblue', edge_color='gray')
                self.canvas.draw()
        except Exception:
            pass
        
                

       
    def stop_gathering(self):
        """Stop the data gathering process and clear the queue."""
        self.is_running = False
        
        with self.data_queue.mutex:
            self.data_queue.queue.clear()