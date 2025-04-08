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

pause = False

class AmoebotStructure:
    def __init__(self):
        # The graph holds each amoebot node and its attributes.
        self.graph = nx.Graph()
        # Dictionaries for the matplotlib patch objects and text labels.
        self.patches = {}
        self.texts = {}
        self.pause = False

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
            print(f"Loaded model from {filename}")
        except Exception as e:
            print(f"Error loading file {filename}: {e}")

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
            color = 'yellow'
            poly = RegularPolygon((x, y), numVertices=6, radius=radius,
                                  orientation=orientation, facecolor=color, edgecolor='k')
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

    def run_global_maxima(self, ax, direction, delay, index):

        button_pasc.set_active(False)
        button_reset.set_active(False)
        button_pasc.label.set_text("Running...")
        # Step 1: Group nodes into stripes.
        groups = {}
        alternate_direction = ''
        if(direction == 'N' or direction == 'S'): alternate_direction = 'E'
        elif(direction == 'E' or direction == 'W'): alternate_direction = 'N'
        elif(direction == 'NE' or direction == 'SW'): alternate_direction = 'NW'
        elif(direction == 'NW' or direction == 'SE'): alternate_direction = 'NE'
        sid_count = 0
        unique_sids = []
        for node, data in self.graph.nodes(data=True):
            sid = stripe_id(data['axial'], alternate_direction)
            if sid not in unique_sids:
                unique_sids.append(sid)
        print(unique_sids)
        sid_count = len(unique_sids)
        if(direction in ('S', 'W', 'SW', 'SE')):
            for node, data in self.graph.nodes(data=True):
                sid = stripe_id(data['axial'], alternate_direction)
                sid = sid_count - sid - 1
                groups.setdefault(sid, []).append({'node': node, 'primary': False, 'secondary': False, 'active': True, 'bits': ""})
        else:
            for node, data in self.graph.nodes(data=True):
                sid = stripe_id(data['axial'], alternate_direction)
                groups.setdefault(sid, []).append({'node': node, 'primary': False, 'secondary': False, 'active': True, 'bits': ""})

        print(groups)
        # 1. Rendezd a sid kulcsokat növekvő sorrendbe
        sorted_sids = sorted(groups.keys())

        # 2. Készíts egy leképezést az eredeti sid értékekhez:
        sid_mapping = {old_sid: new_sid for new_sid, old_sid in enumerate(sorted_sids)}

        # 3. Hozd létre az új groups dictionary-t
        new_groups = {sid_mapping[old_sid]: groups[old_sid] for old_sid in sorted_sids}

        # 4. Opcionálisan felülírhatod az eredetit
        groups = new_groups

        print(groups)




        self.send_beep(index, ax, delay, groups)

    def send_beep(self, ref_node_index, ax, delay, groups):

        find_key = [k for k, v in groups.items() if any(item['node'] == ref_node_index for item in v)]
        for item in groups.get(find_key[0], []): item['primary'] = True

        active_sum = 0
        for i in [*groups]:
            if(groups[i][0]['active'] == True):
                active_sum += 1

        #Color the ref node in red
        self.patches[ref_node_index].set_facecolor('red')
        ax.figure.canvas.draw()
        plt.pause(delay)
        time.sleep(delay)

        while active_sum != 1:
        
            #Beep from ref_node to right
            for i in range(find_key[0] + 1, len(groups)):
                if(i != 0):
                    if(groups[i-1][0]['primary'] == True and groups[i][0]['active'] == True):
                        for item in groups.get(i, []): item['primary'] = False
                        for item in groups.get(i, []): item['secondary'] = True
                    elif(groups[i-1][0]['primary'] == True and groups[i][0]['active'] == False):
                        for item in groups.get(i, []): item['primary'] = True
                        for item in groups.get(i, []): item['secondary'] = False
                    elif(groups[i-1][0]['secondary'] == True and groups[i][0]['active'] == True):
                        for item in groups.get(i, []): item['primary'] = True
                        for item in groups.get(i, []): item['secondary'] = False
                    elif(groups[i-1][0]['secondary'] == True and groups[i][0]['active'] == False):
                        for item in groups.get(i, []): item['primary'] = False
                        for item in groups.get(i, []): item['secondary'] = True


                    #Blink color
                    original_color = self.patches[groups.get(i, [])[0]['node']].get_facecolor()
                    if(groups[i][0]['primary'] == True):
                        node_ids = [item['node'] for item in groups.get(i, [])]
                        for item in node_ids:
                            self.patches[item].set_facecolor('orange')
                    else:
                        node_ids = [item['node'] for item in groups.get(i, [])]
                        for item in node_ids:
                            self.patches[item].set_facecolor('lime')
                    ax.figure.canvas.draw()
                    plt.pause(delay)
                    time.sleep(delay)
                    if pause:
                        while pause:
                            plt.pause(0.1)

                    node_ids = [item['node'] for item in groups.get(i, [])]
                    for item in node_ids:
                        self.patches[item].set_facecolor(original_color)
                    ax.figure.canvas.draw()
                    plt.pause(delay)
                    time.sleep(delay)
                    if pause:
                        while pause:
                            plt.pause(0.1)



            #Beep from ref_node to left
            for i in range(find_key[0] - 1, -1, -1):
                if(groups[i+1][0]['primary'] == True and groups[i+1][0]['active'] == True):
                    for item in groups.get(i, []): item['primary'] = False
                    for item in groups.get(i, []): item['secondary'] = True
                elif(groups[i+1][0]['primary'] == True and groups[i+1][0]['active'] == False):
                    for item in groups.get(i, []): item['primary'] = True
                    for item in groups.get(i, []): item['secondary'] = False
                elif(groups[i+1][0]['secondary'] == True and groups[i+1][0]['active'] == True):
                    for item in groups.get(i, []): item['primary'] = True
                    for item in groups.get(i, []): item['secondary'] = False
                elif(groups[i+1][0]['secondary'] == True and groups[i+1][0]['active'] == False):
                    for item in groups.get(i, []): item['primary'] = False
                    for item in groups.get(i, []): item['secondary'] = True

                
                #Blink color
                original_color = self.patches[groups.get(i, [])[0]['node']].get_facecolor()
                if(groups[i][0]['primary'] == True):
                    node_ids = [item['node'] for item in groups.get(i, [])]
                    for item in node_ids:
                        self.patches[item].set_facecolor('orange')
                else:
                    node_ids = [item['node'] for item in groups.get(i, [])]
                    for item in node_ids:
                        self.patches[item].set_facecolor('lime')
                ax.figure.canvas.draw()
                plt.pause(delay)
                time.sleep(delay)
                if pause:
                    while pause:
                        plt.pause(0.1)


                node_ids = [item['node'] for item in groups.get(i, [])]
                for item in node_ids:
                    self.patches[item].set_facecolor(original_color)
                ax.figure.canvas.draw()
                plt.pause(delay)
                time.sleep(delay)
                if pause:
                    while pause:
                        plt.pause(0.1)

        
            # Add bits
            for i in [*groups]:
                if(groups[i][0]['primary'] == True):
                    for item in groups.get(i, []): item['bits'] = "0" + item['bits']
                elif(groups[i][0]['secondary'] == True):
                    for item in groups.get(i, []): item['bits'] = "1" + item['bits']

                if(groups[i][0]['active'] == True and groups[i][0]['secondary'] == True):
                    for item in groups.get(i, []): item['active'] = False
                for item in groups.get(i, []): item['primary'] = False
                for item in groups.get(i, []): item['secondary'] = False

            for item in groups.get(find_key[0], []): item['primary'] = True


            


            active_sum = 0
            for i in [*groups]:
                if(groups[i][0]['active'] == True):
                    active_sum += 1
                else:
                    for item in groups.get(i, []):
                        self.patches[item['node']].set_facecolor('grey')
                    ax.figure.canvas.draw()
                    plt.pause(delay)
                    time.sleep(delay)
                    if pause:
                        while pause:
                            plt.pause(0.1)



            for i in [*groups]:
                for item in groups.get(i, []):
                    for node, data in self.graph.nodes(data=True):
                        if(item['node'] == node):
                            x, y = data['pos']
                            if node in self.texts:
                                self.texts[node].remove()
                                del self.texts[node]
                            t = ax.text(x, y, item['bits'], ha='center', va='center', fontsize=11, color='k')
                            self.texts[node] = t
                    ax.figure.canvas.draw()
                    plt.pause(delay)
                    time.sleep(delay)   
                    if pause:
                        while pause:
                            plt.pause(0.1)
       

        button_reset.set_active(True)
        button_pasc.set_active(True)
        button_pasc.label.set_text("Run PASC")



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
    index = int(text_box_index.text.strip())
    structure.run_global_maxima(ax, direction=direction, delay=delay, index=index)

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
        structure.create_hexagonal_grid(grid_width=5, grid_height=5, hex_size=1)

    fig, ax = structure.draw_structure(hex_size=1)

    # TextBox for entering direction.
    text_ax_direction = plt.axes([0.85, 0.93, 0.1, 0.05])
    text_box_direction = TextBox(text_ax_direction, "Direction", initial="N")

    # A TeextBox for index input:
    text_ax_index = plt.axes([0.85, 0.86, 0.1, 0.05])
    text_box_index = TextBox(text_ax_index, "Index", initial="5")

    #Set delay
    text_ax_delay = plt.axes([0.85, 0.79, 0.1, 0.05])
    text_box_delay = TextBox(text_ax_delay, "Speed", initial="0.5")

    # A button to run the stripes on every node:
    button_ax = plt.axes([0.85, 0.72, 0.1, 0.05])
    button_pasc = Button(button_ax, "Run PASC")
    button_pasc.on_clicked(run_global_max_button_callback)

    # A button to reset the colors:
    button_reset_ax = plt.axes([0.85, 0.65, 0.1, 0.05])
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
