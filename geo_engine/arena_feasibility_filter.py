#!/usr/bin/env python3
"""
模块 1: Arena Feasibility Filter
==================================
论文流入 → VAP物理论证后 → 评估该机制是否值得整合进Computational Arena。

评估维度（6轴打分）：
1. 可演算性 (Computability)   — 该机制能否编码为演化引擎的fitness函数？
2. 参数化程度 (Parameterizability) — 核心物理量是否可映射为连续可调参数？
3. 竞争不对称性 (Competitive Asymmetry) — 引入后是否产生非平凡优势策略？
4. 拓扑兼容性 (Topological Compatibility) — 与现有Kagome/EPR-Torsion架构的咬合度
5. 反引力潜力 (Anti-Gravity Potential) — 是否对扭曲曲率有直接贡献
6. 实验可行性 (Empirical Anchoring) — 是否有真实实验/arXiv论文支撑

输出: Arena Integration Score [0,1], 推荐优先级, 建议的fitness函数签名
"""

import json
import os
import sys
from typing import Dict, Tuple, Optional

# 权重矩阵 — Kagome/EPR-Torsion 架构下各维度的相对重要性
WEIGHTS = {
    "computability": 0.25,
    "parameterizability": 0.15,
    "competitive_asymmetry": 0.20,
    "topological_compatibility": 0.20,
    "anti_gravity_potential": 0.10,
    "empirical_anchoring": 0.10,
}

# 现有Arena的fitness函数签名模板库
FITNESS_TEMPLATES = {
    "kagome_chirality": "f(θ, κ, N_sync) → chirality_gradient / entropy_cost",
    "kondo_zero_mode": "f(E_0, Γ_pin, T) → 1 / (E_deviation + Γ_leakage)",
    "torsion_coupling": "f(J_s, N, δg) → metric_perturbation / energy_budget",
    "dirac_mass_null": "f(m_eff, v_F, ω_drive) → mass_override_ratio / inertia_cost",
    "floquet_coherence": "f(Ω, τ_decay, φ_noise) → drive_fidelity / decoherence_rate",
    "semi_dirac_anisotropy": "f(m_x, m_y, m_z, α) → anisotropic_gain / directional_loss",
}

ARENA_METRICS_PATH = os.path.expanduser(
    "~/webengine/content/dashboard_data/metrics.json"
)


def load_arena_metrics() -> Dict:
    """加载当前Arena演化参数状态"""
    if os.path.exists(ARENA_METRICS_PATH):
        with open(ARENA_METRICS_PATH, "r") as f:
            return json.load(f)
    return {}


def assess_computability(
    core_mechanism: str, mathematical_form: str
) -> Tuple[float, str]:
    """
    评估该机制的可演算性。

    评分依据：
    - 是否有清晰的数学形式（微分方程、张量、拓扑不变量）
    - 能否映射为标量fitness函数
    - 计算复杂度是否可接受（O(n²) vs O(n log n)）
    """
    score = 0.0
    reasoning = []

    # 关键词启发式
    computable_indicators = [
        "Hamiltonian",
        "topological invariant",
        "Chern number",
        "winding number",
        "Berry curvature",
        "order parameter",
        "free energy",
        "Landau",
        "Ginzburg",
        "mean field",
        "tight-binding",
        "effective model",
        "tensor",
        "spinor",
        "matrix",
        "eigenvalue",
        "coupling constant",
        "susceptibility",
        "conductivity",
    ]

    hit_count = sum(
        1 for ind in computable_indicators if ind.lower() in mathematical_form.lower()
    )
    score = min(1.0, hit_count / 6.0)

    if score >= 0.8:
        reasoning.append("高可演算性：数学形式明确，可直接映射为fitness函数")
    elif score >= 0.4:
        reasoning.append("中等可演算性：需简化或构建代理模型")
    else:
        reasoning.append("低可演算性：需大幅抽象，可能丢失物理保真度")

    return score, "; ".join(reasoning)


