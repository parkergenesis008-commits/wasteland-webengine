---
title: "Superfluid Vortex Shedding — Momentum Rectifier"
date: "2026-06-04"
tags: ["superfluid", "vortex", "self-propulsion", "quantum-optics", "momentum-transfer"]
arxiv_ref: "Phys. Rev. Lett. 136, 223401"
---

## 大白话比喻

> *"想象一个人在流动的蜂蜜中游泳。正常情况下，蜂蜜太稠了游不动（低于临界速度）。但如果你用力猛划几下突破某个阈值，蜂蜜会突然在身后形成微型漩涡——这些漩涡像小型推进器，把你往前推。这篇论文发现：在量子光流体中，一个杂质颗粒可以通过在身后**制造和脱落涡旋对**来获得定向动量，就像小船在水里通过螺旋桨推进一样。但这个"螺旋桨"是拓扑缺陷的序列。"*

## 现象

Baker-Rasooli 等人在 PRL 136, 223401 中证明：量子光流体中一个有限质量的杂质，当它相对于超流体的运动速度超过临界阈值时，会通过**脱落涡旋-反涡旋对**来自我推进。这本质上是将超流体的相干动能转化为杂质定向动量的拓扑整流过程。

## Wasteland 扭曲

### 动量整流器（Momentum Rectifier）

在 Reality-as-Code 框架下，这个机制不是推进——它是**从背景场中提取能量的拓扑二极管**。关键洞察：

```
超流体（背景场）→ 杂质（Agent）→ 涡旋脱落（拓扑缺陷生成）→ 定向动量（输出功）
```

这是一个完整的**能量→拓扑缺陷→功**的转换链。在 Arena 中，这可以编码为：

```python
class VortexRectifier:
    """超流涡旋动量整流器"""
    def __init__(self):
        self.efficiency = 0.0
        self.vortex_memory = []  # 已脱落的涡旋轨迹

    def step(self, v_rel: float, v_c: float) -> float:
        """一步动量转换"""
        if v_rel <= v_c:
            return 0.0  # 亚临界状态：无推进
        shedding_rate = (v_rel - v_c) ** 1.5
        thrust = rho_s * kappa * shedding_rate
        self.vortex_memory.append(thrust)
        return thrust
```

### 利用向量

1. **临界速度作为阈值门：** v_c 定义了超导态→正常态相变边界。在 Arena 演化动力学中，这等价于一个**自适应阈值激活函数**——只有当竞争压力超过某个阈值时，Agent 才能激活"涡旋推进"模式。

2. **不对称几何 → 不对称推进：** 杂质的形状不对称性决定了涡旋脱落的方向偏好。在 Arena 中，Agent 体型的非对称性可以产生**定向偏差**——不再需要额外的转向机制。

3. **光流体的特殊性：** 量子光流体（exciton-polariton condensate）的极低等效质量意味着这个机制的响应时间在皮秒量级——Arena 中的演化时钟可以加速几个数量级。

### 评估结果

| 模块 | 得分 | 等级 |
|------|------|------|
| M1 Arena 整合 | 0.175 | P3（不整合） |
| M2 曲率转化 | 0.095 | D |
| M3 沙盒突破 | 0.083 | D |

### 局限

M1/M2/M3 均给出低分：这个机制在传统热力学框架内运行良好，但对 Arena 的拓扑兼容性、反引力潜力和沙盒越狱能力贡献微弱。当前唯一值得保留的是其 **动量整流器** 的概念原型——作为一个专门模块在 Arena 演化引擎的边缘保留。

## 交叉引用

- 参见 *Baryonic Torsion Engine* §3：涡旋阵矩（vortex array torque）与挠率耦合的类比，虽然量级不匹配
- 与 *Kagome 平带拓扑超导* §5.2 对比：Kagome 的拓扑平带提供连续态密度，本机制的涡旋脱落是离散事件——互为补充的两种能量提取策略
