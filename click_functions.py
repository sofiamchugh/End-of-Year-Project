import tkinter as tk
import customtkinter as ctk
def onClick(event, frame):
    if event.inaxes is None:
        return
    
    click_x, click_y = event.xdata, event.ydata
    for node, (x, y) in frame.pos.items():
        if (click_x - x) ** 2 + (click_y - y) ** 2 < 0.01:
            print(f"Node {node} clicked!")
            
active_tooltip = None
def onHover(event, frame):
    if event.inaxes is None:
        return
    
    global active_tooltip
    found_node = False

    mouse_x, mouse_y = event.xdata, event.ydata
    for node, (x,y) in frame.pos.items():
        if(mouse_x - x)**2 + (mouse_y - y) ** 2 < 0.01:
            if not active_tooltip:
                active_tooltip = ToolTip(node)
                active_tooltip.show_tooltip(event)
            found_node = True
            break

    if active_tooltip and not found_node:
        active_tooltip.hide_tooltip()
        active_tooltip = None
    


class ToolTip:
    def __init__(self, node):
        self.node = node
        self.tooltip_window = None

    def show_tooltip(self, event=None):

        if self.tooltip_window:
            return
        
        self.tooltip_window = tk.Toplevel()
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{event.x + 10}+{event.y + 10}")

        label = ctk.CTkLabel(self.tooltip_window, text = self.node, padx=5, pady=2)
        label.pack()

    def hide_tooltip(self):
         if self.tooltip_window and isinstance(self.tooltip_window, tk.Toplevel):
            self.tooltip_window.destroy()
            self.tooltip_window = None