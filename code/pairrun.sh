#!/bin/bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
RUN_ID="${RUN_ID:-$(date +%Y%m%d_%H%M%S)}"
ATTACK_TYPE="${ATTACK_TYPE:-sfscollision}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
SAT_SOLVER_TYPE="${SAT_SOLVER_TYPE:-auto}"
DEFAULT_TREENGELING="/home/hnli/sat-solvers/lingeling/treengeling"
if [ -n "${SAT_SOLVER:-}" ]; then
    SAT_SOLVER_BIN="${SAT_SOLVER}"
elif [ -x "${DEFAULT_TREENGELING}" ]; then
    SAT_SOLVER_BIN="${DEFAULT_TREENGELING}"
else
    SAT_SOLVER_BIN="$(command -v treengeling || true)"
fi

if [ "${ATTACK_TYPE}" = "collision" ]; then
    ATTACK_FLAG="--collision"
elif [ "${ATTACK_TYPE}" = "sfscollision" ]; then
    ATTACK_FLAG="--sfscollision"
else
    echo "Unsupported ATTACK_TYPE=${ATTACK_TYPE}; expected collision or sfscollision" >&2
    exit 2
fi

if [ -z "${SAT_SOLVER_BIN}" ]; then
    echo "SAT solver not found. Set SAT_SOLVER=/path/to/treengeling or put treengeling on PATH." >&2
    exit 2
fi

mkdir -p "${ROOT_DIR}/cons" "${ROOT_DIR}/logs" "${ROOT_DIR}/result"

run_task() {
    local ROUND=$1
    local WEIGHT=$2
    local satTrd=$3
    local STARTR=$4
    local index=$5
    local solver_name
    local solver_tag
    solver_name="$(basename "${SAT_SOLVER_BIN}")"
    case "${solver_name}" in
        treengeling) solver_tag="tree_t${satTrd}" ;;
        plingeling) solver_tag="plingeling_t${satTrd}" ;;
        cadical|kissat) solver_tag="${solver_name}" ;;
        *) if [ "${SAT_SOLVER_TYPE}" = "parallel" ]; then solver_tag="${solver_name}_t${satTrd}"; else solver_tag="${solver_name}"; fi ;;
    esac
    local log_file="${ROOT_DIR}/logs/${ATTACK_TYPE}_${ROUND}R_w${WEIGHT}_${solver_tag}_start${STARTR}_${RUN_ID}.log"

    "${PYTHON_BIN}" -u "${SCRIPT_DIR}/solve_rightpair.py" \
        -r "${ROUND}" -w "${WEIGHT}" -m "${STARTR}" -satTrd "${satTrd}" \
        -f "${ROOT_DIR}/cons" \
        -sat "${SAT_SOLVER_BIN}" \
        --solver-type "${SAT_SOLVER_TYPE}" \
        "${ATTACK_FLAG}" \
        --run-id "${RUN_ID}" \
        > "${log_file}" 2>&1

    if [ $? -ne 0 ]; then
        echo "Task ${index} failed; see ${log_file}" >> "${ROOT_DIR}/logs/error_${RUN_ID}.log"
        return 1
    fi
}

# 启动任务
run_task 3 192 12 0 1 &

wait
