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
    if direction == 'E' or direction == 'W':
        return r
    elif direction == 'NE' or direction == 'SW':
        return q
    elif direction == 'NW' or direction == 'SE':
        return q + r
    else:
        # Default/fallback, treat as E
        return r

class AmoebotStructure:
    def __init__(self):
        # Graph will store each amoebot as a node with attributes
        self.graph = nx.Graph()
        # For storing Matplotlib patches and texts to update them easily
        self.patches = {}
        self.texts = {}

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
            color = 'lightblue'
            poly = RegularPolygon((x, y), numVertices=6, radius=radius,
                                  orientation=orientation, facecolor=color, edgecolor='k')
            ax.add_patch(poly)
            self.patches[node] = poly
            # Label each hex with the node ID (or something else).
            t = ax.text(x, y, str(node), ha='center', va='center', fontsize=9, color='k')
            self.texts[node] = t

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
            self._add_edges_from_axial()
            print(f"Loaded model from {filename}")
        except Exception as e:
            print(f"Error loading file {filename}: {e}")

    def run_all_stripes(self, ax, direction='E', delay=0.8):
        # Precompute each node's directional coordinate for quick lookup
        dir_coords = {}
        for node, data in self.graph.nodes(data=True):
            q, r = data['axial']
            dir_coords[node] = directional_coord(q, r, direction)

        # We'll iterate over each node as the "reference."
        # In each iteration, we color the axis that goes through that reference in lime.
        node_list = sorted(self.graph.nodes())
        for ref in node_list:
            # 1) Mark the axis
            ref_val = dir_coords[ref]
            for node in node_list:
                if dir_coords[node] == ref_val:
                    self.patches[node].set_facecolor('lime')
                    self.texts[node].set_text("1")
                else:
                    self.patches[node].set_facecolor('lightblue')
                    self.texts[node].set_text("0")
            ax.figure.canvas.draw()
            plt.pause(delay)

        # Optionally, revert to original coloring at the end
        for node in node_list:
            self.patches[node].set_facecolor('lightblue')
            self.texts[node].set_text(str(node))
        ax.figure.canvas.draw()
        print("All stripes displayed for direction:", direction)

# ----------- GUI / Main Code -----------

def run_stripes_button_callback(event):
    direction = text_box.text.upper().strip()  # read from the text box
    if direction not in ['E', 'W', 'NE', 'NW', 'SE', 'SW']:
        print("Invalid direction. Using 'E' by default.")
        direction = 'E'
    structure.run_all_stripes(ax, direction=direction, delay=0.8)

if __name__ == '__main__':
    structure = AmoebotStructure()
    
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        structure.load_from_file(filename, hex_size=1)
    else:
        # No file provided; use a default 5x5 grid.
        structure.create_hexagonal_grid(grid_width=5, grid_height=5, hex_size=1)
    
    fig, ax = structure.draw_structure(hex_size=1)

    # A TextBox for direction input:
    text_ax = plt.axes([0.75, 0.9, 0.2, 0.05])
    text_box = TextBox(text_ax, "Direction", initial="E")

    # A button to run the stripes on every node:
    button_ax = plt.axes([0.75, 0.8, 0.2, 0.06])
    button_stripe = Button(button_ax, "Run Stripe")
    button_stripe.on_clicked(run_stripes_button_callback)

    plt.show()
