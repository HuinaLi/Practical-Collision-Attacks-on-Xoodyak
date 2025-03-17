from read_dc_logfile import *
from verifydc_model import *
import subprocess
import argparse
import timeit
import logging
import re


######### path information ##############
keypath = [
    "/home/user/lhn/xoodoo_collision/rightpair_search/code/print_right_pair.py",
    "/home/user/lhn/xoodoo_collision/rightpair_search/result",
    "/home/user/lhn/xoodoo_collision/rightpair_search/code/ban_solution.py"
    ]


def run_satsolver(solver, nrThread, filename1, filename2,timeout_seconds = 1000000):
    """Run solver and log output to filename2."""
    try:
        with open(filename2, "w") as f:
            result = subprocess.run([solver, "-t", str(nrThread),  filename1], stdout=f, stderr=subprocess.STDOUT, check=True, timeout=timeout_seconds)
            # result = subprocess.run([solver,   filename1], stdout=f, stderr=subprocess.STDOUT, check=True, timeout=timeout_seconds)
    
    except subprocess.TimeoutExpired:
        print(f"The solver was terminated after {timeout_seconds} seconds due to timeout.")
        return False
    except subprocess.CalledProcessError as e:
        ## 20: UNSAT; 10: s SATISFIABLE
        if e.returncode == 20 or e.returncode == 10:
            # print("SAT solver finished successfully with exit code 20 (Satisfiable).")
            return True
        else:
            print(f"SAT solver failed with exit code {e.returncode}.")
            return False
    # else:
    #     print("SAT solver finished successfully.")
    return True 

def check_satisfiability(filename2):
    """Check if the log file contains 's SATISFIABLE'."""
    try:
        with open(filename2, "r") as f:
            content = f.read()
        return "s SATISFIABLE" in content
    except FileNotFoundError:
        print(f"Log file {filename2} does not exist or cannot be read.")
        return False

def delete_file(filename):
    """Delete the specified file."""
    try:
        subprocess.run(["rm", "-f", filename], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error while trying to delete file {filename}: {e}")

def save_output(command, print_file):
    """Run the command and save the output to print_file."""
    res = subprocess.run(command, capture_output=True, text=True)
    if res.returncode != 0:
        print("F")
        # return False
    if res.returncode == 0:
        with open(print_file, "w") as f:
            f.write(res.stdout)
        print(f"Output has been saved to {print_file}")
    return True

def solve(ROUNDS, Weight, Path, solver, nrThread, sr, Diff_bitlist):
    
    print(f"#Round: {ROUNDS}, #as =: {Weight}, START:")

    # Generate CNF files
    check_dc_validity_newmodel(ROUNDS, Weight, sr, Path, Diff_bitlist)

    # Generate filenames
    filename = generate_filename(Path, ROUNDS,Weight)
    filename1 = filename + ".cnf"
    
    count = 1
    while True:
        print(f"Solve START: no.{count}")
        filename2 = filename + f"no{count}" + ".log"
        start1 = timeit.default_timer()
        # Run solver and check satisfiability
        if run_satsolver(solver, nrThread, filename1, filename2):
            if not check_satisfiability(filename2):
                print(f"UNSAT")
                delete_file(filename1)
                end1 = timeit.default_timer()
                logging.info("cost: %f s" % (end1 - start1))
                print("cost: %f s" % (end1 - start1))
                break  # continue the loop if UNSAT
        else:
            print(f"SAT solver command failed for {filename1}")
            break

        end1 = timeit.default_timer()
        logging.info("solve cost: %f s" % (end1 - start1))
        print("solve cost: %f s" % (end1 - start1))
        ## store this colliding trail to True_sol_index list
        print("Find!")

        # Run the solution script and save output
        print(f"Check: ")
        start = timeit.default_timer()
        command3 = [
            "python",
            f"{keypath[0]}",
            "-r",
            str(ROUNDS),
            "-m",
            str(sr),
            "-s",
            filename2
        ]
        print_file = f"{keypath[1]}/{ROUNDS}round_w{Weight}_rightpair_no{count}.log"
        if not save_output(command3, print_file):
            break
        end = timeit.default_timer()
        logging.info("check cost: %f s" % (end - start))
        print("check cost: %f s" % (end - start))
       

        command4 = [
                "python",
                f"{keypath[2]}",
                "-c",
                filename1,
                "-s",
                filename2,
                "-r",
                str(ROUNDS)
            ]
        result = subprocess.run(command4, capture_output=True)
        # print(result.stdout)
        # delete_file(filename2)
        count -= 1
        if count <= 0:
            break
    print("__________End____________")

if __name__ == "__main__":
    parse = argparse.ArgumentParser(description="run solve")
    parse.add_argument("-r", "--rounds", type=int, help="number of rounds")
    parse.add_argument("-s", "--spath", type=str, help="solution file path")
    parse.add_argument("-f", "--path", type=str, help="cnf file path")
    parse.add_argument("-w", "--weight", type=int, help="weight")
    parse.add_argument("-sat", "--solver", type=str, help="solver path")
    parse.add_argument("-satTrd", "--thread", type=int, help="specify the number of thread of the parallel sat solver")
    parse.add_argument("-m", "--stratrnd", type=int, help="start_rnd")
    args = parse.parse_args()
    Diff = [0 for r in range(4*args.rounds)]
   ############# SFS ############## 
    print("we have arrived here")
    file_path = '/home/user/lhn/xoodoo_collision/trail_search/3rtrail/cons/R3_S64_M0_E64.log'
    
    diff_bit_lists = read_dcsol_ls(file_path,args.rounds)
    Diff_list = diff_bit_lists[4*args.stratrnd:]
    print(len(Diff_list))
    solve(args.rounds, 
          args.weight, 
          args.path, 
          args.solver, 
          args.thread, 
          args.stratrnd,
          Diff_list
        )
    