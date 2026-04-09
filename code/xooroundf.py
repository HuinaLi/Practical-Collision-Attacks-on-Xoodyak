"""
Xoodoo: a 384-bit permutation Implementation in ANF (Algebraic Normal Form)

This module implements the Xoodoo permutation function used in Xoodyak.
The implementation focuses on algebraic normal form representation for cryptanalysis.

The state is represented as a 384-bit array organized as 3x4x32 bits.
Coordinates (x, y, z) where 0 <= x <= 3, 0 <= y <= 2, 0 <= z <= 31.
Index calculation: 32 * (x + 4 * y) + z

The state vector is a list where each element is a Boolean Polynomial in the ANF ring.

Author: Huina
Date: Sep 28, 2025
"""

import logging
import os
from typing import List, Tuple, Union, Optional

from sage.all import *
from sage.rings.polynomial.pbori import *
from sage.sat.converters.polybori import CNFEncoder 
from sage.sat.solvers.dimacs import DIMACS

# Constants
STATE_SIZE = 384 # State size in bits for this implementation (3 * 4 * 32)
LANE_SIZE = 32 # Lane size in bits
Y_SIZE = 3 # Number of rows (y-dimension) in Xoodoo state
X_SIZE = 4 # Number of columns (x-dimension) in Xoodoo state
XOODOO_ROUNDS = 12 # Number of rounds in Xoodoo
# Assuming the file path is correct in the execution environment
THETA_REVERSE_FILE = "/home/huina/Xoodyak-cryptanalysis/collision_search/code/thetaReverse.txt" 
THETA_INV_ROW_WEIGHT = 133 # Weight of each row in the pre-computed Inverse Theta matrix

# Round constants for addConst step
ROUND_CONSTANTS = [
  0x0058, 0x0038, 0x03c0, 0x00d0, 0x0120, 0x0014, 0x0060, 0x002c, 0x0380, 0x00f0,
  0x01a0, 0x0012
]


# Setup logging (unchanged)
logger = logging.getLogger('XoodooRoundF_in_ANF_form')
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

ch.setFormatter(formatter)
logger.addHandler(ch)

# -----------------------------------------------------------
# Core Helper Functions
# -----------------------------------------------------------

def index_xyz(x: int, y: int, z: int) -> int:
  """
  Calculate the index of coordinates (x, y, z) in the state array.
  """
  x, y, z = x % X_SIZE, y % Y_SIZE, z % LANE_SIZE
  return LANE_SIZE * (x + X_SIZE * y) + z

def index_xy(x: int, y: int) -> int:
    """
     Calculate the index of coordinates (x, y) in a 2D plane.
     Args:
          x: X coordinate (0-3)

          y: Y coordinate (0-2)
     Returns:
          Index in the 2D plane
    """

    x, y = x % X_SIZE, y % Y_SIZE
    return x + X_SIZE * y

def index_xz(x: int, z: int) -> int:

    """
    Calculate the index of coordinates (x, z) in a lane.
    Args:
        x: X coordinate (0-3)
        z: Z coordinate (0-31)

    Returns:
        Index in the lane
    """

    x, z = x % X_SIZE, z % LANE_SIZE

    return z + LANE_SIZE * x

def single_matrix(X: List, r0: int, r1: int) -> List:
    """
    Apply matrix transformation with given rotation offsets (for Rho and Theta).

    Args:
    X: Input plane vector (size X_SIZE * LANE_SIZE)
    r0: X-direction rotation offset (Lane rotation)
    r1: Z-direction rotation offset (Bit rotation)

    Returns:
    Transformed plane vector
    """
    if not X:
        return []

    plane_size = X_SIZE * LANE_SIZE
    Y = [R(0) for _ in range(plane_size)] 
    
    for i in range(X_SIZE): # x_out
        for j in range(LANE_SIZE): # z_out
                
            idx_out = index_xz(i,j)
            idx_in = index_xz(i-r0, j-r1)
                
            Y[idx_out] = X[idx_in]
    return Y


# -----------------------------------------------------------
# Forward Round Functions
# -----------------------------------------------------------

