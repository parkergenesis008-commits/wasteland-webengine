---
title: "PBH视界晶格与小红点异常"
date: "2026-06-14"
tags:
  - primordial-black-hole
  - horizon-lattice
  - little-red-dots
  - baryonic-torsion
  - super-eddington
  - fractal-foam
arxiv_ref: "Phys. Rev. Lett. 136, 231402 (2026)"
---

## 大白话比喻

> *"这就好比宇宙早期撒了一把'微型黑洞种子'，这些种子像癌细胞一样疯狂吞噬周围物质，在短短几亿年内长成超大质量黑洞。JWST看到的那些诡异的'小红点'，就是这些黑洞还在狼吞虎咽时的婴儿照——而标准模型告诉我们，它们根本不应该长这么快。"*

更精确地说：想象在宇宙大爆炸后的汤里，某些区域的密度刚好足够高，直接坍缩成微型黑洞(10⁴-10⁶倍太阳质量)。这些微小黑洞就像引力锚点，吸引暗物质晕中的气体，以超过爱丁顿极限数倍的速度疯狂吸积——相当于一个人每分钟吃掉自己体重100倍的食物。结果就是，原本需要10亿年才能长大的超大质量黑洞，在不到5亿年内就成熟了。

## Phenomenon

**Primordial Black Hole (PBH) Seeded Supermassive Black Hole (SMBH) Growth**

JWST's observation of "Little Red Dots" (LRDs) at redshift z~5-7 revealed a population of compact, high-redshift sources hosting supermassive black holes that are significantly overmassive relative to their host stellar mass. These objects violate standard SMBH formation models, which require stellar-mass seeds (~100 M☉) to grow via Eddington-limited accretion over >1 Gyr.

The PBH pathway proposed by De Luca et al. (2026) resolves this tension through three coupled mechanisms:

1. **PBH Formation in Radiation Era**: Density fluctuations in the early universe produce PBHs with initial masses ~10⁴-10⁶ M☉, bypassing the stellar-seed bottleneck.
2. **Hierarchical PBH Clustering**: PBHs form binaries within dark matter minihalos, merging to produce intermediate-mass seeds before gas accretion begins.
3. **Super-Eddington Accretion**: In dense pre-galactic environments, PBHs accrete at f_Edd ~ 1-10× the Eddington rate, achieving exponential mass growth: M(t) = M_0 · exp(f_Edd · (1-ε)/ε · t/t_Sal).

The mass function follows dn/dM ∝ M^(-α) with α~1.5-2.5, peaking at M_PBH,initial ~ 10⁵ M☉. After ~500 Myr of super-Eddington accretion, these PBHs reach M_SMBH ~ 10⁷-10⁹ M☉, matching the JWST LRD observations.

## Wasteland Twist

**The Horizon Lattice: A Fractal Foam of Gravitational Symmetry-Breaking**

Each PBH event horizon encodes ~10⁷⁶-10⁸⁰ bits of Bekenstein-Hawking entropy — not as passive information storage, but as *active topological defects* in the spacetime fabric. The PBH population forms a **fractal hierarchical horizon lattice** where:

- **Each PBH acts as a curvature attractor** — akin to a topological defect frozen in during inflation, a permanent scar in the metric
- **Hierarchical merging creates nonlinear coupling** — the merger rate of PBH binaries follows M_dot_merge ∝ f_PBH^(53/21) × M^(-32/37), creating scale-invariant entanglement between horizon surfaces
- **Super-Eddington accretion as runtime parameter injection** — mass growth scales as M(t) ~ M_0 · exp(Γ·t), the exponential growth factor Γ = f_Edd·(1-ε)/ε·t_Sal^(-1) is a *controllable gain parameter*

**Why this is an exploit:**

In the Baryonic Torsion / Reality-as-Code framework, event horizons are not event horizons — they are **segfault boundaries** where the simulation's renderer hits a divide-by-zero in the metric tensor. A PBH horizon lattice is a *distributed array of pre-existing segfault points*, connected through hierarchical merger chains that act as **IPC (Inter-Process Communication) channels between sandbox layers**.

The super-Eddington parameter Γ is the critical lever: it represents the rate at which a PBH can "overwrite" its mass parameter faster than the simulation's error-correction can stabilize. At f_Edd > 1, the accretion gain exceeds the Eddington-limit error-correction bandwidth — equivalent to a **hotpatch injection that outruns the sandbox's built-in rollback**.

## Evaluation Results

### M1 — Arena Feasibility (0.155, P3)
| Axis | Score | Assessment |
|------|-------|------------|
| Computability | 0.00 | Low — requires heavy abstraction |
| Parameterizability | **0.90** | 6-dimensional parameter space (M_PBH, f_Edd, α, ε, f_PBH, f_merge) |
| Competitive Asymmetry | 0.00 | Close to zero-sum |
| Topological Compatibility | 0.00 | Requires new architectural layer |
| Anti-Gravity Potential | 0.00 | No direct curvature-spacetime link |
| Empirical Anchoring | 0.20 | PRL-published, but no lab validation |

### M2 — Topology → Curvature (0.095, Grade D)
- Lattice classified as **Kagome** (engine artifact — fractal foam overpowered by condensed-matter defaults)
- Berry curvature dipole D_ab = 10.0 Å
- Spin current J_s = 6.24×10¹⁴ A/m²
- Metric perturbation δg = 4.80×10⁻¹⁴⁶ (1.0×10⁹⁴× below engineering threshold)
- **Bottleneck**: N² amplification requires N_critical ≈ 10⁵³ synchronous nodes

### M3 — Sandbox Exploit (0.042, Grade D)
- Dominant channel: Hotpatch Injection (D, 0.167)
- All other channels: 0.0
- Assessment: "完全在沙盒物理规则内运作"

## Cross-References

- *Baryonic Torsion Compression Engine*, §3 — horizon lattice as torsion coupling surface
- *Kagome Flat-Band Topological Superconductivity*, §2 — Berry curvature dipole comparison
- *Primordial Black Hole Accretion Dynamics* — Super-Eddington gain parameter Γ
- *Reality-as-Code: Simulation Architecture*, §7 — segfault boundaries and sandbox IPC
