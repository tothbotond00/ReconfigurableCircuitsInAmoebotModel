import sys

def main():
    if len(sys.argv) < 3:
        print("Usage: python ascii_to_axial.py <input_grid.txt> <output_model.txt>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    # Read the ASCII grid lines
    with open(input_file, 'r') as f:
        lines = [line.rstrip('\n') for line in f]

    # We'll interpret each row/col as part of an 'even-q vertical layout' for pointy-topped hexes.
    #
    # That means:
    #   q = column_index
    #   r = row_index - floor(q/2)
    #
    # For each '1' in the ASCII grid, we create a node with an incrementing node_id.

    node_id = 0
    nodes = []  # will store tuples of (node_id, q, r)

    row_count = len(lines)
    if row_count == 0:
        print("Error: input grid is empty.")
        sys.exit(1)

    col_count = len(lines[0])

    for row in range(row_count):
        if len(lines[row]) < col_count:
            # In case lines have varying lengths
            print(f"Warning: line {row} is shorter than expected.")
        for col in range(col_count):
            char = lines[row][col]
            if char == '1':
                # compute q, r in even-q vertical layout
                q = col
                r = row - (col // 2)
                nodes.append((node_id, q, r))
                node_id += 1

    # Write out the results
    with open(output_file, 'w') as out:
        out.write("# Example Amoebot Model File\n")
        out.write("# Each line: node_id, q, r\n")
        for (nid, q, r) in nodes:
            out.write(f"{nid},{q},{r}\n")

    print(f"Wrote {len(nodes)} nodes to {output_file}.")

if __name__ == '__main__':
    main()
