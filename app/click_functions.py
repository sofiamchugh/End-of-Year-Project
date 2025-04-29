import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import threading
from playwright.sync_api import sync_playwright

open_popups = {}
active_tooltip = None

def onClick(event, frame, ax, fig):
    if event.inaxes is None:
        return
    
    click_x, click_y = event.xdata, event.ydata
    for node, (x, y) in frame.pos.items():
        if (click_x - x) ** 2 + (click_y - y) ** 2 < 0.01:
            if node not in open_popups or not open_popups[node].is_open():
                popup = NodePopup(node)
                popup.show_window()
                open_popups[node] = popup
            break
            

def onHover(event, frame, ax, fig):
    if event.inaxes is None:
        return
    
    global active_tooltip
    found_node = False

    mouse_x, mouse_y = event.xdata, event.ydata
    for node, (x,y) in frame.pos.items():
        if(mouse_x - x)**2 + (mouse_y - y) ** 2 < 0.01:
            if not active_tooltip or active_tooltip.node != node:
                if active_tooltip:
                    active_tooltip.hide_tooltip(fig)
                active_tooltip = ToolTip(node, x, y)
                active_tooltip.show_tooltip( ax, fig)
            found_node = True
            break

    if active_tooltip and not found_node:
        active_tooltip.hide_tooltip(fig)
        active_tooltip = None
    

class ToolTip:
    def __init__(self, node, x, y):
        self.node = node
        self.data_x = x
        self.data_y = y
        self.annotation = None
        self._hide_timer = None

    def show_tooltip(self, ax, fig):
        if self._hide_timer:
            fig.canvas.get_tk_widget().after_cancel(self._hide_timer)
            self._hide_timer = None

        if self.annotation:
            self.annotation.set_visible(True)
        else:
            self.annotation = ax.annotate(
                self.node,
                xy=(self.data_x, self.data_y),
                xytext=(10, 10),
                textcoords='offset points',
                bbox=dict(boxstyle="round", fc="lightyellow", ec="gray"),
                arrowprops=dict(arrowstyle="->", color='gray'),
            )
        fig.canvas.draw_idle()

    def hide_tooltip(self, fig=None):
        # Wait 500ms before hiding the tooltip
        if self._hide_timer or not self.annotation:
            return

        def hide():
            if self.annotation:
                self.annotation.set_visible(False)
                self.annotation = None
            if fig:
                fig.canvas.draw_idle()

        self._hide_timer = fig.canvas.get_tk_widget().after(500, hide)

class NodePopup:
    def __init__(self, node):
        self.node = node
        self.window = None

    def is_open(self):
        return self.window is not None and self.window.winfo_exists()

    def show_window(self):
        if self.is_open():
            return
        self.window = ctk.CTkToplevel()
        self.window.title(f"Information")
        self.window.geometry("400x200")
        self.window.wm_transient()

        link_button = ctk.CTkButton(self.window, text="Follow link", command=lambda: self.open_url(False))
        save_button = ctk.CTkButton(self.window, text="Download contents of webpage", command=self.download)
        close_button = ctk.CTkButton(self.window, text="Close", command=self.window.destroy)
        link_button.pack(pady=5)
        save_button.pack(pady=5)
        close_button.pack(pady=5)

    
    def open_url(self, headless):
        print("opening a URL")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=headless) 
                page = browser.new_page()
                page.goto(self.node)
                return page, browser
        except Exception as e:
            print(f"Failed to open url: {e}")

    def download(self):
        url = self.node.replace('https://', '').replace('http://', '').replace('/', '_').replace('.', '_')
        page, browser = self.open_url(True)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")  # Scroll to the bottom
        page.wait_for_load_state()
        text = page.content()
        browser.close()

        filename = f"{url}.txt"
        f = open(filename, "w")
        f.write(text)
        messagebox.showwarning("Saved")