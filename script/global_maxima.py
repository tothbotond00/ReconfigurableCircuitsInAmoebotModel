#!/usr/bin/env python3
import json
import sys
import math
import networkx as nx
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



    def run_global_maxima(self, direction, index):

        start_time = time.time()
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

        # 1. Rendezd a sid kulcsokat növekvő sorrendbe
        sorted_sids = sorted(groups.keys())

        # 2. Készíts egy leképezést az eredeti sid értékekhez:
        sid_mapping = {old_sid: new_sid for new_sid, old_sid in enumerate(sorted_sids)}

        # 3. Hozd létre az új groups dictionary-t
        new_groups = {sid_mapping[old_sid]: groups[old_sid] for old_sid in sorted_sids}

        # 4. Opcionálisan felülírhatod az eredetit
        groups = new_groups



        results = self.send_beep(index, groups)

        end_time = time.time()

        results.append(start_time)
        results.append(end_time)

        return results

    def send_beep(self, ref_node_index, groups):

        find_key = [k for k, v in groups.items() if any(item['node'] == ref_node_index for item in v)]
        for item in groups.get(find_key[0], []): item['primary'] = True

        active_sum = 0
        for i in [*groups]:
            if(groups[i][0]['active'] == True):
                active_sum += 1


        # count the pasc algorithm steps, for all stripes at once and every
        step_total = 0
        step_all_lines = 0
        pasc_iterations = 0

        while active_sum != 1:
            pasc_iterations += 1
        
            #Beep from ref_node to right
            for i in range(find_key[0] + 1, len(groups)):
                if(i != 0):
                    step_all_lines += 1
                    if(groups[i-1][0]['primary'] == True and groups[i][0]['active'] == True):
                        for item in groups.get(i, []):
                            item['primary'] = False
                            step_total += 1
                        for item in groups.get(i, []):
                            item['secondary'] = True
                    elif(groups[i-1][0]['primary'] == True and groups[i][0]['active'] == False):
                        for item in groups.get(i, []):
                            item['primary'] = True
                            step_total += 1
                        for item in groups.get(i, []):
                            item['secondary'] = False
                    elif(groups[i-1][0]['secondary'] == True and groups[i][0]['active'] == True):
                        for item in groups.get(i, []):
                            item['primary'] = True
                            step_total += 1
                        for item in groups.get(i, []):
                            item['secondary'] = False
                    elif(groups[i-1][0]['secondary'] == True and groups[i][0]['active'] == False):
                        for item in groups.get(i, []):
                            item['primary'] = False
                            step_total += 1
                        for item in groups.get(i, []):
                            item['secondary'] = True

                    #print(f"PASC iterations: {pasc_iterations}, Stripe steps: {step_all_lines}, Total steps: {step_total}")



            #Beep from ref_node to left
            for i in range(find_key[0] - 1, -1, -1):
                step_all_lines += 1
                if(groups[i+1][0]['primary'] == True and groups[i+1][0]['active'] == True):
                    for item in groups.get(i, []):
                        item['primary'] = False
                        step_total += 1
                    for item in groups.get(i, []):
                        item['secondary'] = True
                elif(groups[i+1][0]['primary'] == True and groups[i+1][0]['active'] == False):
                    for item in groups.get(i, []):
                        item['primary'] = True
                        step_total += 1
                    for item in groups.get(i, []):
                        item['secondary'] = False
                elif(groups[i+1][0]['secondary'] == True and groups[i+1][0]['active'] == True):
                    for item in groups.get(i, []):
                        item['primary'] = True
                        step_total += 1
                    for item in groups.get(i, []):
                        item['secondary'] = False
                elif(groups[i+1][0]['secondary'] == True and groups[i+1][0]['active'] == False):
                    for item in groups.get(i, []):
                        item['primary'] = False
                        step_total += 1
                    for item in groups.get(i, []):
                        item['secondary'] = True

                #print(f"PASC iterations: {pasc_iterations}, Stripe steps: {step_all_lines}, Total steps: {step_total}")



        
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

        return [pasc_iterations, step_all_lines, step_total]
       





# --- Main Code ---

def run_global_max_button(dir, ind):
    direction_param = dir.upper().strip()
    if direction_param not in ['N','S','E','W','NE','NW','SE','SW']:
        print("Invalid direction. Using 'N' by default.")
        direction_param = 'N'
    index_param = int(ind.strip())
    results = structure.run_global_maxima(direction=direction_param, index=index_param)

    #print(f"Execution time: {((results[4] - results[3])*1000):.3f} milliseconds")
    #print(f"End, PASC iterations: {results[0]}, Stripe steps: {results[1]}, Total steps: {results[2]}")

    output = {
        "time": ((results[4] - results[3])*1000),
        "iterations": results[0],
        "stripe_steps": results[1],
        "total_steps": results[2]
    }

    print(json.dumps(output))




if __name__ == '__main__':
    structure = AmoebotStructure()
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        direction = sys.argv[2]
        index = sys.argv[3]
        structure.load_from_file(filename, hex_size=1)

        run_global_max_button(direction, index)

    else:
        exit()


