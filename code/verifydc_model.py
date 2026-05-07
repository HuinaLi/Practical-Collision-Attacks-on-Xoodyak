from pathlib import Path
from datetime import datetime
import argparse

from xooroundf import *
from sage.sat.converters.polybori import CNFEncoder
from sage.sat.solvers.dimacs import DIMACS
from pysat.card import *
from pysat.formula import IDPool


#cnf_sbox =  13
cnf_sbox =  [
    [1, 6, -4],
    [2, 3, -6],
    [2, 4, -5],
    [4, 5, -2],
    [1, -2, -4],
    [2, -3, -5],
    [3, -1, -6],
    [6, -1, -3],
    [1, 2, 4, -3],
    [2, 5, 6, -1],
    [3, 6, -2, -5],
    [4, -3, -5, -6],
    [5, -1, -4, -6]
]

VALID_ATTACK_TYPES = ("collision", "sfscollision")
VALID_COLLISION_INIT_MODES = ("constraints", "substitution")


def generate_run_id():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def normalize_attack_type(attack_type):
    if attack_type not in VALID_ATTACK_TYPES:
        raise ValueError(
            f"Unsupported attack type {attack_type!r}; expected one of {VALID_ATTACK_TYPES}."
        )
    return attack_type


def normalize_collision_init_mode(collision_init_mode):
    if collision_init_mode not in VALID_COLLISION_INIT_MODES:
        raise ValueError(
            f"Unsupported collision initialization mode {collision_init_mode!r}; "
            f"expected one of {VALID_COLLISION_INIT_MODES}."
        )
    return collision_init_mode


def generate_filename(Path, ROUNDS, Weight, run_id=None, attack_type="sfscollision"):
    """Return the output filename prefix without the .cnf suffix."""
    attack_type = normalize_attack_type(attack_type)
    run_id = run_id or generate_run_id()
    path = PathLib(Path)

    # Support both directory path and explicit .cnf file path.
    if path.suffix == ".cnf":
        return str(path.with_name(f"{path.stem}_{attack_type}_{run_id}"))
    return str(path / f"{attack_type}_{ROUNDS}round_w{Weight}_{run_id}")


# Avoid shadowing pathlib.Path while preserving the historical Path argument name.
PathLib = Path


def add_collision_initialization(Q, a_vars, state, ring, collision_init_mode="constraints"):
    """Add the extra initialization constraints used only by collision mode."""
    collision_init_mode = normalize_collision_init_mode(collision_init_mode)
    for i in range(128, state):
        if collision_init_mode == "constraints":
            if i in [128, 376]:
                Q.add(a_vars[0][i] + 1)
            else:
                Q.add(a_vars[0][i])
        else:
            if i in [128, 376]:
                Q.add(a_vars[0][i] + 1)
                a_vars[0][i] = ring(1)
            else:
                Q.add(a_vars[0][i])
                a_vars[0][i] = ring(0)