def theta(X: List) -> List:
    """
    Theta step: X[y] = X[y] + P(x-1, z-5) + P(x-1, z-14).
    """
    plane_size = X_SIZE * LANE_SIZE
    E1 = [R(0) for _ in range(plane_size)]
    E2 = [R(0) for _ in range(plane_size)]
    P = []
    Y = [R(0) for _ in range(STATE_SIZE)]
    
    # 1. Calculate column parities P[i]
    for i in range(plane_size):
        parity = (X[i] + X[i + plane_size] + X[i + 2 * plane_size])
        P.append(parity)
    
    # 2. Calculate E1 and E2
    E1[:plane_size] = single_matrix(P, 1, 5) 
    E2[:plane_size] = single_matrix(P, 1, 14)

    # 3. Apply theta transformation
    for plane in range(Y_SIZE):
        for j in range(plane_size):
            Y[j + plane * plane_size] = X[j + plane * plane_size] + E1[j] + E2[j]
    
    return Y

def rho_west(X: List) -> List:
    """
    Rho west step: Apply lane rotations to planes y=1 and y=2.
    """
    plane_size = X_SIZE * LANE_SIZE
    X_out = X[:] # Create copy for output
    
    # y=1: (1, 0) - Shift 1 lane West
    X_out[plane_size:2*plane_size] = single_matrix(X[plane_size:2*plane_size], 1, 0)
        
    # y=2: (0, 11) - Rotate 11 bits
    X_out[2*plane_size:3*plane_size] = single_matrix(X[2*plane_size:3*plane_size], 0, 11)

    return X_out

def add_const(X: List, r: int) -> List:
    """
    Add round constant to the state (XOR with 1 at specific LSB positions).
    """
    if r >= len(ROUND_CONSTANTS):
        raise ValueError(f"Round number {r} exceeds maximum {len(ROUND_CONSTANTS)-1}")
    
    constant = ROUND_CONSTANTS[r]
    X_new = X[:]
        
    for i in range(16):
        if (constant >> i) & 0x1:
            X_new[i] = X_new[i] + 1 
        
    return X_new

def single_sbox(x0, x1, x2) -> Tuple:
  """
  Forward 3-bit S-box (Chi step's core component).
  """
  y0 = x0 + (1 + x1) * x2
  y1 = x1 + (1 + x2) * x0
  y2 = x2 + (1 + x0) * x1
  return y0, y1, y2

def chi(A: List) -> List:
  """
  Chi step: Apply S-box across the y-planes for each (x, z) column.
  """
  B = [R(0) for _ in range(STATE_SIZE)]
  plane_size = X_SIZE * LANE_SIZE
  
  for j in range(plane_size):
    B[0 + j], B[plane_size + j], B[2*plane_size + j] = single_sbox(
      A[0 + j], A[plane_size + j], A[2*plane_size + j]
    )
  return B

def rho_east(X: List) -> List:
    """
    Rho east step: Apply lane rotations to planes y=1 and y=2.
    """
    plane_size = X_SIZE * LANE_SIZE
    X_out = X[:]
        
    # y=1: (0, 1) - Rotate 1 bit
    X_out[plane_size:2*plane_size] = single_matrix(X[plane_size:2*plane_size], 0, 1)
        
    # y=2: (2, 8) - Shift 2 lanes East and Rotate 8 bits
    X_out[2*plane_size:3*plane_size] = single_matrix(X[2*plane_size:3*plane_size], 2, 8)
    
    return X_out


# -----------------------------------------------------------
# Inverse Round Functions
# -----------------------------------------------------------

def inv_single_sbox(y0, y1, y2) -> Tuple:
  """
  Inverse 3-bit S-box. (Inverse Chi step core component)
  """
  x2 = y2 + (1 + y0) * y1
  x1 = y1 + (1 + y2) * y0
  x0 = y0 + (1 + y1) * y2
  return x0, x1, x2

def inv_chi(A: List) -> List:
  """
  Inverse Chi step.
  """
  B = [R(0) for _ in range(STATE_SIZE)]
  plane_size = X_SIZE * LANE_SIZE
  
  for j in range(plane_size):
    B[0 + j], B[plane_size + j], B[2*plane_size + j] = inv_single_sbox(
      A[0 + j], A[plane_size + j], A[2*plane_size + j]
    )
  return B

def inv_rho_east(X: List) -> List:
    """
    Inverse Rho East step. Reverses the rotations of rho_east.
    """
    plane_size = X_SIZE * LANE_SIZE
    X_out = X[:]
        
    # y=1: (0, 1) -> (0, -1)
    X_out[plane_size:2*plane_size] = single_matrix(X[plane_size:2*plane_size], 0, -1)
        
    # y=2: (2, 8) -> (-2, -8)
    X_out[2*plane_size:3*plane_size] = single_matrix(X[2*plane_size:3*plane_size], -2, -8)
    
    return X_out