def assess_parameterizability(
    core_mechanism: str, parameters: Dict[str, float]
) -> Tuple[float, str]:
    """
    评估核心物理参数是否可作为Arena的演化参数。

    连续可调参数数量越多 → 演化空间越丰富但搜索复杂度越高。
    最优区间: 3-7个可调参数。
    """
    n_params = len(parameters)
    reasoning = []

    if n_params == 0:
        score = 0.0
        reasoning.append("无可调参数，无法演化")
    elif 1 <= n_params <= 2:
        score = 0.3
        reasoning.append("参数太少，演化自由度不足")
    elif 3 <= n_params <= 5:
        score = 0.8
        reasoning.append(f"参数数量{n_params}，演化空间理想")
    elif 6 <= n_params <= 8:
        score = 0.9
        reasoning.append(f"参数数量{n_params}，演化空间丰富")
    else:
        score = 0.4
        reasoning.append(f"参数数量{n_params}过多，需降维或正则化")

    return score, "; ".join(reasoning)


def assess_competitive_asymmetry(core_mechanism: str) -> Tuple[float, str]:
    """
    评估该机制是否产生非平凡的优势/劣势策略。
    最好的机制产生"剪刀石头布"式的循环优势，而非单调优势。
    """
    asymmetry_indicators = [
        "phase transition",
        "critical point",
        "symmetry breaking",
        "topological phase",
        "edge state",
        "flat band",
        "Fermi surface nesting",
        "quantum critical",
        "frustration",
        "competition",
        "trade-off",
        "tradeoff",
        "optimization",
        "routing",
        "self-organization",
    ]

    hit_count = sum(
        1 for ind in asymmetry_indicators if ind.lower() in core_mechanism.lower()
    )
    score = min(1.0, hit_count / 5.0)

    reasoning = []
    if score >= 0.8:
        reasoning.append("高竞争不对称性：可产生非平凡策略空间")
    elif score >= 0.4:
        reasoning.append("中等竞争不对称性：可能导致单调优化问题")
    else:
        reasoning.append("低竞争不对称性：策略空间趋近于零和博弈")

    return score, "; ".join(reasoning)


def assess_topological_compatibility(core_mechanism: str) -> Tuple[float, str]:
    """
    与现有 Kagome/EPR-Torsion 架构的拓扑兼容性。
    """
    existing_architecture_keywords = [
        "Kagome",
        "kagome",
        "triangular",
        "honeycomb",
        "frustrated",
        "lattice",
        "topological",
        "Chern",
        "edge state",
        "flat band",
        "Dirac",
        "Weyl",
        "nodal",
        "spin-orbit",
        "spin texture",
        "Berry",
        "torsion",
        "chiral",
        "superconductivity",
        "Kondo",
        "heavy fermion",
        "quantum metric",
        "Floquet",
        "driven",
        "topological insulator",
        "topological semimetal",
        "Majorana",
        "axion",
    ]

    hit_count = sum(
        1 for kw in existing_architecture_keywords if kw.lower() in core_mechanism.lower()
    )
    score = min(1.0, hit_count / 5.0)

    reasoning = []
    if score >= 0.8:
        reasoning.append("高度兼容：直接与现有Kagome/EPR-Torsion架构咬合")
    elif score >= 0.4:
        reasoning.append("部分兼容：需接口转换或桥接机制")
    else:
        reasoning.append("低兼容性：需新建架构层，成本高")

    return score, "; ".join(reasoning)


