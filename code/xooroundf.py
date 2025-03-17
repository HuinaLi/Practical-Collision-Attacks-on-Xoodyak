from sage.all import *
from sage.rings.polynomial.pbori import *
import logging
from sage.sat.converters.polybori import CNFEncoder 
from sage.sat.solvers.dimacs import DIMACS
# create logger
logger = logging.getLogger('XooodooRoundF_in_ANF_form')
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('c:%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

"""Xoodoo: a 384-bit permutation
    lane: 32 bits
    little endian: for example - 0x00000004 = [0, 0, 0, 0, 0, 1, 0, 0, ..., 0] i.e. 04000000
                                                          ^
                                                          |
                                            lowest byte at lowest significant
    But hex2vector() function does not convert to little endian, and function's output is [0, 0, 1, 0, 0, 0, 0, 0, ..., 0]
    state: 384 bits = 3 * 4 words
    We use a list to denote a state/word and the element of the list is a bit
    xoodoo uses sx,y,z to denote each word, 0 <= x <= 3, 0 <= y <= 2, 0 <= z <= 31
    index of sx,y,z: 32 * (x + 4 * y) + z
"""
def index_xyz(x: int, y: int, z:int) -> int:
    """return the index of coordinates x, y, z

    Args:
        x (int): x coordinate
        y (int): y coordinate
        z (int): z coordinate

    Returns:
        int: index of x, y ,z
    """
    x, y, z= x%4, y%3, z%32
    return 32 * (x + 4 * y) + z

def index_xy(x: int, y: int) -> int:
    """return the index of coordinates x, y

    Args:
        x (int): x coordinate
        y (int): y coordinate

    Returns:
        int: index of x, y
    """
    x, y = x%4, y%3
    return x + 4 * y

def index_xz(x: int, z: int) -> int:
    """return the index of coordinates x, z

    Args:
        x (int): x coordinate
        z (int): z coordinate

    Returns:
        int: index of x, z
    """
    x, z = x%4, z%32
    return z + 32 * x

def hex2bin(Hex_in, Bin_len=64):
    Bin_out = []
    for j in range(Bin_len):
        Bin_out.append(Hex_in >> ( Bin_len -1 - j ) & 0x1)
    return Bin_out

def index_z(z: int)-> int:
    """return the index of coordinates z

    Args:
        z (int): z coordinate

    Returns:
        int: index of z
    """
    z = (z + 32)%32
    return z

def bin2int(a:list) -> int:
    """把[1,0,1,0..,0]这类二进制list转成int
    """
    b = ""
    for i in a:
        b += str(i)
    return int(b, 2)

def SingleMatrix(X, r0, r1):
  Y = []
  for i in range(4):
      for j in range(32):
          Y.append(X[32 * ((i - r0 + 4) % 4) + (j - r1 + 32) % 32])
  return Y

def theta(X):
    E1 = [R(0) for i in range(128)]
    E2 = [R(0) for i in range(128)]
    P = []
    Y = []
    for i in range(128):
        P.append(X[i] + X[i + 128] + X[i + 256])
    E1[0:128] = SingleMatrix(P, 1, 5)
    E2[0:128] = SingleMatrix(P, 1, 14)

    for j in range(128):
        Y.append(X[j] + E1[j] + E2[j])
        
    for j in range(128):
        Y.append(X[j + 128] + E1[j] + E2[j])

    for j in range(128):
        Y.append(X[j + 256] + E1[j] + E2[j])
    return Y

def rhowest(X):
    X[0:128] = SingleMatrix(X[0: 128], 0, 0)
    X[128:256] = SingleMatrix(X[128:256], 1, 0)
    X[256:384] = SingleMatrix(X[256:384], 0, 11)

    return (X)

def addConst ( X, r ):
    constant = [ 0x0058, 0x0038, 0x03c0, 0x00d0, 0x0120, 0x0014, 0x0060, 0x002c, 0x0380, 0x00f0,
            0x01a0, 0x0012 ]
    for i in range(16):
        if constant[r] >> i  & 0x1:
            X[i] += 1
    return X

def SingleSbox(x0, x1, x2):
    y0 = x0 + (1 + x1) * x2
    y1 = x1 + (1 + x2) * x0
    y2 = x2 + (1 + x0) * x1
    return y0, y1, y2

def chi(A):
    B = [R(0) for i in range(384)]
    for j in range(128):
        B[0 + j], B[128 + j], B[256 + j] = SingleSbox(A[0 + j], A[128 + j], A[256 + j])
    return B

def rhoeast(X):
    X[0:128] = SingleMatrix(X[0: 128], 0, 0)
    X[128:256] = SingleMatrix(X[128:256], 0, 1)
    X[256:384] = SingleMatrix(X[256:384], 2, 8)
    return (X)

def round(X):
    for i in range(2):
       X = theta(X)
       X = rhowest(X)
       X = addConst(X, i)
       X = chi(X)
       X = rhoeast(X)
    return X

def print_Xstate(X):
    for i in range(12):
        # print a row at a time
        row_print = ""
        # now start convert binary state to hex form
        # get the binary state
        state_binary = X[32 * i : 32 * i + 32]
        
        # Check if binary state length is valid
        if len(state_binary) % 8 != 0:
            logger.error("The length of a word should be a multiple of 8")
            exit(1)
        
        # Compute hex every 8 bits
        state_hex = ""
        for k in range(len(state_binary) // 8):
            # Compute 8 bits int value
            tmp = 0
            for bit in range(8):
                # Correct bit shifting: process from MSB to LSB
                tmp += (int(state_binary[k * 8 + bit]) << (bit))
            # Convert int value to hex, ensure 2-digit format, then add to the state
            state_hex += hex(tmp)[2:].zfill(2)
        
        # Format hex string with "0x" prefix
        state_hex = "0x" + state_hex
        # Add to the row, delimiter is " "(space)
        row_print += state_hex + " "
        print(row_print)
    print("------")

def generate_singlesbox_ValueandDiff_relation():
    R = declare_ring([Block('x', 3),'u'], globals() )
    Diff_in = [[1,0,0],[0,1,1],[1,0,1],[1,1,1]]
    Y = [R(0) for _ in range(3)]
    for diff in Diff_in:
        X = [R(x(i)) for i in range(3)]
        for i in range(3):
            X[i] += diff[i]*R(u)
        Y = SingleSbox(X[0],X[1],X[2])
        
        for i in range(3):
            if i == 0 :
                print(Y[i]/R(u) + 1)
            else:
                print(Y[i]/R(u))


if __name__ == '__main__':
    R = declare_ring([Block('x', 6),'u'], globals() )
    # X = [R(x(i)) for i in range(3)]
    # Y = [R(x(i + 3)) for i in range(3)]
    # Q = set()
    # X = SingleSbox(X[0],X[1],X[2])
    # for i in range(3):
    #     Q.add(Y[i] + X[i])
    # filename = "/home/user/lhn/xoodoo_collision/rightpair_search/code/test.cnf"
    # solver = DIMACS(filename = filename)
    # e = CNFEncoder(solver, R)
    # e(list(Q))
    # solver.write()
    generate_singlesbox_ValueandDiff_relation()