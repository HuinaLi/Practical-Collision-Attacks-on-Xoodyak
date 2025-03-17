#!/bin/bash

run_task() {
    local ROUND=$1
    local WEIGHT=$2
    local satTrd=$3
    local STARTR=$4
    local index=$5

    python -u /home/user/lhn/xoodoo_collision/rightpair_search/code/solve_rightpair.py \
        -r $ROUND  -w $WEIGHT -m $STARTR -satTrd $satTrd \
        -f /home/user/lhn/xoodoo_collision/rightpair_search/cons \
        -sat /home/user/lhn/lingeling/treengeling \
        > /home/user/lhn/xoodoo_collision/rightpair_search/logs/collision_2R_w${WEIGHT}_tree_t${satTrd}_start${STARTR}_kmt.log 2>&1
    
    if [ $? -ne 0 ]; then
        echo "Task $index failed" >> /home/user/lhn/xoodoo_collision/rightpair_search/logs/error.log
    fi
    
}

# 启动任务
run_task 2 128 10 0 1 & 

wait