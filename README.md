# SAC25-Practical-Collision-Attacks-on-Reduced-Round-Xoodyak-Hash-Mode
The source codes and results are used to help verify the results in our paper.
All experiments are conducted on a server with Intel(R) Xeon(R) Gold 6230R CPU @ 2.10GHz 26 Cores, 125G RAM, and CentOS Linux 7. 
- SageMath version 10.2
- Python 3.10.14
- treengeling 1.0.0

## Xoodoo Collision Analysis Tool Project Overview

This project is a specialized toolset for analyzing collision attacks on the Xoodoo. Xoodoo is a 384-bit permutation  used in cryptographic hash functions and eXtendable Output Functions (XOF). This project implements differential trail search and collision pair search functionality for the Xoodoo algorithm.

## Main Features

### 1. Differential Trail Search
- **Location**: `trail_search/`
- **Function**: Search for round-reduced Xoodoo differential trails, finding collision trails with specific numbers of active S-boxes
- **Features**:
  - Supports 2-4 round Xoodoo differential trail search
  - Uses SAT solvers for constraint solving
  - Configurable upper and lower bounds for active S-box counts

### 2. Collision Pair Search (Right Pair Search)
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
├── trail_search/               # Differential trail search module
│   ├── code/                   # Core code
│   │   ├── trailmodel.py      # Differential trail model generation
│   │   ├── solvemodel.py      # SAT solver invocation
│   │   ├── print_trail.py     # Result output
│   │   └── xooroundf.py       # Xoodoo round function implementation
│   ├── cons/                   # Constraint files (.cnf)
│   ├── logs/                   # Solver logs
│   └── result/                 # Search results
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

### Differential Trail Search Algorithm
1. Build CNF constraint models including:
   - Differential propagation constraints for Xoodoo round functions
   - Constraints on the number of active S-boxes
   - Boundary conditions for differential trails
2. Use SAT solvers to find differential trails satisfying constraints
3. Gradually reduce the number of active S-boxes to find optimal trails

### Collision Pair Search Algorithm
1. Build verification models based on known differential trails
2. Add specific value constraints and differential constraints
3. Use SAT solvers to find message pairs satisfying conditions
4. Verify that found message pairs indeed produce collisions

## Usage

### Differential Trail Search

```bash
# Generate differential trail model
python trail_search/code/trailmodel.py -r 3 -b1 64 -b2 0 -b3 64 -f trail_search/cons/

# Solve differential trail
python trail_search/code/solvemodel.py -r 3 -b1 64 -b2 0 -b3 64 -f trail_search/cons/ -sat /path/to/solver -satTrd 4
```

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

### Differential Trail Search Parameters
- `-r, --round`: Number of rounds (2-4)
- `-b1, --bound_start`: Upper bound for active S-boxes in first round
- `-b2, --bound_mid`: Upper bound for active S-boxes in middle rounds
- `-b3, --bound_end`: Upper bound for active S-boxes in last round
- `-f, --path`: Output file path

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

### Differential Trail Results
- Display number of active S-boxes per round
- Output hexadecimal representation of differential trails
- Record search time and solver status

### Collision Pair Results
- Display hexadecimal values of input message pairs
- Output intermediate states for each round
- Verify validity of collisions

## Application Scenarios

1. **Cryptanalysis**: Evaluate the security of the Xoodoo algorithm
2. **Collision Attacks**: Find collision attack methods for Xoodoo
3. **Differential Analysis**: Study differential properties of Xoodoo
4. **Academic Research**: Support theoretical cryptography research

## Notes

1. Ensure SAT solver paths are correctly configured
2. Large parameter searches may require significant time
3. Result files may occupy considerable disk space
4. Recommend running on high-performance machines

## Author Information

- Author: Huina Li
- Created: December 2024
- Version: 1.0

## License

This project is for academic research use only.
```



