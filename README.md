# SAC25 Practical Collision Attacks on Reduced-Round Xoodyak Hash Mode

This repository contains source code and experiment outputs used to verify the results in our paper.

## Environment

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

1. Install PySAT:

```bash
pip install "python-sat[aiger,approxmc,cryptosat,pblib]"
python -c "import pysat; print('pysat installed successfully')"
```

1. Install SAT solvers:
  - Lingeling family: [https://github.com/arminbiere/lingeling](https://github.com/arminbiere/lingeling)
  - CaDiCaL: [https://github.com/arminbiere/cadical](https://github.com/arminbiere/cadical)

Set the solver path once per shell session if the binary is not on `PATH`:

```bash
export SAT_SOLVER=/path/to/treengeling
```

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

Run commands from the repository root after activating the Sage environment:

```bash
cd /path/to/xoodyak-collision
conda activate sage
export SAT_SOLVER=/path/to/treengeling
```

Generated CNF, solver log, run log, and right-pair output filenames include a run timestamp in `YYYYmmdd_HHMMSS` format.

Collision runs support two initialization modes:

- `constraints`: add traditional unit constraints with `{Q.add(a_vars[0][i] + 1)}` or `{Q.add(a_vars[0][i])}`.
- `substitution`: substitute constants during model construction with `{Q.add(a_vars[0][i] + 1) and a_vars[0][i] = ring(1)}` or `{Q.add(a_vars[0][i]) and a_vars[0][i] = ring(0)}`.

### 1) Build Verification Model Only

```bash
python code/verifydc_model.py \
  -r 3 \
  -f cons \
  -w 192 \
  -m 0 \
  --sfscollision
```

Use `--collision` instead of `--sfscollision` to include the extra initialization constraints. Collision mode defaults to `--collision-init-mode constraints`; use `--collision-init-mode substitution` to substitute initialization constants during model construction.

Expected output prefix:

```text
we have arrived here
12
#Round: 3, #as =: 192, START:
New DC Verify Model Constructed:) var_num:5761, clause_num:45888
CNF has been saved to cons/sfscollision_3round_w192_YYYYmmdd_HHMMSS.cnf
```

### 2) Full Right-Pair Search Pipeline

```bash
python code/solve_rightpair.py \
  -r 3 \
  -w 192 \
  -m 0 \
  -satTrd 12 \
  -f cons \
  -sat "$SAT_SOLVER" \
  --sfscollision
```

For the collision variant:

```bash
python code/solve_rightpair.py \
  -r 2 \
  -w 128 \
  -m 0 \
  -satTrd 10 \
  -f cons \
  -sat "$SAT_SOLVER" \
  --collision \
  --collision-init-mode constraints
```

For the substitution-based collision initialization:

```bash
python code/solve_rightpair.py \
  -r 2 \
  -w 128 \
  -m 0 \
  -satTrd 10 \
  -f cons \
  -sat "$SAT_SOLVER" \
  --collision \
  --collision-init-mode substitution
```

### 3) Batch Run

```bash
SAT_SOLVER="$SAT_SOLVER" SAT_SOLVER_TYPE=auto ATTACK_TYPE=sfscollision bash code/pairrun.sh
```

Set `ATTACK_TYPE=collision` for the collision initialization constraints. Set `PYTHON_BIN=/path/to/python` if the activated environment's Python is not the first Python 3 executable on `PATH`.

## Minimal Reproducible Example (3R, w=192)

Run the following command from the repository root:

```bash
python code/solve_rightpair.py \
  -r 3 \
  -w 192 \
  -m 0 \
  -satTrd 12 \
  -f cons \
  -sat "$SAT_SOLVER" \
  --sfscollision
```

Reference output:

```text
we have arrived here
12
#Round: 3, #as =: 192, START:
Attack type: sfscollision
Run ID: YYYYmmdd_HHMMSS
New DC Verify Model Constructed:) var_num:5761, clause_num:45888
CNF has been saved to cons/sfscollision_3round_w192_YYYYmmdd_HHMMSS.cnf
Solve START: no.1
solve cost: 9.736500 s
Find!
Check:
Output has been saved to result/sfscollision_3round_w192_YYYYmmdd_HHMMSS_rightpair_no1.log
check cost: 1.087854 s
__________End____________
```

Note: timing values (for example `solve cost` and `check cost`) may vary across machines.

## Key Parameters

- `-r, --rounds`: number of rounds
- `-w, --weight`: target weight (active S-box count setting)
- `-m, --stratrnd`: start round index
- `-f, --path`: CNF output path or output directory; defaults to `cons` in `solve_rightpair.py`
- `-satTrd, --thread`: thread count for parallel solvers (`treengeling`/`plingeling`); ignored for sequential solvers (`cadical`/`kissat`)
- `-sat, --solver`: SAT solver executable path; defaults to `SAT_SOLVER`, `/home/hnli/sat-solvers/lingeling/treengeling`, or `treengeling` on `PATH`
- `--solver-type`: `auto`, `parallel`, or `sequential`; auto treats `treengeling`/`plingeling` as parallel and `cadical`/`kissat` as sequential
- `--sfscollision`: default attack type; does not add initialization constraints
- `--collision`: adds the initialization constraints in `verifydc_model.py`
- `--collision-init-mode`: collision initialization mode; `constraints` keeps variables and adds unit constraints, while `substitution` replaces initialized state bits with constants before CNF generation
- `--run-id`: optional timestamp/run id override for reproducible filenames


## Notes

- `code/__pycache__/` is generated cache and should not be tracked.
- Prefer running all scripts inside the `sage` conda environment.
- Avoid hard-coded absolute project paths; scripts derive paths from their own location or CLI arguments.
- The runtimes of SAT instances are sensitive to the execution environment; however, the discrepancies are not substantial

## Author

- Huina Li

## License

MIT License.
