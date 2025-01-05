import tkinter as tk
from tkinter import messagebox
import on_start, visuals
import node

#define states so we know what layout to render
ON_START = 0
IN_PROGRESS = 1
COMPLETE = 2
state = ON_START

#initialise window
root = tk.Tk()
root.title("Gather")
root.geometry("800x600")

first_node = 0
if(state == ON_START):
    on_start.on_start(root)

elif(state == IN_PROGRESS):
        visuals.draw(root, first_node)
        #draw nodes
    
# Run the application
root.mainloop()