def inv_rho_west(X: List) -> List:
    """
    Inverse Rho West step. Reverses the rotations of rho_west.
    """
    plane_size = X_SIZE * LANE_SIZE
    X_out = X[:]
        
    # y=1: (1, 0) -> (-1, 0)
    X_out[plane_size:2*plane_size] = single_matrix(X[plane_size:2*plane_size], -1, 0)
        
    # y=2: (0, 11) -> (0, -11)
    X_out[2*plane_size:3*plane_size] = single_matrix(X[2*plane_size:3*plane_size], 0, -11)
        
    return X_out

# -----------------------------------------------------------
# Inverse Theta (File Load Implementation)
# -----------------------------------------------------------

M_THETA_INV = None

def load_theta_reverse(filename: str) -> Matrix:
    """
    Reads the inverse matrix M_Theta_inv from a file following the C++ reference logic.
    """
    M_INV = Matrix(GF(2), STATE_SIZE, STATE_SIZE, 0)
  
    try:
        with open(filename, 'r') as f:
            for i in range(STATE_SIZE):
                line = f.readline().strip()
                if not line:
                    logger.error(f"Error reading file: Line {i} is empty. Expected {STATE_SIZE} rows.")
                    raise ValueError("Incomplete thetaReverse file.")
            
                try:
                    positions = [int(pos) for pos in line.split()]
                except ValueError:
                    logger.error(f"Error parsing line {i}: Non-integer value found.")
                    raise
                
                # Build M_INV[i, pos] = 1
                for pos in positions:
                    if 0 <= pos < STATE_SIZE:
                        M_INV[i, pos] = 1
                    else:
                        logger.warning(f"Index {pos} out of range in line {i}. Skipping.")

    except FileNotFoundError:
        logger.error(f"ERROR: Inverse matrix file '{filename}' not found. Cannot proceed with inv_theta.")
        raise
        
    return M_INV

def get_inverse_theta_matrix():
    """Load and cache the inverse matrix M_Theta_inv."""
    global M_THETA_INV
    if M_THETA_INV is not None:
        return M_THETA_INV
    
    logger.info(f"Loading Xoodoo Theta inverse matrix from {THETA_REVERSE_FILE}...")
    
    if not os.path.exists(THETA_REVERSE_FILE):
        logger.error(f"File {THETA_REVERSE_FILE} not found. Check file path: {THETA_REVERSE_FILE}")
        raise FileNotFoundError(f"Required file {THETA_REVERSE_FILE} not found.")

    M_THETA_INV = load_theta_reverse(THETA_REVERSE_FILE)
    logger.info("Inverse matrix loading completed.")
    return M_THETA_INV


def inv_theta(Y: List) -> List:
    """
    Inverse Theta step: X = M_Theta_inv * Y (Linear operation in ANF).
    """
    M_INV = get_inverse_theta_matrix()
    
    X_out = [R(0) for _ in range(STATE_SIZE)]
    
    # Perform matrix multiplication X_out[i] = sum(M_INV[i, j] * Y[j]) mod 2
    for i in range(STATE_SIZE):
        result = R(0)
        for j in range(STATE_SIZE):
            if M_INV[i, j] == 1:
                result = result + Y[j] # XOR in ANF ring
        X_out[i] = result
        
    return X_out


# -----------------------------------------------------------
# High-Level Permutation Functions
# -----------------------------------------------------------

def round(X: List, r: int) -> List:
    """
    Apply r forward rounds of Xoodoo permutation.
    """
    if r > XOODOO_ROUNDS:
        raise ValueError(f"Number of rounds {r} exceeds maximum {XOODOO_ROUNDS}")
    
    for i in range(r):
        X = theta(X)
        X = rho_west(X)
        X = add_const(X, i)
        X = chi(X)
        X = rho_east(X)
    return X

def inv_round(X: List, r: int) -> List:
    """
    Apply r inverse rounds of Xoodoo permutation.
    """
    if r > XOODOO_ROUNDS:
        raise ValueError(f"Number of rounds {r} exceeds maximum {XOODOO_ROUNDS}")
    
    for i in range(r-1, -1, -1): 
        X = inv_rho_east(X)
        X = inv_chi(X)
        X = add_const(X, i) 
        X = inv_rho_west(X)
        X = inv_theta(X)
    return X

