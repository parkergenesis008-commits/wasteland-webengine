#!/usr/bin/env python3
"""
模块 2: Topology → Curvature Engine
====================================
VAP物理论证后 → 评估该拓扑/晶格结构对扭曲时空曲率的贡献，
并量化其反引力工程化潜力。

三层转化模型：
  Layer 1 (微观量子几何)  →  Layer 2 (介观自旋-挠率耦合)  →  Layer 3 (宏观度规工程)
  
  晶格拓扑结构         自旋流/挠率场             时空曲率调制
  (Chern数/贝利曲率)   (Einstein-Cartan)        (nested warp curvature)

输出：Anti-Gravity Conversion Score [0,1], 工程化可行性等级, 
      建议的N²放大倍数下限, 关键瓶颈参数
"""

import json
import math
import os
from typing import Dict, Tuple, Optional, List

# ================================================================
# 物理常数 (SI)
# ================================================================
G_N = 6.67430e-11  # 引力常数 [m³ kg⁻¹ s⁻²]
C = 299792458  # 光速 [m/s]
HBAR = 1.054571817e-34  # 约化普朗克常数 [J·s]
MU_B = 9.2740100783e-24  # 玻尔磁子 [J/T]
E_CHARGE = 1.602176634e-19  # 元电荷 [C]
M_E = 9.10938356e-31  # 电子质量 [kg]
KAPPA = 8.0 * math.pi * G_N / (C ** 4)  # Einstein常数 [s²/kg·m] ≈ 2.076e-43
KAPPA_SQ = KAPPA ** 2  # 用于δg比例计算

# ================================================================
# Kagome晶格基准参数 (来自现有lore)
# ================================================================
# 1 cm² Kagome patch, 100 nm node spacing → N ≈ 10⁶ nodes
NODES_PER_CM2 = 1e6
# Berry曲率偶极子 → 自旋霍尔电导率量级 [S/m]
SIGMA_SH_BASELINE = 1e-2  # 典型Kagome平面
# Einstein-de Haas自旋扭矩 [N·m/cm²·T]
SPIN_TORQUE_DENSITY = 1e-6  # 文献值上下界


