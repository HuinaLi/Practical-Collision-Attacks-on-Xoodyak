# SAC25-Practical-Collision-Attacks-on-Reduced-Round-Xoodyak-Hash-Mode
The source codes and results are used to help verify the results in our paper.


## Xoodoo Collision Analysis Tool项目概述

本项目是一个专门用于分析Xoodoo密码算法碰撞攻击的工具集。Xoodoo是一个384位的置换函数，应用于密码学哈希函数和可扩展输出函数(XOF)中。本项目实现了对Xoodoo算法的差分路径搜索和碰撞对搜素功能。

## 主要功能

### 1. 差分路径搜索 (Trail Search)
- **位置**: `trail_search/`
- **功能**: 搜索Xoodoo算法的差分路径，寻找具有特定活跃S盒数量的碰撞轨迹
- **特点**: 
  - 支持2-4轮Xoodoo的差分路径搜索
  - 使用SAT求解器进行约束求解
  - 可配置活跃S盒数量的上下界

### 2. 碰撞对查找 (Right Pair Search)
- **位置**: `rightpair_search/`
- **功能**: 基于已知差分路径查找具体的碰撞消息对
- **特点**:
  - 验证差分路径的有效性
  - 生成具体的碰撞消息对
  - 支持多轮Xoodoo的碰撞查找

## 项目结构

```
xoodoo_collision/
├── readme.md                    # 项目说明文档
├── trail_search/               # 差分路径搜索模块
│   ├── code/                   # 核心代码
│   │   ├── trailmodel.py      # 差分路径模型生成
│   │   ├── solvemodel.py      # SAT求解器调用
│   │   ├── print_trail.py     # 结果输出
│   │   └── xooroundf.py       # Xoodoo轮函数实现
│   ├── cons/                   # 约束文件(.cnf)
│   ├── logs/                   # 求解日志
│   └── result/                 # 搜索结果
├── rightpair_search/           # 碰撞对查找模块
│   ├── code/                   # 核心代码
│   │   ├── solve_rightpair.py # 碰撞对求解主程序
│   │   ├── verifydc_model.py  # 差分路径验证模型
│   │   ├── print_right_pair.py # 碰撞对输出
│   │   ├── xooroundf.py       # Xoodoo轮函数实现
│   │   └── pairrun.sh         # 批处理脚本
│   ├── cons/                   # 约束文件(.cnf)
│   ├── logs/                   # 求解日志
│   └── result/                 # 碰撞对结果
```

## 核心算法

### Xoodoo轮函数
Xoodoo算法包含以下操作：
1. **θ (theta)**: 线性扩散层
2. **ρ_west (rhowest)**: 西向旋转
3. **ι (addConst)**: 添加轮常数
4. **χ (chi)**: 非线性S盒层
5. **ρ_east (rhoeast)**: 东向旋转

### 差分路径搜索算法
1. 构建CNF约束模型，包含：
   - Xoodoo轮函数的差分传播约束
   - 活跃S盒数量的约束
   - 差分路径的边界条件
2. 使用SAT求解器寻找满足约束的差分路径
3. 逐步降低活跃S盒数量，寻找最优路径

### 碰撞对查找算法
1. 基于已知差分路径构建验证模型
2. 添加具体的值约束和差分约束
3. 使用SAT求解器查找满足条件的消息对
4. 验证找到的消息对确实产生碰撞

## 使用方法

### 差分路径搜索

```bash
# 生成差分路径模型
python trail_search/code/trailmodel.py -r 3 -b1 64 -b2 0 -b3 64 -f trail_search/cons/

# 求解差分路径
python trail_search/code/solvemodel.py -r 3 -b1 64 -b2 0 -b3 64 -f trail_search/cons/ -sat /path/to/solver -satTrd 4
```

### 碰撞对查找

```bash
# 查找碰撞对
python rightpair_search/code/solve_rightpair.py -r 2 -w 128 -m 0 -satTrd 10 -f rightpair_search/cons/ -sat /path/to/solver
```

### 批处理运行

```bash
# 运行差分路径搜索批处理
bash trail_search/code/run.sh

# 运行碰撞对查找批处理
bash rightpair_search/code/pairrun.sh
```

## 参数说明

### 差分路径搜索参数
- `-r, --round`: 轮数 (2-4)
- `-b1, --bound_start`: 第一轮活跃S盒数量上界
- `-b2, --bound_mid`: 中间轮活跃S盒数量上界  
- `-b3, --bound_end`: 最后一轮活跃S盒数量上界
- `-f, --path`: 输出文件路径

### 碰撞对查找参数
- `-r, --rounds`: 轮数
- `-w, --weight`: 权重/活跃S盒数量
- `-m, --stratrnd`: 起始轮数
- `-satTrd, --thread`: SAT求解器线程数
- `-sat, --solver`: SAT求解器路径

## 依赖环境

- Python
- SageMath (用于多项式环和SAT编码)
- SAT求解器 (如lingeling, treengeling等)
- pysat (Python SAT库)

## 输出结果

### 差分路径结果
- 显示每轮的活跃S盒数量
- 输出差分路径的十六进制表示
- 记录搜索时间和求解状态

### 碰撞对结果
- 显示输入消息对的十六进制值
- 输出每轮的中间状态
- 验证碰撞的有效性

## 应用场景

1. **密码分析**: 评估Xoodoo算法的安全性
2. **碰撞攻击**: 寻找Xoodoo的碰撞攻击方法
3. **差分分析**: 研究Xoodoo的差分特性
4. **学术研究**: 支持密码学理论研究

## 注意事项

1. 确保SAT求解器路径正确配置
2. 大参数搜索可能需要较长时间
3. 结果文件会占用较多磁盘空间
4. 建议在性能较好的机器上运行

## 作者信息

- 作者: Huina Li
- 创建时间: 2024年12月
- 版本: 1.0

## 许可证

本项目仅供学术研究使用。
```

