import tkinter as tk
def drawNode(node):
    return 0
def drawLink(parent, child):
    return 0
def drawExpand(parent):
    return 0

def drawRest(parent):
    if(len(parent.children) > 7):
        drawExpand(parent)
    else:
        for child in parent.children:
            drawNode(child)
            drawLink(parent, child)
            drawRest(child)

def draw(root, firstNode):
    drawNode(firstNode)
    drawRest(firstNode)

class GatherFrame(tk.Frame):
    def __init__(self, parent, controller, data_queue):
        super().__init__(parent)
        self.controller = controller
        self.data_queue = data_queue
        self.is_running = True
        #UI elements go here
        stop_button = tk.Button(self, text="Stop", command=self.stop_gathering)
        stop_button.pack(pady=10)
        
    def poll_data(self):
        if not self.is_running:
            return
        try:
            while True:
                data = self.data_queue.get_nowait()
                if data is None:
                    return
        except Exception:
            pass
        self.after(100, self.poll_data)

    def stop_gathering(self):
        """Stop the data gathering process and clear the queue."""
        self.is_running = False
        self.label.config(text="Data gathering stopped.")
        with self.data_queue.mutex:
            self.data_queue.queue.clear()