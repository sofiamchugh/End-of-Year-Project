import tkinter as tk
import customtkinter as ctk
from playwright.sync_api import sync_playwright

def onClick(event, frame, ax, fig):
    if event.inaxes is None:
        return
    
    click_x, click_y = event.xdata, event.ydata
    for node, (x, y) in frame.pos.items():
        if (click_x - x) ** 2 + (click_y - y) ** 2 < 0.01:
            popup = NodePopup(node)
            popup.show_window()
            
active_tooltip = None
def onHover(event, frame, ax, fig):
    if event.inaxes is None:
        return
    
    global active_tooltip
    found_node = False

    mouse_x, mouse_y = event.xdata, event.ydata
    for node, (x,y) in frame.pos.items():
        if(mouse_x - x)**2 + (mouse_y - y) ** 2 < 0.01:
            if not active_tooltip:
                active_tooltip = ToolTip(node)
                active_tooltip.show_tooltip(event, ax, fig)
            found_node = True
            break

    if active_tooltip and not found_node:
        active_tooltip.hide_tooltip()
        active_tooltip = None
    

class ToolTip:
    def __init__(self, node):
        self.node = node
        self.tooltip_window = None

    def show_tooltip(self, event=None, ax=None, fig=None):

        if self.tooltip_window:
            return
        
        if ax and fig:
            display_coords = ax.transData.transform((event.xdata, event.ydata))
            x_screen, y_screen = fig.canvas.get_tk_widget().winfo_rootx(), fig.canvas.get_tk_widget().winfo_rooty()
            x, y = int(display_coords[0] + x_screen), int(display_coords[1]+y_screen)

            self.tooltip_window = tk.Toplevel()
            self.tooltip_window.wm_overrideredirect(True)
            self.tooltip_window.wm_geometry(f"+{x + 10}+{y + 10}")

            label = ctk.CTkLabel(self.tooltip_window, text = self.node, padx=5, pady=2)
            label.pack()

    def hide_tooltip(self):
         if self.tooltip_window and isinstance(self.tooltip_window, tk.Toplevel):
            self.tooltip_window.destroy()
            self.tooltip_window = None

class NodePopup:
    def __init__(self, node):
        self.node = node
        self.window = None
    def show_window(self):
        if self.window:
            return
        self.window = ctk.CTkToplevel()
        self.window.title(f"Information")
        self.window.geometry("200x100")
        self.window.wm_transient()

        link_button = ctk.CTkButton(self.window, text="Follow link", command=self.open_url)
        save_button = ctk.CTkButton(self.window, text="Download contents of webpage", command=self.download)
        close_button = ctk.CTkButton(self.window, text="Close", command=self.window.destroy)
        link_button.pack(pady=5)
        save_button.pack(pady=5)
        close_button.pack(pady=5)

    
    def open_url(self):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch() 
                page = browser.new_page()
                page.goto(self.node.url)

        except Exception as e:
            print(f"Failed to open url: {e}")

    def download(self):
        return self.node.content