from pathlib import Path
import argparse
import logging
import os
import shlex
import shutil
import subprocess
import sys
import timeit

from verifydc_model import (
    VALID_COLLISION_INIT_MODES,
    build_default_diff,
    check_dc_validity_newmodel,
    generate_run_id,
    normalize_attack_type,
    normalize_collision_init_mode,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = Path(__file__).resolve().parent
DEFAULT_CNF_DIR = PROJECT_ROOT / "cons"
DEFAULT_RESULT_DIR = PROJECT_ROOT / "result"
DEFAULT_TREENGELING = Path("/home/hnli/sat-solvers/lingeling/treengeling")
PARALLEL_SOLVERS = {"treengeling", "plingeling"}
SEQUENTIAL_SOLVERS = {"cadical", "kissat"}
VALID_SOLVER_TYPES = ("auto", "parallel", "sequential")


def infer_solver_type(solver):
    solver_name = Path(solver).name.lower()
    if solver_name in PARALLEL_SOLVERS:
        return "parallel"
    if solver_name in SEQUENTIAL_SOLVERS:
        return "sequential"
    return "sequential"


def resolve_solver_type(solver_type, solver):
    if solver_type not in VALID_SOLVER_TYPES:
        raise ValueError(f"Unsupported solver type {solver_type!r}; expected one of {VALID_SOLVER_TYPES}.")
    if solver_type == "auto":
        return infer_solver_type(solver)
    return solver_type


def build_solver_command(solver, nrThread, filename1, solver_type="auto"):
    effective_solver_type = resolve_solver_type(solver_type, solver)
    if effective_solver_type == "parallel":
        return [solver, "-t", str(nrThread), filename1], effective_solver_type, None

    warning = None
    if nrThread and int(nrThread) > 1:
        warning = f"Thread option -satTrd {nrThread} ignored for sequential solver {Path(solver).name}."
    return [solver, filename1], effective_solver_type, warning


def run_satsolver(solver, nrThread, filename1, filename2, timeout_seconds=1000000, solver_type="auto"):
    """Run solver and log output to filename2."""
    solver_cmd, effective_solver_type, warning = build_solver_command(solver, nrThread, filename1, solver_type)
    print(f"SAT solver type: {effective_solver_type}", flush=True)
    if warning:
        print(warning, flush=True)
    print(f"SAT solver command: {shlex.join(solver_cmd)}", flush=True)
    try:
        Path(filename2).parent.mkdir(parents=True, exist_ok=True)
        with open(filename2, "w") as f:
            subprocess.run(solver_cmd, stdout=f, stderr=subprocess.STDOUT, check=True, timeout=timeout_seconds)

    except subprocess.TimeoutExpired:
        print(f"The solver was terminated after {timeout_seconds} seconds due to timeout.")
        return False
    except subprocess.CalledProcessError as e:
        ## 20: UNSAT; 10: s SATISFIABLE
        if e.returncode == 20 or e.returncode == 10:
            return True
        print(f"SAT solver failed with exit code {e.returncode}.")
        return False
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
        Path(filename).unlink(missing_ok=True)
    except OSError as e:
        print(f"Error while trying to delete file {filename}: {e}")


def save_output(command, print_file):
    """Run the command and save the output to print_file."""
    res = subprocess.run(command, capture_output=True, text=True)
    if res.returncode != 0:
        print("F")
        if res.stderr:
            print(res.stderr.strip())
        return False

    print_file = Path(print_file)
    print_file.parent.mkdir(parents=True, exist_ok=True)
    with print_file.open("w") as f:
        f.write(res.stdout)
    print(f"Output has been saved to {print_file}")
    return True


def solve(ROUNDS, Weight, cnf_path, solver, nrThread, sr, Diff_bitlist, attack_type="sfscollision", run_id=None, solver_type="auto", collision_init_mode="constraints"):
    attack_type = normalize_attack_type(attack_type)
    collision_init_mode = normalize_collision_init_mode(collision_init_mode)
    run_id = run_id or generate_run_id()

    print(f"#Round: {ROUNDS}, #as =: {Weight}, START:")
    print(f"Attack type: {attack_type}")
    if attack_type == "collision":
        print(f"Collision init mode: {collision_init_mode}")
    print(f"Run ID: {run_id}")

    # Generate CNF files
    filename1 = check_dc_validity_newmodel(
        ROUNDS,
        Weight,
        sr,
        cnf_path,
        Diff_bitlist,
        run_id=run_id,
        attack_type=attack_type,
        collision_init_mode=collision_init_mode,
    )

    filename = str(Path(filename1).with_suffix(""))
    result_dir = DEFAULT_RESULT_DIR
    result_dir.mkdir(parents=True, exist_ok=True)

    count = 1
    while True:
        print(f"Solve START: no.{count}")
        filename2 = f"{filename}_no{count}.log"
        start1 = timeit.default_timer()
        # Run solver and check satisfiability
        if run_satsolver(solver, nrThread, filename1, filename2, solver_type=solver_type):
            if not check_satisfiability(filename2):
                print("UNSAT")
                delete_file(filename1)
                end1 = timeit.default_timer()
                logging.info("cost: %f s" % (end1 - start1))
                print("cost: %f s" % (end1 - start1))
                break
        else:
            print(f"SAT solver command failed for {filename1}")
            break

        end1 = timeit.default_timer()
        logging.info("solve cost: %f s" % (end1 - start1))
        print("solve cost: %f s" % (end1 - start1))
        ## store this colliding trail to True_sol_index list
        print("Find!")

        # Run the solution script and save output
        print("Check: ")
        start = timeit.default_timer()
        command3 = [
            sys.executable,
            str(CODE_DIR / "print_right_pair.py"),
            "-r",
            str(ROUNDS),
            "-m",
            str(sr),
            "-s",
            filename2,
        ]
        print_file = result_dir / f"{attack_type}_{ROUNDS}round_w{Weight}_{run_id}_rightpair_no{count}.log"
        if not save_output(command3, print_file):
            break
        end = timeit.default_timer()
        logging.info("check cost: %f s" % (end - start))
        print("check cost: %f s" % (end - start))

        command4 = [
            sys.executable,
            str(CODE_DIR / "ban_solution.py"),
            "-c",
            filename1,
            "-s",
            filename2,
            "-r",
            str(ROUNDS),
        ]
        subprocess.run(command4, capture_output=True)
        # delete_file(filename2)
        count -= 1
        if count <= 0:
            break
    print("__________End____________")


def resolve_solver(cli_solver):
    if cli_solver:
        return cli_solver
    env_solver = os.environ.get("SAT_SOLVER")
    if env_solver:
        return env_solver
    if DEFAULT_TREENGELING.exists():
        return str(DEFAULT_TREENGELING)
    treengeling = shutil.which("treengeling")
    if treengeling:
        return treengeling
    raise ValueError("SAT solver not specified. Pass -sat/--solver, set SAT_SOLVER, or install treengeling on PATH.")


if __name__ == "__main__":
    parse = argparse.ArgumentParser(description="run solve")
    parse.add_argument("-r", "--rounds", type=int, required=True, help="number of rounds")
    parse.add_argument("-s", "--spath", type=str, help="solution file path")
    parse.add_argument("-f", "--path", type=str, default=str(DEFAULT_CNF_DIR), help="cnf output directory or .cnf file path")
    parse.add_argument("-w", "--weight", type=int, required=True, help="weight")
    parse.add_argument("-sat", "--solver", type=str, help="solver path; defaults to SAT_SOLVER, bundled treengeling, or treengeling on PATH")
    parse.add_argument("--solver-type", choices=VALID_SOLVER_TYPES, default="auto", help="solver family: auto detects treengeling/plingeling as parallel and cadical/kissat as sequential")
    parse.add_argument("-satTrd", "--thread", type=int, default=1, help="thread count for parallel solvers; ignored for sequential solvers")
    parse.add_argument("-m", "--stratrnd", type=int, required=True, help="start_rnd")
    parse.add_argument("--run-id", type=str, default=None, help="timestamp/run id used in output filenames")
    parse.add_argument("--collision-init-mode", choices=VALID_COLLISION_INIT_MODES, default="constraints", help="collision initialization mode: add constraints or substitute constants")
    attack_group = parse.add_mutually_exclusive_group()
    attack_group.add_argument("--collision", action="store_true", help="enable collision initialization constraints")
    attack_group.add_argument("--sfscollision", action="store_true", help="use SFS collision constraints (default)")
    args = parse.parse_args()

    attack_type = "collision" if args.collision else "sfscollision"
    solver = resolve_solver(args.solver)

    print("we have arrived here")
    Diff_list = build_default_diff(args.rounds)
    print(len(Diff_list))

    solve(
        args.rounds,
        args.weight,
        args.path,
        solver,
        args.thread,
        args.stratrnd,
        Diff_list,
        attack_type=attack_type,
        run_id=args.run_id,
        solver_type=args.solver_type,
        collision_init_mode=args.collision_init_mode,
    )
