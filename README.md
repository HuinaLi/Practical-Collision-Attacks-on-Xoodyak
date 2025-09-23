# SAC25-Practical-Collision-Attacks-on-Reduced-Round-Xoodyak-Hash-Mode
The source codes and results are used to help verify the results in our paper.
All experiments are conducted on a server with Intel(R) Xeon(R) Gold 6230R CPU @ 2.10GHz 26 Cores, 125G RAM, and CentOS Linux 7. 
- SageMath version 10.2
- Python 3.10.14
- treengeling 1.0.0

## Xoodoo Collision Analysis Tool Project Overview

This project is a specialized toolset for analyzing collision attacks on the Xoodoo. Xoodoo is a 384-bit permutation  used in cryptographic hash functions and eXtendable Output Functions (XOF). This project implements  collision pair search functionality for the Xoodoo algorithm.

## Main Features

###  Collision Pair Search (Right Pair Search)
- **Location**: `rightpair_search/`
- **Function**: Find specific collision message pairs based on known differential trails
- **Features**:
  - Validates the effectiveness of differential trails
  - Generates specific collision message pairs
  - Supports multi-round Xoodoo collision search

## Project Structure

```
xoodoo_collision/
├── readme.md                    # Project documentation
├── rightpair_search/           # Collision pair search module
│   ├── code/                   # Core code
│   │   ├── solve_rightpair.py # Main collision pair solver
│   │   ├── verifydc_model.py  # Differential trail verification model
│   │   ├── print_right_pair.py # Collision pair output
│   │   ├── xooroundf.py       # Xoodoo round function implementation
│   │   └── pairrun.sh         # Batch processing script
│   ├── cons/                   # Constraint files (.cnf)
│   ├── logs/                   # Solver logs
│   └── result/                 # Collision pair results
```

## Core Algorithms

### Xoodoo Round Function
The Xoodoo algorithm consists of the following operations:
1. **θ (theta)**: Linear diffusion layer
2. **ρ_west (rhowest)**: Plane shift rotation
3. **ι (addConst)**: Add round constants
4. **χ (chi)**: Non-linear S-box layer
5. **ρ_east (rhoeast)**: Plane shift rotation

### Collision Pair Search Algorithm
1. Build verification models based on known differential trails
2. Add specific value constraints and differential constraints
3. Use SAT solvers to find message pairs satisfying conditions
4. Verify that found message pairs indeed produce collisions

## Usage

### Collision Pair Search

```bash
# Find collision pairs
python rightpair_search/code/solve_rightpair.py -r 2 -w 128 -m 0 -satTrd 10 -f rightpair_search/cons/ -sat /path/to/solver
```

### Batch Processing

```bash
# Run differential trail search batch
bash trail_search/code/run.sh

# Run collision pair search batch
bash rightpair_search/code/pairrun.sh
```

## Parameter Description

### Collision Pair Search Parameters
- `-r, --rounds`: Number of rounds
- `-w, --weight`: Weight/number of active S-boxes
- `-m, --stratrnd`: Starting round number
- `-satTrd, --thread`: Number of SAT solver threads
- `-sat, --solver`: SAT solver path

## Dependencies

- Python
- SageMath (for polynomial rings and SAT encoding)
- SAT solver (such as lingeling, treengeling, etc.)
- pysat (Python SAT library)

## Output Results

### Collision Pair Results
- Display hexadecimal values of input message pairs
- Output intermediate states for each round
- Verify validity of collisions

## Author Information

- Author: Huina Li
- Created: December 2024
- Version: 1.0

## License

This project is for academic research use only.
```



