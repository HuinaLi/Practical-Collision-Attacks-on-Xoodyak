#!/bin/bash

run_task() {
    local ROUND=$1
    local WEIGHT=$2
    local satTrd=$3
    local STARTR=$4
    local index=$5

    python -u /home/hnli/xoodyak-collision/code/solve_rightpair.py \
        -r $ROUND  -w $WEIGHT -m $STARTR -satTrd $satTrd \
        -f /home/hnli/xoodyak-collision/cons \
        -sat /home/hnli/sat-solvers/cadical/build/cadical \
        > /home/hnli/xoodyak-collision/logs/SFScollision_${ROUND}R_w${WEIGHT}_cad_t${satTrd}_start${STARTR}_kmt.log 2>&1
    
    if [ $? -ne 0 ]; then
        echo "Task $index failed" >> /home/hnli/xoodyak-collision/logs/error.log
    fi
    
}

# 启动任务
run_task 4 256 0 0 1 & 

wait