# -----------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------

def print_Xstate(X: List) -> None:

    """
    Pretty-print the Xoodoo state in 3x4 format (3 rows, 4 columns).
    The state is organized as 3 rows (y = 0..2) by 4 columns (x = 0..3) of 32-bit words.
    Each word is displayed in hexadecimal format.
    Args:
        X: State vector to print
    """
    # Print state as Y_SIZE rows, each with X_SIZE words
    for y in range(Y_SIZE):
        row_print = ""
        for x in range(X_SIZE):
            # Calculate word index
            word_index = y * X_SIZE + x
            # Get the binary state for this word
            state_binary = X[LANE_SIZE * word_index: LANE_SIZE * word_index + LANE_SIZE]

            # Check if binary state length is valid
            if len(state_binary) % 8 != 0:
                logger.error("The length of a word should be a multiple of 8")
                return
            # Compute hex every 8 bits
            state_hex = ""
            for k in range(len(state_binary) // 8):
                # Compute 8 bits int value
                tmp = 0
                for bit in range(8):
                    # Correct bit shifting: process from LSB to MSB
                    tmp += (int(state_binary[k * 8 + bit]) << bit)
                # Convert int value to hex, ensure 2-digit format, then add to the state
                state_hex = hex(tmp)[2:].zfill(2) + state_hex
            # Format hex string with "0x" prefix
            state_hex = "0x" + state_hex
            # Add to the row, delimiter is " "(space)
            row_print += state_hex + (" " if x < X_SIZE - 1 else "")
        print(row_print)
    print("------")



def hex_to_binary(hex_input: int, binary_length: int = 32) -> List[int]:

    """
    Convert a hexadecimal number to binary representation.
    Args:
        hex_input: Input hexadecimal number
        binary_length: Length of binary output

    Returns:
        List of binary digits (0/1)
    """

    binary_output = []
    for j in range(binary_length):
        binary_output.append(hex_input >> (j) & 0x1)
    return binary_output


def hex_list_to_bit_list(hex_list: List[int], lanesize:int) -> List[int]:

    """
    Convert a list of integers into a contiguous list of bits (0/1).
    Bit order per integer word:
    - LSB → MSB within each word (i.e., bit 0 first), matching hex_to_binary logic.
    - Only the lowest `word_bits` of each integer are taken.

    Args:
        hex_list: list of integers (e.g., [0x1b, 0x8082, ...])
        word_bits: number of bits to extract per integer (default 32)

    Returns:
        A list of bits (integers 0/1) representing the concatenation of all
        provided integers in LSB-first order per word.
    """

    bit_list: List[int] = []
    mask = (1 << lanesize) - 1 if lanesize < 64 else (1 << lanesize) - 1
    for val in hex_list:
        word = int(val) & mask
        for k in range(lanesize):
             bit_list.append((word >> k) & 0x1)

    return bit_list



def main() -> None:
    """
    Main function for testing and demonstration. Initializes the global PolyBoRi ring R.
    """
    global R, x
    # 1. Initialize the global PolyBoRi ANF ring R
    try:
        # Define the Boolean Polynomial Ring and its variables
        R = declare_ring([Block('x', STATE_SIZE)], globals())
        # Get the list of variables for initial state construction
        # Note: x is now available globally due to declare_ring(..., globals())
        logger.info("PolyBoRi ANF environment initialized successfully.")   
    except NameError:
        logger.error("Could not initialize PolyBoRi environment. Aborting.")
        return

    # 2. Setup Test State
    test_state = [R(0) for _ in range(STATE_SIZE)]
    
    logger.info("Xoodoo Round Function in ANF form")
    logger.info(f"State size: {STATE_SIZE} bits")
    logger.info(f"Lane size: {LANE_SIZE} bits")
    logger.info(f"Number of rounds: {XOODOO_ROUNDS}")
    
    # 3. Run Permutations
    try:
        res = round(test_state, XOODOO_ROUNDS)
        print_Xstate(res)
        logger.info("Forward Round (Rounds=12) Complete.")

        res = inv_round(res, XOODOO_ROUNDS)
        logger.info("Inverse Round (Rounds=12) Complete.")
        print_Xstate(res)
        
    except FileNotFoundError:
        logger.error("Skipping round execution due to missing thetaReverse.txt file. Cannot test inv_theta.")

if __name__ == '__main__':
    main()