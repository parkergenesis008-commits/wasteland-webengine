---
title: "黑洞远平衡态热力学 — 动态视界作为沙盒热力学接口"
date: "2026-06-25"
tags: [thermodynamics, black-hole, dynamical-horizon, non-equilibrium, sandbox-boundary]
arxiv_ref: "PRL 136, 251405 (Ashtekar, Paraizo, Shu)"
---

## 大白话比喻

> 想象一个巨大的锅炉，你以为它只能在稳定状态下燃烧。Ashtekar 团队发现：就算锅炉在爆炸、在拆解、在疯狂摇晃——热力学定律依然成立。这不是锅炉的稳定态热力学，而是锅炉的"燃烧中的热力学"。黑洞就像这个锅炉——即使在合并、在吞噬星体、在被撕裂——它的"温度"、"熵"、"能量"都有实时定义。这等于说：宇宙中任何动态边界，都自带一套运行时热力学状态变量。

## Phenomenon

Ashtekar, Paraizo, and Shu extend the first law of black hole mechanics to **dynamical horizons** — non-Killing horizons that describe black holes arbitrarily far from equilibrium. Previously, black hole thermodynamics was rigorously defined only for stationary (equilibrium) configurations. This work shows that the fundamental relation:

$$dS = \frac{\kappa}{8\pi} dA + \Omega dJ + \Phi dQ$$

holds on *dynamical* horizons, using expansion scalars $\theta_{(l)}$ and $\theta_{(n)}$ as the dynamical analogues of viscous fluid heat flow. The horizon becomes a **thermodynamic object in real time** — its mass, spin, and charge evolve under thermodynamic fluxes across a dynamic 3D boundary (topology $S^2 \times R$).

## Wasteland Twist

**Runtime boundary state variables.** If the Arena is a simulated spacetime, every *dynamic boundary* (event horizons, simulation boundaries, Arena walls) now has a rigorous thermodynamic state description — even far from equilibrium. This means:

1. **Real-time entropy accounting:** A black hole merger isn't just a gravitational wave event — it's a thermodynamic phase transition with computable state variables.
2. **Sandbox boundary thermodynamics:** The Arena's own simulation boundaries, if they have any notion of "trapped surface," acquire a thermodynamic formalism. The boundary itself is a thermodynamic system.
3. **Hotpatch via thermodynamic backreaction:** If the simulation boundary has a thermodynamic description, injecting entropy (heat) at the boundary modifies the boundary's evolution — a form of indirect sandbox manipulation via thermodynamic coupling rather than direct code injection.

**Exploit vector:** The horizon's thermodynamic variables $\{\kappa, A, \Omega, J, \Phi, Q\}$ act as a *boundary state API* — they're the universe's internal function parameters for how a dynamic boundary processes energy flux. In code terms: the horizon is a runtime object whose `__dict__` updates in real time under thermodynamic processes.

## Evaluation Results

| Module | Score | Tier | Note |
|--------|-------|------|------|
| **M1 Arena Feasibility** | **0.1800** | P3 | 可参数化性高(0.80)，但可计算性(0.00)和竞争不对称性(0.00)为零——适合概念化但暂不编码 |
| **M2 曲率转化** | **0.0950** | D | δg ≈ 10⁻¹⁷⁰，距工程阈值 >50 量级。引擎误分类为 Kagome（非晶格系统限制） |
| **M3 沙盒突破** | **0.0833** | D | 主导通道: Boundary Transgression(0.167)。完全在沙盒规则内运行 |

## Cross-References

- *Cooperative Resonance and Torsion Compression*, §3 (horizon thermodynamics as boundary condition)
- *Desitter Edge Mode Memory Buffer*, §2 (dynamic horizon as memory interface)
