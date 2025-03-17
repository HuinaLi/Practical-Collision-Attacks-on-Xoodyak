from xooroundf import *
from sage.sat.converters.polybori import CNFEncoder 
from sage.sat.solvers.dimacs import DIMACS
from pysat.card import *
from pysat.formula import IDPool
import argparse

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
def generate_filename(Path, ROUNDS,Weight):
    # 初始化文件名的前缀部分
    filename = f"{Path}/{ROUNDS}round_w{Weight}"
    
    return filename

def check_dc_validity_newmodel(ROUNDS,Weight,start_rnd,Path,diff,state=384,rate=32):
    R = declare_ring( [Block( 'X', 4*ROUNDS*state),'u' ], globals() )
    a_vars = [[R(X(i + r*state)) for i in range(state) ] for r in range(ROUNDS) ]               
    b_vars = [[R(X(i + ROUNDS*state + r*state)) for i in range(state) ] for r in range(ROUNDS) ] 
    c_vars = [[R(X(i + 2*ROUNDS*state + r*state)) for i in range(state) ] for r in range(ROUNDS) ] 
    d_vars = [[R(X(i + 3*ROUNDS*state + r*state)) for i in range(state) ] for r in range(ROUNDS) ]  
    ####### diff_pre ############  
    #3r: numvars A0--theta-->B0--pw-->C0--s-->D0--pe-->A1--theta-->B1--pw-->C1--s-->D1--pe-->A2--theta-->B2--pw-->C2--s-->D2
    ### Initialization ###### 10000000
    Q = set()
    for i in range(128,state):
        if i in [128, 376]:
            Q.add(a_vars[0][i] +1)
        else:
            Q.add(a_vars[0][i])
    ###########Adding the Constraints of Difference and Value ##################
    for r in range(ROUNDS):
        a_vars[r] = theta(a_vars[r])
        for i in range(state):
            Q.add(b_vars[r][i] + a_vars[r][i])

        b_vars[r] = rhowest(b_vars[r])
        b_vars[r] = addConst(b_vars[r],start_rnd+r)
        for i in range(state):
            Q.add(c_vars[r][i] + b_vars[r][i])

        if r < ROUNDS-1:
            d_vars[r] = rhoeast(d_vars[r]) 
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
                    print ( diff[4*r+3][i], d )
                    print( "Impossible" )
                    exit(0)
                else:
                    Q.add(c_vars[r][i]/R(u) + 1) 
            else:
                d = c_vars[r][i] / R(u) 
                if d == 0:
                    pass
                elif d == 1:
                    print ( diff[4*r+3][i], d )
                    print( "Impossible" )
                    exit(0)
                else:
                    Q.add(c_vars[r][i]/R(u) ) 
        

    filename = generate_filename(Path, ROUNDS, Weight)
    filename += ".cnf"
    solver = DIMACS(filename = filename)
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
                row = [ 2*ROUNDS*state + r*state + index_xyz(x,0,z), \
                        2*ROUNDS*state + r*state + index_xyz(x,1,z), \
                        2*ROUNDS*state + r*state + index_xyz(x,2,z), \
                        3*ROUNDS*state + r*state + index_xyz(x,0,z), \
                        3*ROUNDS*state + r*state + index_xyz(x,1,z), \
                        3*ROUNDS*state + r*state + index_xyz(x,2,z)
                    ]
                for i in range(len(cnf_sbox)):
                    CNF_clause= ""
                    for j in range(len(cnf_sbox[i])):
                        temp = int(cnf_sbox[i][j])
                        if temp > 0 :
                            CNF_clause += str(row[ temp-1] + 1) + " "
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


if __name__ == '__main__':
    parse = argparse.ArgumentParser(description="Adding initialization+Obj")
    parse.add_argument("-r", "--rounds", type=int, help="number of rounds")
    parse.add_argument("-f", "--path", type=str, help="cnf file path")
    parse.add_argument("-w", "--weight", type=int, help="weight")
    parse.add_argument("-m", "--stratrnd", type=int, help="start_rnd")
    args = parse.parse_args()

    check_dc_validity_newmodel(args.rounds, args.weight,args.stratrnd, args.path)