def assess_anti_gravity_potential(core_mechanism: str) -> Tuple[float, str]:
    """
    反引力潜力 — 是否对扭曲时空曲率有直接贡献。
    这是你特别要求的第二个模块的先导评估。
    """
    anti_gravity_indicators = [
        "warp",
        "Alcubierre",
        "torsion",
        "Einstein-Cartan",
        "curvature",
        "metric",
        "spacetime",
        "anti-gravity",
        "antigravity",
        "mass reduction",
        "mass nullification",
        "gravity shielding",
        "gravitational",
        "negative energy",
        "exotic matter",
        "Casimir",
        "Kaluza-Klein",
        "extra dimension",
        "higher dimension",
        "graviton",
        "spin connection",
        "affine connection",
        "Riemann",
        "Ricci",
        "Bianchi",
        "inertial",
        "Mach",
        "frame dragging",
    ]

    hit_count = sum(
        1 for ind in anti_gravity_indicators if ind.lower() in core_mechanism.lower()
    )
    score = min(1.0, hit_count / 5.0)

    reasoning = []
    if score >= 0.8:
        reasoning.append("高反引力潜力：直接影响时空曲率生成")
    elif score >= 0.4:
        reasoning.append("中等反引力潜力：间接影响，需耦合放大机制")
    else:
        reasoning.append("低反引力潜力：与时空曲率无直接关联")

    return score, "; ".join(reasoning)


def assess_empirical_anchoring(core_mechanism: str) -> Tuple[float, str]:
    """
    是否绑定真实实验或arXiv论文。
    """
    empirical_indicators = [
        "experiment",
        "observation",
        "measured",
        "synthesis",
        "fabrication",
        "ST",
        "ARPES",
        "neutron",
        "X-ray",
        "transport",
        "conductivity",
        "specific heat",
        "magnetization",
        "STM",
        "AFM",
        "TEM",
        "arxiv",
        "Nature",
        "Science",
        "PRL",
        "PRB",
        "Physical Review",
        "Nano Letters",
        "Advanced Materials",
        "doi",
    ]

    hit_count = sum(
        1 for ind in empirical_indicators if ind.lower() in core_mechanism.lower()
    )
    score = min(1.0, hit_count / 5.0)

    reasoning = []
    if score >= 0.8:
        reasoning.append("强烈经验锚定：有直接实验或已发表论文支撑")
    elif score >= 0.4:
        reasoning.append("部分经验锚定：理论框架内存在，但缺乏直接实验证据")
    else:
        reasoning.append("弱经验锚定：纯理论推测或跨领域迁移")

    return score, "; ".join(reasoning)


def suggest_fitness_function(
    dim_scores: Dict[str, float],
    core_mechanism: str,
    parameters: Dict[str, float],
) -> str:
    """
    根据评估结果，推荐合适的fitness函数签名。

    匹配策略：从FITNESS_TEMPLATES中找语义最近的模板，
    或生成新的签名。
    """
    # 若拓扑兼容性高，优先匹配现有架构关键词
    best_match = None
    best_score = 0.0

    for template_name, template_sig in FITNESS_TEMPLATES.items():
        kw = template_name.replace("_", " ")
        # 模糊匹配
        match = sum(
            1 for word in kw.split() if word.lower() in core_mechanism.lower()
        )
        if match > best_score:
            best_score = match
            best_match = template_sig

    if best_match and best_score > 0:
        return best_match

    # 无匹配，生成通用签名
    param_names = list(parameters.keys())[:5]
    param_str = ", ".join(param_names) if param_names else "θ₁, θ₂, ..."
    return f"f({param_str}) → composite_fitness / energy_cost"


def compute_integration_score(dim_scores: Dict[str, float]) -> float:
    """
    加权计算Arena Integration Score [0, 1]。
    """
    score = 0.0
    for dim, weight in WEIGHTS.items():
        score += dim_scores.get(dim, 0.0) * weight
    return round(min(1.0, max(0.0, score)), 4)


def get_priority_tier(score: float) -> Tuple[str, str]:
    """
    根据综合评分确定推荐优先级。
    """
    if score >= 0.75:
        return "P0", "立即整合 — 高价值、高兼容、高演化潜力"
    elif score >= 0.55:
        return "P1", "建议整合 — 需桥接接口或代理模型"
    elif score >= 0.35:
        return "P2", "观察候选 — 等实验证据或理论突破再整合"
    else:
        return "P3", "暂不整合 — 贡献度或兼容性不足"


