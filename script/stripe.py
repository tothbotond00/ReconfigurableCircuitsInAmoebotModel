import sys
import math
import networkx as nx
import time
import json

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

    def run_all_stripes(self, direction, index):

        start_time = time.time()

        ref_node = self.graph.nodes()[index]
        q_start, r_start = ref_node['axial']

        step_total = 0
        stripe_nodes = []
        for node, data in self.graph.nodes(data=True):
            q, r = data['axial']
            if directional_coord(q, r, direction) == directional_coord(q_start, r_start, direction):
                stripe_nodes.append(node)
                step_total += 1


        # Index of the reference node in the stripe_nodes list
        ref_index = stripe_nodes.index(index)

        end_time = time.time()


        return [step_total, start_time, end_time]


# ----------- GUI / Main Code -----------

def run_stripes_button_callback(dir, ind):
    direction_param = dir.upper().strip()
    if direction_param not in ['N', 'S', 'W', 'E', 'NE', 'NW', 'SE', 'SW']:
        print("Invalid direction. Using 'E' by default.")
        direction_param = 'E'
    index_param = int(ind.strip())
    results = structure.run_all_stripes(direction=direction_param, index=index_param)

    output = {
        "time": ((results[2] - results[1]) * 1000),
        "steps": results[0]
    }

    print(json.dumps(output))


if __name__ == '__main__':
    structure = AmoebotStructure()
    
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        direction = sys.argv[2]
        index = sys.argv[3]
        structure.load_from_file(filename, hex_size=1)

        run_stripes_button_callback(direction, index)

    else:
        exit()
