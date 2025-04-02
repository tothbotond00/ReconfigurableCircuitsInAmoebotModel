import sys
import math 
import networkx as nx 
import matplotlib.pyplot as plt 
from matplotlib.patches import RegularPolygon
from matplotlib.widgets import Button 
import time

class AmoebotStructure: 
    def __init__(self): 
        # The graph holds each amoebot as a node. 
        # # Node attributes: 'pos' (a tuple with (x,y) coordinates) and 'state' (for example, 'active') 
        self.graph = nx.Graph()
        self.patches = {}
        
    def add_amoebot(self, amoebot_id, pos, state='active'):
        # Each node has a 'pos' (tuple), a 'state' ('active' or 'passive'),
        # and an 'identifier' (list of bits computed over iterations).
        self.graph.add_node(amoebot_id, pos=pos, state=state, identifier=[])

    def add_connection(self, id1, id2):
        self.graph.add_edge(id1, id2)

    @staticmethod
    def axial_to_pixel(q, r, hex_size):
        x = hex_size * (3/2 * q)
        y = hex_size * (math.sqrt(3) * (r + q/2))
        return (x, y)

    def create_hexagonal_grid(self, grid_width, grid_height, hex_size=1):
        amoebot_id = 0
        # Create nodes for axial coordinates (q, r)
        for q in range(grid_width):
            for r in range(grid_height):
                pos = self.axial_to_pixel(q, r, hex_size)
                self.add_amoebot(amoebot_id, pos)
                amoebot_id += 1

        axial_coords = {}
        nodes = list(self.graph.nodes(data=True))
        index = 0
        for q in range(grid_width):
            for r in range(grid_height):
                node_id, data = nodes[index]
                axial_coords[node_id] = (q, r)
                index += 1

        neighbor_dirs = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]
        for node, (q, r) in axial_coords.items():
            for dq, dr in neighbor_dirs:
                # Search for a node with coordinates (q+dq, r+dr)
                for other_node, (oq, or_) in axial_coords.items():
                    if oq == q + dq and or_ == r + dr:
                        if not self.graph.has_edge(node, other_node):
                            self.add_connection(node, other_node)
                        break
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

    def draw_structure(self, hex_size=1, draw_edges=True, ax=None):
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 8))
        else:
            fig = ax.figure

        # Clear previous patches.
        self.patches.clear()
        ax.clear()

        # Orientation for flat-topped hexagons (30° rotation so the top is horizontal).
        orientation = math.radians(30)
        for node, data in self.graph.nodes(data=True):
            x, y = data['pos']
            # Choose a radius that fits nicely.
            radius = 1
            color = 'lightblue' if data['state'] == 'active' else 'gray'
            hexagon = RegularPolygon((x, y), numVertices=6, radius=radius,
                                    orientation=orientation, facecolor=color, edgecolor='k')
            ax.add_patch(hexagon)
            self.patches[node] = hexagon
            # Draw node id text.
            ax.text(x, y, str(node), ha='center', va='center', fontsize=8)

        if draw_edges:
            for u, v in self.graph.edges():
                x1, y1 = self.graph.nodes[u]['pos']
                x2, y2 = self.graph.nodes[v]['pos']
                ax.plot([x1, x2], [y1, y2], 'k-', lw=0.8)

        # Set limits.
        all_x = [data['pos'][0] for node, data in self.graph.nodes(data=True)]
        all_y = [data['pos'][1] for node, data in self.graph.nodes(data=True)]
        margin = hex_size * 2
        ax.set_xlim(min(all_x)-margin, max(all_x)+margin)
        ax.set_ylim(min(all_y)-margin, max(all_y)+margin)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title("Amoebot Hexagonal Grid – PASC Simulation")
        fig.canvas.draw()
        return fig, ax

    def run_PASC_simulation(self, ax, delay=1):
        # Get nodes in chain order (by node id).
        chain = sorted(self.graph.nodes(), key=lambda x: x)
        # Reset states and identifiers.
        for node in chain:
            self.graph.nodes[node]['state'] = 'active'
            self.graph.nodes[node]['identifier'] = []

        iteration = 0
        while True:
            iteration += 1
            bits = {}
            # Reference node always gets bit 0.
            bits[chain[0]] = 0
            # Propagate along the chain order.
            for i in range(1, len(chain)):
                node = chain[i]
                prev = chain[i-1]
                if self.graph.nodes[node]['state'] == 'active':
                    bits[node] = 1 - bits[prev]
                else:
                    bits[node] = bits[prev]
            # Record each node's bit.
            for node in chain:
                self.graph.nodes[node]['identifier'].append(bits[node])
            # Determine which nodes (except the reference) become passive.
            any_change = False
            for i in range(1, len(chain)):
                node = chain[i]
                if self.graph.nodes[node]['state'] == 'active' and bits[node] == 1:
                    self.graph.nodes[node]['state'] = 'passive'
                    any_change = True
            # Update colors.
            for node in chain:
                if self.graph.nodes[node]['state'] == 'active':
                    self.patches[node].set_facecolor('lightblue' if bits[node] == 0 else 'orange')
                else:
                    self.patches[node].set_facecolor('gray')
            ax.figure.canvas.draw()
            plt.pause(delay)
            # Debug: print current identifiers.
            id_strs = {node: "".join(str(bit) for bit in self.graph.nodes[node]['identifier']) for node in chain}
            print(f"Iteration {iteration}: {id_strs}")
            if not any_change:
                print("PASC simulation completed.")
                break
def run_pasc(event):
    structure.run_PASC_simulation(ax, delay=1)

# Visualize the structure.
structure = AmoebotStructure()
if len(sys.argv) > 1:
    filename = sys.argv[1]
    structure.load_from_file(filename, hex_size=1)
else:
    # No file provided; use a default 5x5 grid.
    structure.create_hexagonal_grid(grid_width=5, grid_height=5, hex_size=1)
fig, ax = structure.draw_structure()
# Add a button to run the PASC algorithm.
button_ax = plt.axes([0.80, 0.05, 0.15, 0.075])  # Adjust position as needed.
button = Button(button_ax, 'Run PASC')
button.on_clicked(run_pasc)

plt.show()