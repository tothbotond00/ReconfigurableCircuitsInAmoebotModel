import sys
import math
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.patches import RegularPolygon
from matplotlib.widgets import Button, TextBox
import time


# A helper dict that maps a direction keyword to the "coordinate function" used
# to determine which nodes share the same axis. For a triangular/hex grid in
# axial coordinates (q, r):
#   E  or W : nodes share the same 'r' value
#   NE or SW: nodes share the same 'q' value
#   NW or SE: nodes share the same 'q + r' value
# (You can adapt if your coordinate system differs.)
def directional_coord(q, r, direction):

    if direction == 'NE' or direction == 'SW':
        return r
    elif direction == 'NW' or direction == 'SE':
        return r + q
    elif direction == 'N' or direction == 'S':
        return q
    elif direction == 'W' or direction == 'E':
        return q + 2*r

pause = False

class AmoebotStructure:
    def __init__(self):
        # Graph will store each amoebot as a node with attributes
        self.graph = nx.Graph()
        # For storing Matplotlib patches and texts to update them easily
        self.patches = {}
        self.texts = {}
        self.pause = False

    def add_amoebot(self, amoebot_id, pos, axial):
        # Each node has:
        #  - pos: pixel coordinate
        #  - axial: axial coordinate (q, r)
        #  - stripe: bool used for marking in one step
        self.graph.add_node(amoebot_id, pos=pos, axial=axial, stripe=False)

    def add_connection(self, id1, id2):
        self.graph.add_edge(id1, id2)

    @staticmethod
    def axial_to_pixel(q, r, hex_size):
        x = hex_size * (3/2 * q)
        y = hex_size * (math.sqrt(3) * (r + q/2))
        return (x, y)

    def create_hexagonal_grid(self, grid_width, grid_height, hex_size=1):
        amoebot_id = 0
        for q in range(grid_width):
            for r in range(grid_height):
                pos = self.axial_to_pixel(q, r, hex_size)
                self.add_amoebot(amoebot_id, pos, (q, r))
                amoebot_id += 1

        # Connect neighbors
        axial_coords = {n: data['axial'] for n, data in self.graph.nodes(data=True)}
        neighbor_dirs = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]
        for node, (q, r) in axial_coords.items():
            for dq, dr in neighbor_dirs:
                qq, rr = q + dq, r + dr
                # Find a node with axial coords (qq, rr)
                # (We can do a small dictionary lookup if we invert axial_coords, but let's keep it simple)
                for other, (oq, or_) in axial_coords.items():
                    if oq == qq and or_ == rr:
                        if not self.graph.has_edge(node, other):
                            self.add_connection(node, other)
                        break

    def draw_structure(self, hex_size=1, draw_edges=True, ax=None):
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 8))
        else:
            fig = ax.figure

        ax.clear()
        self.patches.clear()
        self.texts.clear()

        orientation = math.radians(30)  # rotate 30° for flat-topped
        for node, data in self.graph.nodes(data=True):
            x, y = data['pos']
            radius = 1
            color = 'yellow'
            poly = RegularPolygon((x, y), numVertices=6, radius=radius,
                                  orientation=orientation, facecolor=color, edgecolor='k')
            ax.add_patch(poly)
            self.patches[node] = poly
            # Label each hex with the node ID (or something else).
            # t = ax.text(x, y, str(node), ha='center', va='center', fontsize=9, color='k')
            # self.texts[node] = t

        if draw_edges:
            for u, v in self.graph.edges():
                x1, y1 = self.graph.nodes[u]['pos']
                x2, y2 = self.graph.nodes[v]['pos']
                ax.plot([x1, x2], [y1, y2], 'k-', lw=0.8)

        all_x = [data['pos'][0] for _, data in self.graph.nodes(data=True)]
        all_y = [data['pos'][1] for _, data in self.graph.nodes(data=True)]
        margin = hex_size * 2
        ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
        ax.set_ylim(min(all_y) - margin, max(all_y) + margin)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title("Amoebot Hexagonal Grid")
        fig.canvas.draw()
        return fig, ax
    
    def load_from_file(self, filename, hex_size=1):
        self.graph.clear()
        try:
            with open(filename, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split(',')
                    if len(parts) < 3:
                        continue  # skip invalid lines
                    node_id = int(parts[0].strip())
                    q = int(parts[1].strip())
                    r = int(parts[2].strip())
                    pos = self.axial_to_pixel(q, r, hex_size)
                    self.add_amoebot(node_id, pos, (q, r))
            print(f"Loaded model from {filename}")
        except Exception as e:
            print(f"Error loading file {filename}: {e}")

    def run_pasc(self, ax, index, delay):
        button_pasc.set_active(False)
        button_reset.set_active(False)
        button_pasc.label.set_text("Running...")

        # Get the reference node
        ref_node = self.graph.nodes()[index]

        node_list = []

        for id, node in self.graph.nodes(data=True):
            node['primary'] = False
            node['secondary'] = False
            node['active'] = True
            node['bits'] = ""
            node_list.append(node)

        self.send_beep(node_list, ref_node, ax, delay)
        
    
    def send_beep(self, node_list, ref_node, ax, delay):


        ref_node_index = node_list.index(ref_node)
        ref_node['primary'] = True

        active_sum = 0
        for i in range(0, len(node_list)):
            if(node_list[i]['active']):
                active_sum += 1     

        #Color the ref node in red
        self.patches[ref_node_index].set_facecolor('red')
        ax.figure.canvas.draw()
        plt.pause(delay)
        time.sleep(delay)

        while active_sum != 1:
        
            #Beep from ref_node to right
            for i in range(ref_node_index + 1, len(node_list)):
                if(i != 0):
                    if(node_list[i-1]['primary'] == True and node_list[i]['active'] == True):
                        node_list[i]['primary'] = False
                        node_list[i]['secondary'] = True
                    elif(node_list[i-1]['primary'] == True and node_list[i]['active'] == False):
                        node_list[i]['primary'] = True
                        node_list[i]['secondary'] = False
                    elif(node_list[i-1]['secondary'] == True and node_list[i]['active'] == True):
                        node_list[i]['primary'] = True
                        node_list[i]['secondary'] = False
                    elif(node_list[i-1]['secondary'] == True and node_list[i]['active'] == False):
                        node_list[i]['primary'] = False
                        node_list[i]['secondary'] = True

                    #Blink color
                    original_color = self.patches[i].get_facecolor()
                    if(node_list[i]['primary'] == True):
                        self.patches[i].set_facecolor('orange')
                    else:
                        self.patches[i].set_facecolor('lime')
                    ax.figure.canvas.draw()
                    plt.pause(delay)
                    time.sleep(delay)
                    if pause:
                        while pause:
                            plt.pause(0.1)
                    self.patches[i].set_facecolor(original_color)
                    ax.figure.canvas.draw()
                    plt.pause(delay)
                    time.sleep(delay)
                    if pause:
                        while pause:
                            plt.pause(0.1)


            #Beep from ref_node to left
            for i in range(ref_node_index - 1, -1, -1):
                if(node_list[i+1]['primary'] == True and node_list[i+1]['active'] == True):
                    node_list[i]['primary'] = False
                    node_list[i]['secondary'] = True
                elif(node_list[i+1]['primary'] == True and node_list[i+1]['active'] == False):
                    node_list[i]['primary'] = True
                    node_list[i]['secondary'] = False
                elif(node_list[i+1]['secondary'] == True and node_list[i+1]['active'] == True):
                    node_list[i]['primary'] = True
                    node_list[i]['secondary'] = False
                elif(node_list[i+1]['secondary'] == True and node_list[i+1]['active'] == False):
                    node_list[i]['primary'] = False
                    node_list[i]['secondary'] = True
                
                #Blink color
                original_color = self.patches[i].get_facecolor()
                if(node_list[i]['primary'] == True):
                    self.patches[i].set_facecolor('orange')
                else:
                    self.patches[i].set_facecolor('lime')
                ax.figure.canvas.draw()
                plt.pause(delay)
                time.sleep(delay)
                if pause:
                    while pause:
                        plt.pause(0.1)

                self.patches[i].set_facecolor(original_color)
                ax.figure.canvas.draw()
                plt.pause(delay)
                time.sleep(delay)
                if pause:
                    while pause:
                        plt.pause(0.1)


            #Add bits
            for i in range(0, len(node_list)):
                if(node_list[i]['primary'] == True):
                    node_list[i]['bits'] = "0" + node_list[i]['bits']
                elif(node_list[i]['secondary'] == True):
                    node_list[i]['bits'] = "1" + node_list[i]['bits']

            for i in range(0, len(node_list)):
                if(node_list[i]['active'] and node_list[i]['secondary']==True):
                    node_list[i]['active'] = False
                node_list[i]['primary'] = False
                node_list[i]['secondary'] = False

            ref_node_index = node_list.index(ref_node)
            ref_node['primary'] = True


            active_sum = 0
            for i in range(0, len(node_list)):
                if(node_list[i]['active'] == True):
                    active_sum += 1
                else:
                    self.patches[i].set_facecolor('grey')
                    ax.figure.canvas.draw()
                    plt.pause(delay)
                    time.sleep(delay)
                    if pause:
                        while pause:
                            plt.pause(0.1)



            for node, data in self.graph.nodes(data=True):
                x, y = data['pos']

                # Ha a szöveg már létezik, először töröljük
                if node in self.texts:
                    self.texts[node].remove()
                    del self.texts[node]  # Töröljük a szótárból is, hogy ne maradjon hivatkozás

                # Új szöveg létrehozása és eltárolása
                t = ax.text(x, y, node_list[node]['bits'], ha='center', va='center', fontsize=11, color='k')
                self.texts[node] = t  # Frissítjük a tárolt szövegobjektumot

                ax.figure.canvas.draw()  # Az ábra frissítése
                plt.pause(delay)
                time.sleep(delay)
                if pause:
                    while pause:
                        plt.pause(0.1)


        button_reset.set_active(True)
        button_pasc.set_active(True)
        button_pasc.label.set_text("Run PASC")


# ----------- GUI / Main Code -----------

def run_pasc_button_callback(event):
    index = int(text_box_index.text.strip())  # read from the text box
    delay = float(text_box_delay.text.strip())  # read from the text box
    structure.run_pasc(ax, index=index, delay=delay)

def reset_colors_callback(event):
    for node in structure.graph.nodes():
        structure.patches[node].set_facecolor('yellow')
        if node in structure.texts:
            structure.texts[node].remove()
            del structure.texts[node]

    ax.figure.canvas.draw()

def pause_callback(event):
    global pause
    pause = not pause  # Toggle the pause state
    button_pause.label.set_text("Resume" if pause else "Pause")
    

if __name__ == '__main__':
    structure = AmoebotStructure()
    
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        structure.load_from_file(filename, hex_size=1)
    else:
        # No file provided; use a default 5x5 grid.
        structure.create_hexagonal_grid(grid_width=5, grid_height=5, hex_size=1)
    
    fig, ax = structure.draw_structure(hex_size=1)

    # A TeextBox for index input:
    text_ax_index = plt.axes([0.85, 0.93, 0.1, 0.05])
    text_box_index = TextBox(text_ax_index, "Index", initial="0")

    #Set delay
    text_ax_delay = plt.axes([0.85, 0.87, 0.1, 0.05])
    text_box_delay = TextBox(text_ax_delay, "Speed", initial="0.1")

    # A button to run the stripes on every node:
    button_ax = plt.axes([0.85, 0.80, 0.1, 0.06])
    button_pasc = Button(button_ax, "Run PASC")
    button_pasc.on_clicked(run_pasc_button_callback)

    # A button to reset the colors:
    button_reset_ax = plt.axes([0.85, 0.73, 0.1, 0.06])
    button_reset = Button(button_reset_ax, "Reset")
    button_reset.on_clicked(reset_colors_callback)

    #Pause
    button_pause_ax = plt.axes([0.85, 0.2, 0.1, 0.06])
    button_pause = Button(button_pause_ax, "Pause")
    button_pause.on_clicked(pause_callback)

    #Exit
    button_exit_ax = plt.axes([0.85, 0.1, 0.1, 0.06])
    button_exit = Button(button_exit_ax, "Exit")
    button_exit.on_clicked(lambda event: plt.close())


    legend_labels = ['Active', 'Inactive', 'Primary', 'Secondary']
    legend_colors = ['yellow', 'grey', 'orange', 'lime']

    ax.legend([plt.Line2D([0], [0], marker='o', color='w', label=label, markerfacecolor=color, markersize=10) for label, color in zip(legend_labels, legend_colors)], legend_labels, loc='upper left')

    plt.show()