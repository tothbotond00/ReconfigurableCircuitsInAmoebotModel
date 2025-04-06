#!/usr/bin/env python3
import sys
import math
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.patches import RegularPolygon
from matplotlib.widgets import Button, TextBox
import time

# --- Helper functions ---

def stripe_id(axial, direction):
    q, r = axial
    if direction in ['N', 'S']:
        return q
    elif direction in ['NE', 'SW']:
        return r
    elif direction in ['NW', 'SE']:
        return q + r
    elif direction in ['E', 'W']:
        return  q + 2*r
    else:
        return q  # default

def candidate_value(pos, direction):
    x, y = pos
    if direction == 'N':
        return y
    elif direction == 'S':
        return -y
    elif direction == 'E':
        return x
    elif direction == 'W':
        return -x
    elif direction == 'NE':
        return x + y
    elif direction == 'SW':
        return -(x + y)
    elif direction == 'NW':
        return -x + y
    elif direction == 'SE':
        return x - y
    else:
        return y

# --- Main Class ---

class AmoebotStructure:
    def __init__(self):
        # The graph holds each amoebot node and its attributes.
        self.graph = nx.Graph()
        # Dictionaries for the matplotlib patch objects and text labels.
        self.patches = {}
        self.texts = {}

    def add_amoebot(self, amoebot_id, pos, axial):
        # Each node stores its pixel position, its axial coordinate.
        self.graph.add_node(amoebot_id, pos=pos, axial=axial)

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

        # Connect neighbors using the standard six directions.
        axial_coords = {n: data['axial'] for n, data in self.graph.nodes(data=True)}
        neighbor_dirs = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]
        for node, (q, r) in axial_coords.items():
            for dq, dr in neighbor_dirs:
                qq, rr = q + dq, r + dr
                for other, (oq, or_) in axial_coords.items():
                    if oq == qq and or_ == rr:
                        if not self.graph.has_edge(node, other):
                            self.add_connection(node, other)
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
                        continue
                    node_id = int(parts[0].strip())
                    q = int(parts[1].strip())
                    r = int(parts[2].strip())
                    pos = self.axial_to_pixel(q, r, hex_size)
                    self.add_amoebot(node_id, pos, (q, r))
            self._add_edges_from_axial()
            print(f"Loaded model from {filename}")
        except Exception as e:
            print(f"Error loading file {filename}: {e}")

    def _add_edges_from_axial(self):
        axial_coords = {n: data['axial'] for n, data in self.graph.nodes(data=True)}
        neighbor_dirs = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]
        for node, (q, r) in axial_coords.items():
            for dq, dr in neighbor_dirs:
                qq, rr = q + dq, r + dr
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

        orientation = math.radians(30)  # for flat‐topped hexagons
        for node, data in self.graph.nodes(data=True):
            x, y = data['pos']
            radius = 1
            poly = RegularPolygon((x, y), numVertices=6, radius=radius,
                                  orientation=orientation, facecolor='lightblue', edgecolor='k')
            ax.add_patch(poly)
            self.patches[node] = poly
            # Label nodes initially with their ID.
            t = ax.text(x, y, str(node), ha='center', va='center', fontsize=9, color='black')
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

    def run_global_maxima(self, ax, direction, delay=0.5):
        # Step 1: Group nodes into stripes.
        groups = {}
        for node, data in self.graph.nodes(data=True):
            sid = stripe_id(data['axial'], direction)
            groups.setdefault(sid, []).append(node)
        print("Stripe groups (by stripe ID):")
        for sid in sorted(groups.keys()):
            print(f"Stripe {sid}: {groups[sid]}")

        # Step 2: For each stripe, choose the local maximum candidate.
        candidates = []
        for sid, nodes in groups.items():
            best = max(nodes, key=lambda n: candidate_value(self.graph.nodes[n]['pos'], direction))
            candidates.append(best)
        print("Local candidates from each stripe:", candidates)

        # Step 3: Tournament elimination rounds.
        round_num = 1
        current_candidates = candidates[:]
        while len(current_candidates) > 1:
            new_candidates = []
            print(f"Round {round_num}: Candidates = {current_candidates}")
            i = 0
            while i < len(current_candidates):
                if i == len(current_candidates) - 1:
                    new_candidates.append(current_candidates[i])
                    self.patches[current_candidates[i]].set_facecolor('cyan')
                    ax.figure.canvas.draw()
                    plt.pause(delay)
                    i += 1
                else:
                    c1 = current_candidates[i]
                    c2 = current_candidates[i+1]
                    self.patches[c1].set_facecolor('orange')
                    self.patches[c2].set_facecolor('orange')
                    ax.figure.canvas.draw()
                    plt.pause(delay)
                    val1 = candidate_value(self.graph.nodes[c1]['pos'], direction)
                    val2 = candidate_value(self.graph.nodes[c2]['pos'], direction)
                    if val1 >= val2:
                        winner = c1
                        loser = c2
                    else:
                        winner = c2
                        loser = c1
                    self.patches[loser].set_facecolor('grey')
                    self.patches[winner].set_facecolor('red')
                    ax.figure.canvas.draw()
                    plt.pause(delay)
                    new_candidates.append(winner)
                    i += 2
            current_candidates = new_candidates
            round_num += 1

        # Step 4: Highlight global maximum.
        global_max = current_candidates[0]
        print("Global maximum candidate:", global_max, "with value", candidate_value(self.graph.nodes[global_max]['pos'], direction))
        self.patches[global_max].set_facecolor('magenta')
        self.texts[global_max].set_text(f"Max\n{candidate_value(self.graph.nodes[global_max]['pos'], direction):.2f}")
        ax.figure.canvas.draw()
        plt.pause(delay)

    def reset_colors(self, ax):
        for node in self.graph.nodes():
            self.patches[node].set_facecolor('lightblue')
            self.texts[node].set_text(str(node))
        ax.figure.canvas.draw()

# --- GUI / Main Code ---

def run_global_max_button_callback(event):
    direction = text_box_direction.text.upper().strip()
    if direction not in ['N','S','E','W','NE','NW','SE','SW']:
        print("Invalid direction. Using 'N' by default.")
        direction = 'N'
    try:
        delay = float(text_box_delay.text.strip())
    except:
        delay = 0.5
    structure.run_global_maxima(ax, direction=direction, delay=delay)

def reset_colors_callback(event):
    structure.reset_colors(ax)

if __name__ == '__main__':
    structure = AmoebotStructure()
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        structure.load_from_file(filename, hex_size=1)
    else:
        structure.create_hexagonal_grid(grid_width=5, grid_height=5, hex_size=1)

    fig, ax = structure.draw_structure(hex_size=1)

    # TextBox for entering direction.
    text_ax_direction = plt.axes([0.75, 0.9, 0.2, 0.05])
    text_box_direction = TextBox(text_ax_direction, "Direction", initial="N")
    # TextBox for delay (speed) setting.
    text_ax_delay = plt.axes([0.75, 0.84, 0.2, 0.05])
    text_box_delay = TextBox(text_ax_delay, "Speed", initial="0.5")

    # Button to run the global maximum demonstration.
    button_ax = plt.axes([0.85, 0.75, 0.1, 0.06])
    button_global_max = Button(button_ax, "Global Max")
    button_global_max.on_clicked(run_global_max_button_callback)

    # Button to reset colors.
    button_reset_ax = plt.axes([0.85, 0.68, 0.1, 0.06])
    button_reset = Button(button_reset_ax, "Reset Colors")
    button_reset.on_clicked(reset_colors_callback)

    plt.show()
