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

    def run_pasc(self, index):
        start_time = time.time()
        # Get the reference node
        ref_node = self.graph.nodes()[index]

        node_list = []

        for id, node in self.graph.nodes(data=True):
            node['primary'] = False
            node['secondary'] = False
            node['active'] = True
            node['bits'] = ""
            node_list.append(node)

        results = self.send_beep(node_list, ref_node)

        end_time = time.time()

        results.append(start_time)
        results.append(end_time)

        print(results)

        return results
        
    
    def send_beep(self, node_list, ref_node):


        ref_node_index = node_list.index(ref_node)
        ref_node['primary'] = True

        active_sum = 0
        for i in range(0, len(node_list)):
            if(node_list[i]['active']):
                active_sum += 1

        # count the pasc algorithm steps, for all stripes at once and every
        step_total = 0
        pasc_iterations = 0

        while active_sum != 1:
            pasc_iterations += 1
        
            #Beep from ref_node to right
            for i in range(ref_node_index + 1, len(node_list)):
                if(i != 0):
                    if(node_list[i-1]['primary'] == True and node_list[i]['active'] == True):
                        node_list[i]['primary'] = False
                        node_list[i]['secondary'] = True
                        step_total += 1
                    elif(node_list[i-1]['primary'] == True and node_list[i]['active'] == False):
                        node_list[i]['primary'] = True
                        node_list[i]['secondary'] = False
                        step_total += 1
                    elif(node_list[i-1]['secondary'] == True and node_list[i]['active'] == True):
                        node_list[i]['primary'] = True
                        node_list[i]['secondary'] = False
                        step_total += 1
                    elif(node_list[i-1]['secondary'] == True and node_list[i]['active'] == False):
                        node_list[i]['primary'] = False
                        node_list[i]['secondary'] = True
                        step_total += 1


            #Beep from ref_node to left
            for i in range(ref_node_index - 1, -1, -1):
                if(node_list[i+1]['primary'] == True and node_list[i+1]['active'] == True):
                    node_list[i]['primary'] = False
                    node_list[i]['secondary'] = True
                    step_total += 1
                elif(node_list[i+1]['primary'] == True and node_list[i+1]['active'] == False):
                    node_list[i]['primary'] = True
                    node_list[i]['secondary'] = False
                    step_total += 1
                elif(node_list[i+1]['secondary'] == True and node_list[i+1]['active'] == True):
                    node_list[i]['primary'] = True
                    node_list[i]['secondary'] = False
                    step_total += 1
                elif(node_list[i+1]['secondary'] == True and node_list[i+1]['active'] == False):
                    node_list[i]['primary'] = False
                    node_list[i]['secondary'] = True
                    step_total += 1


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

        return [pasc_iterations, step_total]

# ----------- GUI / Main Code -----------

def run_pasc_button(ind):
    index_param = int(ind.strip())

    results = structure.run_pasc(index=index_param)

    # print(f"Execution time: {((results[4] - results[3])*1000):.3f} milliseconds")
    # print(f"End, PASC iterations: {results[0]}, Stripe steps: {results[1]}, Total steps: {results[2]}")

    output = {
        "time": ((results[3] - results[2]) * 1000),
        "iterations": results[0],
        "steps": results[1]
    }

    print(json.dumps(output))


if __name__ == '__main__':
    structure = AmoebotStructure()
    
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        index = sys.argv[2]
        structure.load_from_file(filename, hex_size=1)

        run_pasc_button(index)
    else:
        exit()

