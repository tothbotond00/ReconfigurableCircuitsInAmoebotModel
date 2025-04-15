import sys
import os

def convert_file(input_path, output_path):
    # Read the ASCII grid lines
    with open(input_path, 'r') as f:
        lines = [line.rstrip('\n') for line in f]

    node_id = 0
    nodes = []

    row_count = len(lines)
    if row_count == 0:
        print(f"Error: input grid {input_path} is empty.")
        return

    col_count = len(lines[0])

    for row in range(row_count):
        if len(lines[row]) < col_count:
            print(f"Warning: line {row} in {input_path} is shorter than expected.")
        for col in range(col_count):
            if col >= len(lines[row]):
                continue
            char = lines[row][col]
            if char == '1':
                q = col
                r = row - (col // 2)
                nodes.append((node_id, q, r))
                node_id += 1

    with open(output_path, 'w') as out:
        out.write("# Example Amoebot Model File\n")
        out.write("# Each line: node_id, q, r\n")
        for nid, q, r in nodes:
            out.write(f"{nid},{q},{r}\n")

    print(f"Processed {input_path} -> {output_path} ({len(nodes)} nodes)")


def main():
    if len(sys.argv) != 4:
        print("Usage: python ascii_to_axial_batch.py <input_dir> <output_dir> <file_count>")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    file_count = int(sys.argv[3])

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for i in range(file_count):
        input_file = os.path.join(input_dir, f"{i}.txt")
        output_file = os.path.join(output_dir, f"{i}.txt")
        if os.path.exists(input_file):
            convert_file(input_file, output_file)
        else:
            print(f"Skipping missing file: {input_file}")

if __name__ == '__main__':
    main()
