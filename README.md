# SAC25 Practical Collision Attacks on Reduced-Round Xoodyak (Hash Mode)

This repository contains source code and experiment outputs used to verify the results in our paper.

## Environment

Experiments were run on a server with Intel(R) Xeon(R) Gold 6230R CPU @ 2.10GHz, 26 cores, 125G RAM, and CentOS Linux 7.

- SageMath 10.2
- Python 3.10.14
- treengeling 1.0.0

### Environment Setup (Required Before Running)

1. Install Sage via conda following the official guide:  
   [SageMath conda installation](https://doc.sagemath.org/html/en/installation/conda.html)
2. Restart terminal after conda installation.
3. Create and activate an environment (example name: `sage`):

```bash
conda create -n sage sage python=3.10
conda activate sage
```

Or with mamba:

```bash
mamba create -n sage sage python=3.10
mamba activate sage
```

4. Install PySAT:

```bash
pip install "python-sat[aiger,approxmc,cryptosat,pblib]"
python -c "import pysat; print('pysat installed successfully')"
```

5. Install SAT solvers:
   - Lingeling family: [https://github.com/arminbiere/lingeling](https://github.com/arminbiere/lingeling)
   - CaDiCaL: [https://github.com/arminbiere/cadical](https://github.com/arminbiere/cadical)

## Overview

The project provides tooling for collision analysis on the Xoodoo permutation (384-bit), including:

- differential constraint model construction,
- SAT solving for candidate pairs,
- right-pair verification and output.

## Project Structure

```text
xoodyak-collision/
├── code/
│   ├── xooroundf.py          # Xoodoo round operations
│   ├── verifydc_model.py     # DC verification CNF model builder
│   ├── solve_rightpair.py    # End-to-end SAT solve + check pipeline
│   ├── print_right_pair.py   # Reconstruct and print right pairs
│   ├── read_dc_logfile.py    # Parse SAT solver outputs
│   ├── ban_solution.py       # Block known solutions in CNF
│   └── pairrun.sh            # Batch runner
├── cons/                     # Constraint and CNF files
├── logs/                     # Runtime logs
├── result/                   # Right-pair outputs
├── LICENSE
└── README.md
```

## Core Round Operations

Implemented in `code/xooroundf.py`:

1. `theta` (linear diffusion)
2. `rho_west` (plane/lane rotation)
3. `add_const` (round constant injection)
4. `chi` (non-linear layer)
5. `rho_east` (plane/lane rotation)

## Usage

### 1) Activate Sage Environment

```bash
conda activate sage
```

### 2) Build Verification Model Only

```bash
python /home/hnli/xoodyak-collision/code/verifydc_model.py \
  -r 3 \
  -f /home/hnli/xoodyak-collision/cons/test.cnf \
  -w 192 \
  -m 0
```

Expected output prefix:

```text
we have arrived here
12
#Round: 3, #as =: 192, START:
New DC Verify Model Constructed:) var_num:5761, clause_num:45888
```

### 3) Full Right-Pair Search Pipeline

```bash
python /home/hnli/xoodyak-collision/code/solve_rightpair.py \
  -r 3 \
  -w 192 \
  -m 0 \
  -satTrd 12 \
  -f /home/hnli/xoodyak-collision/cons \
  -sat /home/hnli/sat-solvers/cadical/build/cadical
```

### 4) Batch Run

```bash
bash /home/hnli/xoodyak-collision/code/pairrun.sh
```

## Minimal Reproducible Example (3R, w=192)

Run the following commands in order:

```bash
python /home/hnli/xoodyak-collision/code/solve_rightpair.py \
  -r 3 \
  -w 192 \
  -m 0 \
  -satTrd 12 \
  -f /home/hnli/xoodyak-collision/cons \
  -sat /home/hnli/sat-solvers/cadical/build/cadical 
```

A reference log is available at:

`/home/hnli/xoodyak-collision/logs/SFScollision_3_w192_cad_t0_start0_kmt.log`

Reference output:

```text
we have arrived here
12
#Round: 3, #as =: 192, START:
New DC Verify Model Constructed:) var_num:5761, clause_num:45888
Solve START: no.1
solve cost: 9.736500 s
Find!
Check:
Output has been saved to /home/hnli/xoodyak-collision/result/3round_w192_rightpair_no1.log
check cost: 1.087854 s
__________End____________
```

Note: timing values (for example `solve cost` and `check cost`) may vary across machines.

## Key Parameters

- `-r, --rounds`: number of rounds
- `-w, --weight`: target weight (active S-box count setting)
- `-m, --stratrnd`: start round index
- `-f, --path`: CNF output path or output directory
- `-satTrd, --thread`: SAT solver thread option
- `-sat, --solver`: SAT solver executable path

## Notes

- `code/__pycache__/` is generated cache and should not be tracked.
- Prefer running all scripts inside the `sage` conda environment.

## Author

- Huina Li

## License

MIT License.
