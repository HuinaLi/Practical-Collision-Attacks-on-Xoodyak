from xooroundf import *
from sage.sat.converters.polybori import CNFEncoder 
from sage.sat.solvers.dimacs import DIMACS
from pysat.card import *
from pysat.formula import IDPool
import argparse
from read_dc_logfile import *

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

def generate_connector_anf(ROUNDS,state=384,rate=32):
    R = declare_ring( [Block( 'X', 4*ROUNDS*state),'u' ], globals() )
    a_vars = [[R(X(i + r*state)) for i in range(state) ] for r in range(1) ]
    b_vars = [[R(X(i + state + r*state)) for i in range(state) ] for r in range(1) ]                 
    ####### diff_pre ############  
    #3r: numvars A0--theta-->B0--pw-->C0--s-->D0--pe-->A1--theta-->B1--pw-->C1--s-->D1--pe-->A2--theta-->B2--pw-->C2(--s-->D2)
    ### Initialization ######
    Q = set()
    for i in range(128,state):
        if i == 128 or i == state - 8:
            a_vars[0][i] = R(1)
            # Q.add(a_vars[0][i] + 1)
        else:
            a_vars[0][i] = R(0)
            # Q.add(a_vars[0][i])
    
    ###########Adding the Constraints of Difference and Value ##################
    for r in range(1):
        # print(a_vars[0])
        a_vars[r] = theta(a_vars[r])
        # print(a_vars[0])
        a_vars[r] = rhowest(a_vars[r])
        a_vars[r] = addConst(a_vars[r],r)
        for i in range(state):
            print(a_vars[r][i])
        a_vars[r] = chi(a_vars[r])
        for i in range(state):
            print(a_vars[r][i] + b_vars[r][i])
        
    for r in range(1):
        # print(a_vars[0])
        b_vars[r] = rhoeast(b_vars[r])
        b_vars[r] = theta(b_vars[r])
        # print(a_vars[0])
        b_vars[r] = rhowest(b_vars[r])
        b_vars[r] = addConst(b_vars[r],r+1)
        for z in range(32):
            # print(f"{index_xyz(0,1,z)}: {a_vars[r][index_xyz(0,1,z)]} ")
            print(b_vars[r][index_xyz(0,1,z)])
        for z in range(32):
            # print(f"{index_xyz(0,2,z)}: {a_vars[r][index_xyz(0,2,z)] + 1} ")
            print(b_vars[r][index_xyz(0,2,z)] + 1)
        
        
        
if __name__ == '__main__':

    generate_connector_anf(2)
