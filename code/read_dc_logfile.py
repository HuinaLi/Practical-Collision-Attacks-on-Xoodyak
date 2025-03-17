import math
from xooroundf import *
import argparse

"""read solution from solution file"""
def read_dcsol_ls(sol_path: str, Round: int, solution_sign="s SATISFIABLE", line_split="v", state_x=4, state_y=3, state_z=32, state=384) -> list:
    # var number of A,B,NK
    # var_num = 4*Round*state - state +  state_x*(Round-1)*state_z
    var_num = 4*Round*state - state +  state_x*(Round-1)*state_z
    # extract the solution from cnf solution file
    with open(sol_path, "r") as f:
        contents = f.read()
    # find solution_sign "s SATISFIABLE"
    i = contents.find(solution_sign)
    if i < 0:
        return None
    i += len(solution_sign) + 1
    # get the contents after "s SATISFIABLE"
    lines = contents[i:].split(line_split)
    sol = []
    # get the solution of A,B,D,M0,M1
    for line in lines:
        vars = line.split()
        for var in vars:
            v = 0 if int(var) < 0 else 1
            sol.append(v)
        if len(sol) >= var_num:
            break
    sol = sol[:var_num]
    A = []
    B = []
    C = []
    D = []
    Diff = []
    
    for r in range(Round):
        A.append(sol[r*state : (r+1)*state])
        Diff.append(A[r])
        B.append(sol[Round*state + r*state : Round*state + (r+1)*state])
        Diff.append(B[r])
        C.append(sol[2*Round*state + r*state : 2*Round*state + (r+1)*state])
        Diff.append(C[r])
        if r < Round - 1:
            D.append(sol[3*Round*state + r*state : 3*Round*state + (r+1)*state])
            Diff.append(D[r])
    tmp = C[Round-1][:128] + list([0 for _ in range(256)])
    Diff.append(tmp)
    return Diff



if __name__ == '__main__':
    parse = argparse.ArgumentParser(description="run solve")
    parse.add_argument("-r", "--rounds", type=int, help="number of rounds")
    args = parse.parse_args()
    # print(patterns)
    # 文件路径
    file_path = '/home/user/lhn/xoodoo_collision/trail_search/3rtrail/cons/R3_S10_M60_E54.log'
    
    diff_bit_lists = read_dcsol_ls(file_path, args.rounds)
    
    print(len(diff_bit_lists))

    


    