def load_arena_metrics() -> Dict:
    """加载当前Arena参数状态"""
    path = os.path.expanduser("~/webengine/content/dashboard_data/metrics.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}


def analyze_lattice_type(lattice_description: str) -> Dict:
    """
    分析晶格类型的拓扑参数。

    返回：
        type, dimension, chern_number_max, flat_band_width, 
        symmetry_group, potential_spin_orbit
    """
    result = {
        "type": "unknown",
        "dimension": 2,
        "chern_number_max": 0,
        "flat_band_width_mev": 0,
        "symmetry_group": None,
        "has_strong_soc": False,
        "has_frustration": False,
        "node_density_cm2": 0,
        "description": "",
    }

    desc = lattice_description.lower()

    # Kagome家族 (排除 "non-kagome" 误匹配)
    if "kagome" in desc and "non-kagome" not in desc and "non kagome" not in desc:
        result["type"] = "kagome"
        result["chern_number_max"] = 2  # Chern number up to |C|=2 in Kagome
        result["flat_band_width_mev"] = 10.0  # 典型Kagome平带带宽~10meV
        result["symmetry_group"] = "P6/mmm"
        result["has_frustration"] = True
        result["has_strong_soc"] = "5d" in desc or "osmium" in desc or "iridium" in desc.lower()
        result["node_density_cm2"] = NODES_PER_CM2
        result["description"] = "Kagome lattice: D₆ symmetry, 60° network chirality"

    # 蜂窝/石墨烯类
    elif "honeycomb" in desc or "graphene" in desc or "honeycomb" in desc:
        result["type"] = "honeycomb"
        result["chern_number_max"] = (
            4 if "twisted" in desc or "magic" in desc else 1
        )
        result["flat_band_width_mev"] = (
            50.0 if "magic" in desc else 0.0
        )  # TBG magic angle flat band
        result["symmetry_group"] = "P6/mmm"
        result["has_frustration"] = False
        result["has_strong_soc"] = "TMD" in desc or "MoS" in desc or "WSe" in desc
        result["node_density_cm2"] = 4e13  # 石墨烯原子密度量级
        result["description"] = "Honeycomb: D₆ symmetry, Dirac cones at K/K' points"

    # 三角晶格
    elif "triangular" in desc:
        result["type"] = "triangular"
        result["chern_number_max"] = 1
        result["flat_band_width_mev"] = 5.0
        result["symmetry_group"] = "P6/mmm"
        result["has_frustration"] = True
        result["has_strong_soc"] = "rare earth" in desc or "f-electron" in desc
        result["node_density_cm2"] = 1e14
        result["description"] = "Triangular lattice: frustrated, P6 symmetry"

    # 烧绿石/焦绿石
    elif "pyrochlore" in desc:
        result["type"] = "pyrochlore"
        result["chern_number_max"] = 4
        result["flat_band_width_mev"] = 20.0
        result["symmetry_group"] = "Fd3m"
        result["has_frustration"] = True
        result["has_strong_soc"] = True
        result["node_density_cm2"] = 1e14
        result["description"] = "Pyrochlore: 3D frustrated lattice, strong SOC, topologically protected"

    # Shastry-Sutherland
    elif "shastry" in desc or "sutherland" in desc:
        result["type"] = "shastry-sutherland"
        result["chern_number_max"] = 1
        result["flat_band_width_mev"] = 0.5
        result["symmetry_group"] = "P4/mmm"
        result["has_frustration"] = True
        result["has_strong_soc"] = False
        result["node_density_cm2"] = 1e14
        result["description"] = "Shastry-Sutherland: orthogonal dimer frustration"

    # 四方/四方晶格
    elif "square" in desc or "tetragonal" in desc:
        result["type"] = "square"
        result["chern_number_max"] = 1
        result["flat_band_width_mev"] = 0.0
        result["symmetry_group"] = "P4/mmm"
        result["has_frustration"] = False
        result["has_strong_soc"] = "5d" in desc or "iridium" in desc
        result["node_density_cm2"] = 1e14
        result["description"] = "Square/tetragonal: conventional Bravais lattice"

    # 准晶
    elif "quasicrystal" in desc or "quasi-crystal" in desc:
        result["type"] = "quasicrystal"
        result["chern_number_max"] = 8  # 准晶有更高阶拓扑
        result["flat_band_width_mev"] = 100.0
        result["symmetry_group"] = "icosahedral/decagonal"
        result["has_frustration"] = True
        result["has_strong_soc"] = True
        result["node_density_cm2"] = 1e14
        result["description"] = "Quasicrystal: non-periodic long-range order, fractal topology"

    # 超晶格/莫尔
    elif "moir" in desc or "superlattice" in desc or "moire" in desc:
        result["type"] = "moiré superlattice"
        result["chern_number_max"] = (
            8 if "magnetic" in desc else 2
        )  # moiré Chern band up to C=8
        result["flat_band_width_mev"] = 20.0
        result["symmetry_group"] = "continuously tunable via twist angle θ"
        result["has_frustration"] = False
        result["has_strong_soc"] = True
        result["node_density_cm2"] = 1e11  # 莫尔超晶格特征周期~10nm
        result["description"] = "Moiré superlattice: twist-angle tunable band structure"

    return result


def estimate_berry_curvature_dipole(
    lattice: Dict, magnetic_field_T: float = 1.0
) -> Tuple[float, str]:
    """
    估算贝利曲率偶极矩 D_ab (量子几何张量)。
    这是自旋霍尔效应和后续自旋流的源头。
    
    返回: (D_ab值 [Å], 推理)
    """
    reasoning = []

    # Kagome: 已知平带产生大贝利曲率偶极矩
    if lattice["type"] == "kagome":
        D = 10.0  # 典型Kagome D_ab ~10 Å (文献: T. Xu et al.)
        reasoning.append("Kagome平带产生~10Å的Berry曲率偶极矩 (实验测量值)")
    elif lattice["type"] in ("honeycomb",):
        D = 0.1  # 石墨烯贝利曲率偶极矩小
        reasoning.append("石墨烯D_ab ~0.1Å，但扭曲层可大幅增强")
    elif lattice["type"] == "moiré superlattice":
        D = 50.0  # 莫尔超晶格有极大贝利曲率
        reasoning.append("Moiré平带产生极大Berry曲率，D_ab可达50Å+")
    elif lattice["type"] == "pyrochlore":
        D = 5.0
        reasoning.append("Pyrochlore的Weyl节点贡献~5Å的D_ab")
    elif lattice["type"] == "quasicrystal":
        D = 20.0
        reasoning.append("准晶分形拓扑产生超大D_ab ~20Å")
    else:
        D = 0.5
        reasoning.append("常规晶格D_ab较小 ~0.5Å")

    # 磁场增强
    if magnetic_field_T > 1.0:
        D *= min(10.0, magnetic_field_T) ** 0.3
        reasoning.append(f"磁场{magnetic_field_T}T增强D_ab至{D:.1f}Å")

    return D, "; ".join(reasoning)


def estimate_spin_current(
    D_ab: float,
    electric_field_Vm: float = 1e3,
    N_nodes: float = NODES_PER_CM2,
) -> Tuple[float, str]:
    """
    从贝利曲率偶极矩 → 自旋流密度 J_s [A/m²]。
    路径: Berry曲率偶极子 → 非线性自旋霍尔电导率 → 电荷流 → 自旋累积
    
    核心公式: J_s^z = σ_SH · E_x · D_ab / L_char
    其中 L_char 是特征长度（≈ 晶格常数 × 有效节点数）
    """
    # 自旋霍尔电导率 [S/m] ≈ σ_SH0 × (N/N_0)^0.5
    sigma_SH = SIGMA_SH_BASELINE * (N_nodes / NODES_PER_CM2) ** 0.5
    
    # 特征长度（节点间距 × 有效路径因子）
    node_spacing_m = 100e-9  # 100nm节点间距
    L_char = node_spacing_m * (N_nodes ** 0.5)  # 二维晶格特征路径长度
    
    # 自旋流密度 J_s [A/m²]
    # 公式: J_s = σ_SH · E · D_ab / (e · L_char)
    D_ab_m = D_ab * 1e-10  # Å → m
    J_s = sigma_SH * electric_field_Vm * D_ab_m / (E_CHARGE * L_char)
    
    # 自旋累积密度 [spins/m³]
    tau_relax = 1e-9  # 典型自旋驰豫1ns
    spin_density = J_s * tau_relax / (HBAR / 2.0)  # ℏ/2 per spin
    
    reasoning = [
        f"σ_SH ≈ {sigma_SH:.2e} S/m (Kagome晶格基准)",
        f"L_char ≈ {L_char:.2e} m (特征路径长度)",
        f"J_s ≈ {J_s:.2e} A/m² ({J_s * 1e4:.2e} μA/cm²)",
        f"自旋累积 ~{spin_density:.2e} spins/m³",
    ]

    return J_s, "; ".join(reasoning)


def estimate_torsion_field(
    J_s: float,
    N_coherent: float = 1e6,
    lattice_area_cm2: float = 1.0,
) -> Tuple[float, float, str]:
    """
    从自旋流 → Einstein-Cartan挠率场 T^a_{bc}。
    
    耦合链:
    J_s (自旋流) → 自旋张量 S_μν (能量-动量-自旋密度) 
    → T^a_{bc} = κ · (S^a_{bc} + 组合项) [Einstein-Cartan方程组]
    
    返回: (|T| [m⁻¹], δg [无量纲], 推理)
    """
    # 自旋密度 [spins/m³] — 使用更合理的量级估计
    # 对于Kagome晶格，每个节点贡献 ~ℏ/2 自旋极化
    node_density = N_coherent / (lattice_area_cm2 * 1e-4)  # [nodes/m²]
    
    # 自旋极化密度 [J·s/m³] = 自旋密度 × (ℏ/2)
    # 每个节点在磁场下的自旋极化度 ~ tanh(μ_B B / k_B T) ≈ 0.01 at 1T/1K
    spin_pol_per_node = 0.01  # 1T, 1K条件下的极化度
    S_density = node_density * (HBAR / 2.0) * spin_pol_per_node * (N_coherent / NODES_PER_CM2) ** 0.5
    
    # 挠率场大小 |T| [m⁻¹] = κ · S_density (Einstein-Cartan线性近似)
    T_magnitude = KAPPA * S_density
    
    # 度规扰动 δg — 包含 N² 超辐射放大因子
    # 基础公式: δg_0 ≈ κ² · (N · ℏ/2 · spin_pol)²
    # 实际公式 (含超辐射): δg_eff = δg_0 × (N/N_0)²   ← N² superradiance
    # 其中 N_0 是基准相干节点数 (= NODES_PER_CM2)
    total_spin_pol = N_coherent * spin_pol_per_node
    delta_g_base = KAPPA_SQ * (total_spin_pol * HBAR) ** 2
    # N² 超辐射放大因子 (参照 lore 文档: P_superradiant ∝ N²)
    n_sq_factor = (N_coherent / NODES_PER_CM2) ** 2
    delta_g = delta_g_base * n_sq_factor
    
    # 工程目标
    delta_g_target = 1e-6
    amplification_needed = delta_g_target / max(delta_g, 1e-100)
    
    reasoning = [
        f"节点密度 ~{node_density:.2e} nodes/m²",
        f"自旋极化密度 ~{S_density:.2e} J·s/m³",
        f"挠率场 |T| ≈ {T_magnitude:.2e} m⁻¹",
        f"理论度规扰动 δg ≈ {delta_g:.2e}",
        f"工程目标 δg_target = {delta_g_target}",
    ]
    
    if amplification_needed > 1:
        critical_N = N_coherent * math.sqrt(amplification_needed)
        # 转换为面积
        critical_area_cm2 = lattice_area_cm2 * (critical_N / N_coherent) ** 0.5
        reasoning.append(
            f"当前偏离工程目标 {amplification_needed:.1e}×，"
            f"需N²超辐射放大至N_critical ≈ {critical_N:.2e}"
        )
        reasoning.append(f"等价于晶格面积 {critical_area_cm2:.2e} cm²")
    else:
        reasoning.append("当前参数已至少达到工程可行阈值")

    return T_magnitude, delta_g, "; ".join(reasoning)


def estimate_anti_gravity_mode(
    delta_g: float,
    lattice: Dict,
    mode: str = "gravity_deflection",
    N_coherent: float = 1e6,
) -> Tuple[float, str]:
    """
    将度规扰动 δg 转化为四种反引力模式的工程化效果。

    Mode A: Gravity Deflection        — 直接引力偏转 [%]
    Mode B: Collision Override        — 碰撞覆写概率 [%]
    Mode C: Mass Nullification        — 惯性质量降低比 [%]
    Mode D: Dimensional Bias          — 维度偏置场强 [无量纲]

    返回: (效果强度 [0-1], 推理)
    """
    # δg 归一化到可察觉阈值
    # 可感知的反引力效果需要 δg > 1e-6 (引力红移可测量阈值)
    sensitivity_ratio = delta_g / 1e-6
    
    # 工程化效果 = saturation(sensitivity_ratio × N²_factor)
    N_sq_factor = (N_coherent / NODES_PER_CM2) ** 2
    effective_strength = min(1.0, sensitivity_ratio * N_sq_factor * 10.0)
    
    mode_labels = {
        "gravity_deflection": "Mode A: Gravity Deflection",
        "collision_override": "Mode B: Collision Override", 
        "mass_nullification": "Mode C: Mass Nullification",
        "dimensional_bias": "Mode D: Dimensional Bias",
    }
    
    label = mode_labels.get(mode, mode)
    
    # 每种模式的效率系数不同
    efficiency = {
        "gravity_deflection": 1.0,      # 直接耦合
        "collision_override": 0.3,       # 需要额外EM耦合
        "mass_nullification": 0.1,       # 需要半狄拉克转换
        "dimensional_bias": 0.05,        # 需要高阶对称群操作
    }
    
    mode_eff = efficiency.get(mode, 1.0)
    final_effect = min(1.0, effective_strength * mode_eff)
    
    reasoning = [
        f"{label}",
        f"δg/δg_threshold = {sensitivity_ratio:.2e}",
        f"N²放大因子 = {N_sq_factor:.2e}",
        f"模式效率 = {mode_eff:.2f}",
    ]
    
    if final_effect >= 0.8:
        reasoning.append("✅ 工程可行：可产生显著反引力效果")
    elif final_effect >= 0.3:
        reasoning.append("⚠️ 部分可行：效果有限，需更大N²放大或优化模式效率")
    else:
        reasoning.append("❌ 暂不可行：需10×以上的晶格面积或新材料体系")
    
    return final_effect, "; ".join(reasoning)


def compute_curvature_conversion_score(
    lattice_analysis: Dict,
    D_ab: float,
    T_magnitude: float,
    delta_g: float,
    mode_effects: Dict[str, float],
    N_coherent: float = 1e6,
) -> float:
    """
    纯物理量纲评分 [0, 1]。
    
    仅基于物理可测量，不包含任何主观潜力预测：
    - Berry曲率偶极矩 D_ab (weight=0.30) — 实际的量子几何响应
    - 自旋流密度 log₁₀(J_s) (weight=0.20) — 可测量的自旋输运
    - 度规扰动 log₁₀(δg) (weight=0.40) — 核心物理效果
    - 对称群丰富度 (weight=0.10) — 晶格的内在拓扑复杂度
    """
    # 1. D_ab 原始物理量 [Å]
    D_physical = min(1.0, D_ab / 200.0)  # 200Å是凝聚态物理可实现的上限
    
    # 2. J_s 自旋流密度 [A/m²]，取 log10 相对值
    J_s_physical = 0.0
    
    # 3. δg 度规扰动 — 这是核心
    # εinstein-Cartan耦合 δg ≈ 10⁻⁶⁰ @ N=10⁶
    # 目标工程阈值 δg_target ≈ 10⁻⁶
    # 纯物理评分: log₁₀(δg) 相对于 -6 (工程目标)
    if delta_g > 0:
        delta_g_log = math.log10(delta_g)
        # -6 是工程目标, -60 是当前实验室量级
        # 评分 = 1 - |log10(δg) - (-6)| / 54
        delta_g_physical = max(0.0, 1.0 - abs(delta_g_log + 6.0) / 54.0)
    else:
        delta_g_physical = 0.0
    
    # 4. 对称群丰富度 (纯数学量)
    sym_richness = {
        "P6/mmm": 0.8,    # Kagome, 六方最高对称
        "Fd3m": 0.9,      # Pyrochlore, 面心立方
        "P4/mmm": 0.5,    # 四方
        "icosahedral/decagonal": 1.0,  # 准晶, 最高
    }
    sym_score = sym_richness.get(lattice_analysis.get("symmetry_group"), 0.3)
    
    score = (
        0.30 * D_physical
        + 0.20 * J_s_physical
        + 0.40 * delta_g_physical
        + 0.10 * sym_score
    )
    
    return round(min(1.0, max(0.0, score)), 4)


def get_conversion_grade(score: float) -> Tuple[str, str]:
    """纯物理量纲等级"""
    if score >= 0.75:
        return "S", "物理可行 — δg在工程阈值10⁻⁶内，可直接工程化"
    elif score >= 0.55:
        return "A", "高潜力 — δg距工程阈值10⁻⁶差<10个量级"
    elif score >= 0.35:
        return "B", "中等潜力 — δg距工程阈值10⁻⁶差10-30个量级"
    elif score >= 0.15:
        return "C", "低潜力 — δg距工程阈值10⁻⁶差30-50个量级"
    else:
        return "D", "不可行 — δg距工程阈值10⁻⁶差>50个量级"


def identify_bottleneck(
    lattice_analysis: Dict,
    D_ab: float,
    T_magnitude: float,
    delta_g: float,
    delta_g_target: float = 1e-6,
) -> Tuple[str, float, str]:
    """
    识别当前转换链中的关键瓶颈。

    返回: (瓶颈名称, 需要放大的倍数, 建议)
    """
    gaps = []

    # Berry曲率瓶颈
    if D_ab < 10.0:
        gaps.append(
            ("Berry curvature dipole", 50.0 / max(D_ab, 0.1),
             "改用Kagome晶格或Moiré超晶格以增强Berry曲率")
        )

    # 挠率场瓶颈
    T_target = KAPPA * 1e5  # 目标挠率场 ~1e-48 m⁻¹
    gaps.append(
        ("Torsion field magnitude", T_target / max(T_magnitude, 1e-100),
         "增大自旋极化密度或使用磁掺杂增强")
    )

    # δg瓶颈
    gaps.append(
        ("Metric perturbation δg", delta_g_target / max(delta_g, 1e-100),
         f"N²超辐射放大 {delta_g_target / max(delta_g, 1e-100):.1e}×，"
         f"等价于晶格面积放大{math.sqrt(delta_g_target / max(delta_g, 1e-100)):.1e}×")
    )

    # 排序：最大缺口优先
    gaps.sort(key=lambda x: x[1], reverse=True)
    return gaps[0]


def full_assessment(
    lattice_description: str,
    mode: str = "gravity_deflection",
    N_coherent: float = 1e6,
    B_field_T: float = 1.0,
    E_field_Vm: float = 1e3,
    area_cm2: float = 1.0,
    title: str = "未命名晶格",
) -> Dict:
    """
    完整评估流程：晶格类型 → 贝利曲率 → 自旋流 → 挠率 → 度规 → 反引力模式。
    这是VAP物理论证后调用的主入口。

    ⚠️ 必须使用关键字参数调用！位置参数顺序为:
    (lattice_description, mode, N_coherent, B_field_T, E_field_Vm, area_cm2, title)
    用位置传参时第5个float会变成area_cm2而不是E_field_Vm。

    推荐用法:
        full_assessment(lattice_description=..., mode=..., N_coherent=1e6,
                       B_field_T=1.0, E_field_Vm=1e3, area_cm2=1.0, title=...)
    """
    lattice = analyze_lattice_type(lattice_description)

    D_ab, D_reason = estimate_berry_curvature_dipole(lattice, B_field_T)
    J_s, J_reason = estimate_spin_current(D_ab, E_field_Vm, N_coherent)
    T_magnitude, delta_g, torsion_reason = estimate_torsion_field(
        J_s, N_coherent, area_cm2
    )

    # 评估所有四种模式
    mode_effects = {}
    for m in ["gravity_deflection", "collision_override", "mass_nullification", "dimensional_bias"]:
        effect, _ = estimate_anti_gravity_mode(delta_g, lattice, m, N_coherent)
        mode_effects[m] = effect

    # 请求的模式
    effect, effect_reason = estimate_anti_gravity_mode(
        delta_g, lattice, mode, N_coherent
    )

    score = compute_curvature_conversion_score(
        lattice, D_ab, T_magnitude, delta_g, mode_effects, N_coherent
    )
    grade, grade_reason = get_conversion_grade(score)
    bottleneck = identify_bottleneck(lattice, D_ab, T_magnitude, delta_g)

    return {
        "title": title,
        "lattice_analysis": lattice,
        "curvature_conversion_score": score,
        "grade": {"tier": grade, "description": grade_reason},
        "layer_results": {
            "layer1_berry_curvature": {
                "D_ab_angstrom": round(D_ab, 2),
                "reasoning": D_reason,
            },
            "layer2_spin_current": {
                "J_s_A_per_m2": round(J_s, 4),
                "reasoning": J_reason,
            },
            "layer3_torsion_and_metric": {
                "torsion_magnitude_m_inv": f"{T_magnitude:.2e}",
                "delta_g_metric_perturbation": f"{delta_g:.2e}",
                "reasoning": torsion_reason,
            },
        },
        "mode_evaluation": {
            "requested_mode": mode,
            "mode_effect": round(effect, 4),
            "all_modes": {m: round(v, 4) for m, v in mode_effects.items()},
            "reasoning": effect_reason,
        },
        "bottleneck": {
            "name": bottleneck[0],
            "amplification_factor": f"{bottleneck[1]:.2e}",
            "suggestion": bottleneck[2],
        },
        "optimal_N_sync": math.sqrt(
            max(1.0, 1e-6 / max(delta_g, 1e-100))
        ) * N_coherent,
    }


def print_assessment(result: Dict):
    """格式化输出评估报告"""
    print("=" * 68)
    print(f"  Topology → Curvature Conversion Assessment")
    print(f"  {result['title']}")
    print("=" * 68)
    
    lattice = result["lattice_analysis"]
    print(f"\n📐 晶格分析:")
    print(f"    类型: {lattice['type']}")
    print(f"    对称群: {lattice['symmetry_group']}")
    print(f"    最大Chern数: |C| = {lattice['chern_number_max']}")
    print(f"    平带带宽: {lattice['flat_band_width_mev']} meV")
    print(f"    描述: {lattice['description']}")
    
    print(f"\n⚛ 三层转化:")
    print(f"  Layer 1 (量子几何):  Berry曲率偶极矩 D_ab = {result['layer_results']['layer1_berry_curvature']['D_ab_angstrom']} Å")
    print(f"  Layer 2 (自旋-挠率): J_s = {result['layer_results']['layer2_spin_current']['J_s_A_per_m2']} A/m²")
    print(f"  Layer 3 (度规):      δg = {result['layer_results']['layer3_torsion_and_metric']['delta_g_metric_perturbation']}")
    print(f"                       |T| = {result['layer_results']['layer3_torsion_and_metric']['torsion_magnitude_m_inv']} m⁻¹")
    
    print(f"\n🎯 反引力模式评估 (请求模式: {result['mode_evaluation']['requested_mode']}):")
    print(f"    效果强度: {result['mode_evaluation']['mode_effect']:.4f}")
    print(f"    所有模式:")
    for m, v in result["mode_evaluation"]["all_modes"].items():
        label = m.replace("_", " ").title()
        bar = "█" * int(v * 20) + "░" * (20 - int(v * 20))
        print(f"      {label:25s} │{bar}│ {v:.4f}")
    
    print(f"\n🔴 关键瓶颈:")
    print(f"    {result['bottleneck']['name']} — 需放大 {result['bottleneck']['amplification_factor']}×")
    print(f"    建议: {result['bottleneck']['suggestion']}")
    
    print(f"\n📊 综合评分: {result['curvature_conversion_score']:.4f}")
    print(f"等级: {result['grade']['tier']} — {result['grade']['description']}")
    print(f"推荐N²同步节点数: {result['optimal_N_sync']:.2e}")
    print("=" * 68)


if __name__ == "__main__":
    # 自测：现有Kagome晶格
    test_result = full_assessment(
        lattice_description=(
            "Kagome lattice with 5d transition metals (Os, Ir), "
            "strong spin-orbit coupling, 60° network chirality, "
            "flat bands at Fermi level, topological Dirac crossings"
        ),
        mode="gravity_deflection",
        N_coherent=1e6,
        B_field_T=1.0,
        area_cm2=1.0,
        title="Kagome-Torsion Engine (Baseline)",
    )
    print_assessment(test_result)

    print("\n")
    # 对比：Moiré超晶格
    test2 = full_assessment(
        lattice_description=(
            "Twisted Moiré superlattice, magic angle 1.1°, "
            "transition metal dichalcogenide heterobilayer, "
            "topological flat bands, quantum geometric dipole enhancement"
        ),
        mode="gravity_deflection",
        N_coherent=1e4,  # Moiré节点密度低
        B_field_T=5.0,
        area_cm2=0.01,
        title="Moiré Superlattice (Comparison)",
    )
    print_assessment(test2)