def run_assessment(
    core_mechanism: str,
    mathematical_form: str,
    parameters: Dict[str, float],
    title: str = "未命名机制",
) -> Dict:
    """
    主入口：对一条物理论文/机制运行完整6轴评估。

    参数：
        core_mechanism: 机制描述（自然语言，需包含关键词供启发式分析）
        mathematical_form: 数学形式描述
        parameters: {参数名: 默认值} 映射
        title: 机制名称
    """
    dim_scores = {}
    details = {}

    # 6轴评估
    dim_scores["computability"], details["computability"] = assess_computability(
        core_mechanism, mathematical_form
    )
    dim_scores["parameterizability"], details["parameterizability"] = (
        assess_parameterizability(core_mechanism, parameters)
    )
    dim_scores["competitive_asymmetry"], details["competitive_asymmetry"] = (
        assess_competitive_asymmetry(core_mechanism)
    )
    dim_scores["topological_compatibility"], details["topological_compatibility"] = (
        assess_topological_compatibility(core_mechanism)
    )
    dim_scores["anti_gravity_potential"], details["anti_gravity_potential"] = (
        assess_anti_gravity_potential(core_mechanism)
    )
    dim_scores["empirical_anchoring"], details["empirical_anchoring"] = (
        assess_empirical_anchoring(core_mechanism)
    )

    integration_score = compute_integration_score(dim_scores)
    priority_tier, priority_reason = get_priority_tier(integration_score)
    suggested_fitness = suggest_fitness_function(
        dim_scores, core_mechanism, parameters
    )

    return {
        "title": title,
        "integration_score": integration_score,
        "priority": {"tier": priority_tier, "reason": priority_reason},
        "dimension_scores": dim_scores,
        "dimension_details": details,
        "suggested_fitness_function": suggested_fitness,
        "recommended_parameters": list(parameters.keys()),
    }


def print_report(result: Dict):
    """格式化输出评估报告"""
    print("=" * 65)
    print(f"  Arena Integration Assessment: {result['title']}")
    print("=" * 65)
    print(f"  综合评分: {result['integration_score']:.4f}")
    print(f"  优先级:   {result['priority']['tier']} — {result['priority']['reason']}")
    print("-" * 65)
    print("  维度评分:")
    for dim, score in result["dimension_scores"].items():
        label = dim.replace("_", " ").title()
        bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
        print(f"    {label:30s} │{bar}│ {score:.2f}")
    print("-" * 65)
    print(f"  推荐 Fitness: {result['suggested_fitness_function']}")
    print(f"  推荐参数:     {', '.join(result['recommended_parameters'])}")
    print("=" * 65)


if __name__ == "__main__":
    # 快速自测：用现有的Kagome-Torsion引擎做一次评估
    test_result = run_assessment(
        core_mechanism=(
            "Kagome lattice topological defects coupling to Einstein-Cartan torsion, "
            "generating spin current via Berry curvature dipole and Einstein-de Haas effect, "
            "producing metric perturbation through N² superradiant amplification. "
            "Cooperative resonance phase-locking enables warp bubble generation with "
            "positive energy density per Bobrick-Martire and Rodal. "
            "Topological protection from 60° network chirality prevents warp instability "
            "per Buchert-Frackowiak. Multi-mode operation: gravity deflection, "
            "collision override, mass nullification, dimensional bias."
        ),
        mathematical_form=(
            "Modified Einstein-Cartan: G_μν + Λg_μν = κ(T_μν + T_μν^spin), "
            "J_s ∝ N (coherent), P ∝ N² (superradiant), δg_μν ∝ κ²(J_s)², "
            "Berry curvature dipole D_ab = ∫ dk f_0 ∂_a Ω_b, "
            "spin Hall conductivity σ_SH ∝ D_ab, "
            "mode switching via PLL retuning to target field gradient"
        ),
        parameters={
            "N_sync_nodes": 1e6,
            "spin_torque_Nm": 1e-6,
            "kondo_zero_mode_deviation_mev": 0.001,
            "dirac_mass_override_ratio": 98.5,
            "floquet_drive_coherence": 99.9,
            "semi_dirac_anisotropic_inertia": 5000.0,
        },
        title="Kagome-Torsion Multi-Mode Engine",
    )
    print_report(test_result)
