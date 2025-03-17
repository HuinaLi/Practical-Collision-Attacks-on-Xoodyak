from read_dc_logfile import *
import argparse

"""read solution from solution file"""
def read_sol_ls(sol_path: str, solution_sign="s SATISFIABLE", line_split="v",  state=384) -> list:
    var_num = state 
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
    # get the solution 
    for line in lines:
        vars = line.split()
        for var in vars:
            v = 0 if int(var) < 0 else 1
            sol.append(v)
        if len(sol) >= var_num:
            break
    sol = sol[:var_num]
    # print(f"sol:\n{sol}")

    

    print("--------------------Print Solution Start-------------------------------")
    print(f"Value_in: ")
    print_Xstate(sol)
    print("-------------------------Print Done :)--------------------------------")
    return sol

def according_valid_dc_generate_message_pair(Value_in,ROUNDS,strat_rnd,diff_start,diff_end,state = 384,rate=32):
    R = declare_ring([Block( 'X', state ),'u' ], globals())
    Value_out = [R(0) for i in range(state)]
    
    for i in range(state):
        if Value_in[i] == 1:
            Value_in[i] = R(1)
        else:
            Value_in[i] = R(0)
    
    for i in range(state):
        Value_out[i] = Value_in[i] + diff_start[i]
    
    # print difference state and input Value_in, Value_out
    print("##############################################")
    print("A{}: ".format(strat_rnd))
    print_Xstate(diff_start)
    print("##############################################")
    print("input Value_in state at round {}: ".format(strat_rnd))
    print_Xstate(Value_in)
    print("##############################################")
    print("input Value_out  state at round {}: ".format(strat_rnd))
    print_Xstate(Value_out)
    # start round function
    print("start round function")
    for r in range(ROUNDS):
        # theta
        Value_in = theta(Value_in)
        Value_out = theta(Value_out)
        # rhowest
        Value_in = rhowest(Value_in)
        Value_out = rhowest(Value_out)
        # add const
        Value_in = addConst(Value_in,r+strat_rnd)
        Value_out = addConst(Value_out,r+strat_rnd)
        # non-linear layer
        Value_in = chi(Value_in)
        Value_out = chi(Value_out)
        # compute difference
        diff = [Value_in[i] + Value_out[i] for i in range(state)]
        # print difference state and input Value_in, Value_out
        print("##############################################")
        print("D{}: ".format(r+strat_rnd))
        print_Xstate(diff)
        print("##############################################")
        print("Value_in{}^S: ".format(r+strat_rnd))
        print_Xstate(Value_in)
        print("##############################################")
        print("Value_out{}^S: ".format(r+strat_rnd))
        print_Xstate(Value_out)
        # linear layer
        if r < ROUNDS-1:
            # rhoeast
            Value_in = rhoeast(Value_in)
            Value_out = rhoeast(Value_out)
            # compute difference
            diff = [Value_in[i] +Value_out[i] for i in range(state)]
            print("##############################################")
            print("A{}: ".format(r+strat_rnd+1))
            print_Xstate(diff)
            print("##############################################")
            print("Value_in{}: ".format(r+strat_rnd+1))
            print_Xstate(Value_in)
            print("##############################################")
            print("Value_out{}: ".format(r+strat_rnd+1))
            print_Xstate(Value_out)

    # check diff_end 
    for i in range(state):
        if Value_in[i] + Value_out[i] != diff_end[i]:
            print("False! Not satisfy")
            sys.exit(1)
            
    print("Find right pair!")  
    sys.exit(0)

if __name__ == '__main__':
    parse = argparse.ArgumentParser(description="Adding initialization+Obj")
    parse.add_argument("-r", "--rounds", type=int, help="number of rounds")
    parse.add_argument("-s", "--spath", type=str, help="solution file path")
    parse.add_argument("-m", "--stratrnd", type=int, help="start_rnd")
    
    args = parse.parse_args()

   ############# dc ############## 
    file_path = '/home/user/lhn/xoodoo_collision/trail_search/3rtrail/cons/R3_S64_M0_E64.log'
    diff_bit_lists = read_dcsol_ls(file_path,args.rounds)
    Value_in = read_sol_ls(args.spath)
    according_valid_dc_generate_message_pair(Value_in, args.rounds,args.stratrnd, diff_bit_lists[0],diff_bit_lists[4*args.stratrnd], diff_bit_lists[-1])
    