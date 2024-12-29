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