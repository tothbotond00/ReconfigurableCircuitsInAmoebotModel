import os
import subprocess
import csv
import json

# Configuration
folder1 = "tests100"
folder2 = "tests100icycle"
program1 = "python global_maxima.py"  # or "./program_a" for compiled binaries
program2 = "python global_maxima.py"
output_csv = "results_100_2.csv"


# Utility to run a program and capture metrics
def run_program(cmd, input_path):
    result = subprocess.run(f"{cmd} {input_path}", shell=True, capture_output=True, text=True)

    return result

# Prepare CSV
with open(output_csv, mode="w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "file","executionTime","iterations","stripeSteps","totalSteps","executionTimeIcycle","iterationsIcycle","stripeStepsIcycle","totalStepsIcycle"
    ])

    for file in sorted(os.listdir(folder1)):
        path1 = os.path.join(folder1, file)
        path2 = os.path.join(folder2, file)


        argument1 = path1 + " N 10"
        argument2 = path2 + " N 10"


        if not os.path.isfile(path2):
            print(f"Missing counterpart for {file} in {folder2}")
            continue

        with open(path1, 'r') as f1:
            lines1 = f1.readlines()

        with open(path2, 'r') as f2:
            lines2 = f2.readlines()

        if len(lines1) < 25 or len(lines2) < 25:
            print("File has less than 25 rows, wrong input file")
            continue


        print(f"Processing {file}...")


        res1 = run_program(program1, argument1)
        res2 = run_program(program2, argument2)

        stdout1 = str(res1.stdout)
        stdout2 = str(res2.stdout)

        stdout1_parsed = stdout1[stdout1.find('{'):stdout1.rfind('}')+1]
        stdout2_parsed = stdout2[stdout2.find('{'):stdout2.rfind('}')+1]

        res_variables1 = json.loads(stdout1_parsed)
        res_variables2 = json.loads(stdout2_parsed)

        '''
        print("Result1:")
        print(res_variables1['time'])
        print(res_variables1['iterations'])
        print(res_variables1['stripe_steps'])
        print(res_variables1['total_steps'])
        print("Result2:")
        print(res_variables2['time'])
        print(res_variables2['iterations'])
        print(res_variables2['stripe_steps'])
        print(res_variables2['total_steps'])
        '''

        writer.writerow([
            file,
            res_variables1['time'],
            res_variables1['iterations'],
            res_variables1['stripe_steps'],
            res_variables1['total_steps'],
            res_variables2['time'],
            res_variables2['iterations'],
            res_variables2['stripe_steps'],
            res_variables2['total_steps']
        ])

print("✅ Results written to", output_csv)