def check_dc_validity_newmodel(
    ROUNDS,
    Weight,
    start_rnd,
    Path,
    diff,
    state=384,
    rate=32,
    run_id=None,
    attack_type="sfscollision",
    collision_init_mode="constraints",
):
    attack_type = normalize_attack_type(attack_type)
    collision_init_mode = normalize_collision_init_mode(collision_init_mode)
    R = declare_ring([Block('X', 4*ROUNDS*state), 'u'], globals())
    a_vars = [[R(X(i + r*state)) for i in range(state)] for r in range(ROUNDS)]
    b_vars = [[R(X(i + ROUNDS*state + r*state)) for i in range(state)] for r in range(ROUNDS)]
    c_vars = [[R(X(i + 2*ROUNDS*state + r*state)) for i in range(state)] for r in range(ROUNDS)]
    d_vars = [[R(X(i + 3*ROUNDS*state + r*state)) for i in range(state)] for r in range(ROUNDS)]
    ####### diff_pre ############
    #3r: numvars A0--theta-->B0--pw-->C0--s-->D0--pe-->A1--theta-->B1--pw-->C1--s-->D1--pe-->A2--theta-->B2--pw-->C2--s-->D2
    ### Initialization ###### 10000000
    Q = set()
    if attack_type == "collision":
        add_collision_initialization(Q, a_vars, state, R, collision_init_mode)
    ###########Adding the Constraints of Difference and Value ##################
    for r in range(ROUNDS):
        a_vars[r] = theta(a_vars[r])
        for i in range(state):
            Q.add(b_vars[r][i] + a_vars[r][i])

        b_vars[r] = rho_west(b_vars[r])
        b_vars[r] = add_const(b_vars[r], start_rnd+r)
        for i in range(state):
            Q.add(c_vars[r][i] + b_vars[r][i])

        if r < ROUNDS-1:
            d_vars[r] = rho_east(d_vars[r])
            for i in range(state):
                Q.add(a_vars[r+1][i] + d_vars[r][i])

    for r in range(ROUNDS):
        for i in range(state):
            c_vars[r][i] += diff[4*r+2][i] * R(u)

        c_vars[r] = chi(c_vars[r])

        for i in range(state):
            if diff[4*r+3][i] == 1:
                d = c_vars[r][i] / R(u)
                if d == 1:
                    pass
                elif d == 0:
                    print(diff[4*r+3][i], d)
                    print("Impossible")
                    exit(0)
                else:
                    Q.add(c_vars[r][i]/R(u) + 1)
            else:
                d = c_vars[r][i] / R(u)
                if d == 0:
                    pass
                elif d == 1:
                    print(diff[4*r+3][i], d)
                    print("Impossible")
                    exit(0)
                else:
                    Q.add(c_vars[r][i]/R(u))

    filename = generate_filename(Path, ROUNDS, Weight, run_id=run_id, attack_type=attack_type)
    filename += ".cnf"
    PathLib(filename).parent.mkdir(parents=True, exist_ok=True)
    solver = DIMACS(filename=filename)
    e = CNFEncoder(solver, R)
    e(list(Q))
    solver.write()

    with open(filename, "r") as f:
        cnf_info = f.readline().split(" ")
        var_num, clause_num = int(cnf_info[2]), int(cnf_info[3])
        ls_cnf = f.read()
    # print(var_num,clause_num)

    constraint_cnf = " "
    ## cnf_sbox
    row = [0]*6
    for r in range(ROUNDS):
        for x in range(4):
            for z in range(rate):
                # [c0 c1 c2 d0 d1 d2]
                row = [
                    2*ROUNDS*state + r*state + index_xyz(x, 0, z),
                    2*ROUNDS*state + r*state + index_xyz(x, 1, z),
                    2*ROUNDS*state + r*state + index_xyz(x, 2, z),
                    3*ROUNDS*state + r*state + index_xyz(x, 0, z),
                    3*ROUNDS*state + r*state + index_xyz(x, 1, z),
                    3*ROUNDS*state + r*state + index_xyz(x, 2, z),
                ]
                for i in range(len(cnf_sbox)):
                    CNF_clause = ""
                    for j in range(len(cnf_sbox[i])):
                        temp = int(cnf_sbox[i][j])
                        if temp > 0:
                            CNF_clause += str(row[temp-1] + 1) + " "
                        else:
                            CNF_clause += str(-1 * row[abs(temp+1)]-1) + " "
                    CNF_clause += '0'
                    constraint_cnf += CNF_clause + "\n"
                    clause_num += 1

    with open(filename, "w") as f:
        f.write(f"p cnf {var_num} {clause_num}\n")
        f.write(ls_cnf)
        f.write(constraint_cnf)

    print(f"New DC Verify Model Constructed:) var_num:{var_num}, clause_num:{clause_num}")
    print(f"CNF has been saved to {filename}")
    return filename


def build_default_diff(rounds, state=384):
    diff_list = [0 for _ in range(state)]
    for i in range(32):
        diff_list[i] = 1
    return [diff_list for _ in range(4*rounds)]


if __name__ == '__main__':
    parse = argparse.ArgumentParser(description="Build the DC verification CNF model.")
    parse.add_argument("-r", "--rounds", type=int, required=True, help="number of rounds")
    parse.add_argument("-f", "--path", type=str, required=True, help="cnf output directory or .cnf file path")
    parse.add_argument("-w", "--weight", type=int, required=True, help="weight")
    parse.add_argument("-m", "--stratrnd", type=int, required=True, help="start_rnd")
    parse.add_argument("--run-id", type=str, default=None, help="timestamp/run id used in output filenames")
    parse.add_argument("--collision-init-mode", choices=VALID_COLLISION_INIT_MODES, default="constraints", help="collision initialization mode: add constraints or substitute constants")
    attack_group = parse.add_mutually_exclusive_group()
    attack_group.add_argument("--collision", action="store_true", help="enable collision initialization constraints")
    attack_group.add_argument("--sfscollision", action="store_true", help="use SFS collision constraints (default)")
    args = parse.parse_args()

    attack_type = "collision" if args.collision else "sfscollision"
    Diff_list = build_default_diff(args.rounds)
    print("we have arrived here")
    print(len(Diff_list))
    print(f"#Round: {args.rounds}, #as =: {args.weight}, START:")

    check_dc_validity_newmodel(
        args.rounds,
        args.weight,
        args.stratrnd,
        args.path,
        Diff_list,
        run_id=args.run_id,
        attack_type=attack_type,
        collision_init_mode=args.collision_init_mode,
    )
