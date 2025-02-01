def onClick(event, frame):
    if event.inaxes is None:
        return
    
    click_x, click_y = event.xdata, event.ydata
    for node, (x, y) in frame.pos.items():
        if (click_x - x) ** 2 + (click_y - y) ** 2 < 0.01:
            print(f"Node {node} clicked!")

def onHover(event, frame):
    return 0
def onExpand(node):
    return 0