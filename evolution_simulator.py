# Shepherd's Wasteland - Reality-as-Code Evolution Simulator
import random

class ArenaState:
    def __init__(self):
        self.kondo_zero_mode_deviation_mev = 0.0
        self.floquet_driving_cycles = 0
        self.corner_state_fidelity = 1.0

    def apply_floquet_hammer(self):
        # 模拟“祖冲之二号”的高阶非平衡拓扑相重击
        self.floquet_driving_cycles += 1
        if self.floquet_driving_cycles >= 50:
            self.corner_state_fidelity = 0.9999 + (random.random() * 0.0001)
            return "HOTP_CORNER_STATE_LOCKED"
        return "DRIVING_IN_PROGRESS"


class TMDChassis:
    def __init__(self):
        self.valley_degeneracy = 1
        self.shear_strain_tensor = 0.0
        self.landau_level_multiplex = 1
        self.flux_vortex_state = False

    def apply_shear_strain(self, pressure_gpa):
        self.shear_strain_tensor += pressure_gpa
        if self.shear_strain_tensor > 1.5:
            self.valley_degeneracy = "BROKEN"
            self.landau_level_multiplex = 3
            self.flux_vortex_state = True
            return "SYMMETRY_SHATTERED_TRIPLE_DEFENSE_ACTIVE"
        return "STRAIN_INCREASING"


class SiliconTinWafer:
    def __init__(self):
        self.tin_coverage = 0.0
        self.chiral_spin_state = False
        self.void_center_integrity = 0.0

    def deposit_tin_dust(self, coverage_ratio):
        self.tin_coverage = coverage_ratio
        if 0.330 < self.tin_coverage < 0.336:
            self.chiral_spin_state = True
            self.void_center_integrity = 1.0
            return "CHIRAL_FLOWER_BLOOM_SUCCESS"
        else:
            self.chiral_spin_state = False
            self.void_center_integrity = 0.0
            return "LATTICE_COLLAPSE"


class PlasmonicMoireFabric:
    def __init__(self):
        self.wavefront_phase_delta = 0.0
        self.skyrmion_topological_invariant = 0
        self.arena_coordinate_fidelity = 1.0

    def execute_topological_transition(self, phase_shift):
        self.wavefront_phase_delta = phase_shift
        self.skyrmion_topological_invariant = int(abs(phase_shift * 10))
        
        if self.skyrmion_topological_invariant > 5:
            self.arena_coordinate_fidelity = 0.0
            return "SKYRMION_MINEFIELD_DEPLOYED_COORDINATES_SCRAMBLED"
        return "FABRIC_NORMAL"


class MnBi2Te4Armor:
    def __init__(self):
        self.alox_cap_integrity = 1.0
        self.qah_insulation_strength = 1.0
        self.spin_flop_cascade_level = 0

    def withstand_in_plane_emp(self, magnetic_field_strength):
        if self.alox_cap_integrity > 0.9:
            self.spin_flop_cascade_level += int(magnetic_field_strength)
            self.qah_insulation_strength += (magnetic_field_strength * 0.5)
            return f"SPIN_FLOP_CASCADE_TRIGGERED_DEFENSE_UP_TO_{self.qah_insulation_strength}"
        return "ARMOR_BREACH_QUANTUM_DECOHERENCE"


class JunkLensArray:
    def __init__(self):
        self.lens_count = 12
        self.meron_texture_robustness = 0.0
        self.sensor_noise_level = 0.0

    def focus_hostile_light(self, chaotic_light_intensity, decoherence_noise):
        self.meron_texture_robustness = chaotic_light_intensity * 0.8
        residual_noise = max(0, decoherence_noise - self.meron_texture_robustness)
        self.sensor_noise_level = residual_noise
        
        if residual_noise == 0:
            return "SPONTANEOUS_MERON_SHIELD_ACTIVE_NOISE_NULLIFIED"
        return "PARTIAL_DECOHERENCE_SUSTAINED"


class EvolutionaryGameEngine:
    def __init__(self, population_size=1000000):
        self.population_size = population_size
        self.generation = 0
        # 初始种群比例
        self.phenotypes = {
            "MnBi2Te4_Tanks": 0.25,        # 锰铋碲风暴坦克 (吸收EMP)
            "TMD_Brawlers": 0.25,          # 机械破晶狂战士 (免疫锁定)
            "Plasmonic_Assassins": 0.25,   # 等离子体刺客 (扭曲坐标)
            "JunkLens_Scavengers": 0.25    # 废透镜拾荒者 (免疫强光噪声)
        }

    def run_generation(self, environment_hazard):
        self.generation += 1
        
        # 基于环境灾难的复制子动态 (Replicator Dynamics)
        if environment_hazard == "GLOBAL_EMP_STORM":
            # EMP风暴：坦克吸收能量繁衍，拾荒者和刺客大量死亡
            self.phenotypes["MnBi2Te4_Tanks"] *= 1.5
            self.phenotypes["JunkLens_Scavengers"] *= 0.6
            self.phenotypes["Plasmonic_Assassins"] *= 0.6
            self.phenotypes["TMD_Brawlers"] *= 0.9
        elif environment_hazard == "CHAOTIC_LASER_SWEEP":
            # 混乱激光扫射：拾荒者涌现Meron护盾存活，坦克装甲被过热
            self.phenotypes["JunkLens_Scavengers"] *= 1.4
            self.phenotypes["MnBi2Te4_Tanks"] *= 0.7
            self.phenotypes["TMD_Brawlers"] *= 0.8
        elif environment_hazard == "PRECISION_LOCK_ON":
            # 高维坐标锁定：狂战士应力劈裂脱靶，刺客扭曲坐标，坦克成活靶子
            self.phenotypes["TMD_Brawlers"] *= 1.3
            self.phenotypes["Plasmonic_Assassins"] *= 1.3
            self.phenotypes["MnBi2Te4_Tanks"] *= 0.5
            
        # 归一化种群比例
        total = sum(self.phenotypes.values())
        for key in self.phenotypes:
            self.phenotypes[key] /= total

        return self.phenotypes





if __name__ == "__main__":
    import random
    
    egt = EvolutionaryGameEngine()
    hazards = ["EMP_STORM", "LASER_SWEEP", "PRECISION_LOCK_ON", "MELEE_AMBUSH"]
    
    history = {k: [] for k in egt.phenotypes.keys()}
    
    for i in range(5000):
        hazard = random.choice(hazards)
        egt.generation += 1
        
        # Base decay
        for key in egt.phenotypes:
            egt.phenotypes[key] *= 0.9
            
        if hazard == "EMP_STORM":
            egt.phenotypes["MnBi2Te4_Tanks"] *= 2.0
            egt.phenotypes["JunkLens_Scavengers"] *= 0.3
        elif hazard == "LASER_SWEEP":
            egt.phenotypes["JunkLens_Scavengers"] *= 2.0
            egt.phenotypes["Plasmonic_Assassins"] *= 0.3
        elif hazard == "PRECISION_LOCK_ON":
            egt.phenotypes["Plasmonic_Assassins"] *= 2.0
            egt.phenotypes["MnBi2Te4_Tanks"] *= 0.3
        elif hazard == "MELEE_AMBUSH":
            egt.phenotypes["TMD_Brawlers"] *= 2.0
            egt.phenotypes["JunkLens_Scavengers"] *= 0.3
            egt.phenotypes["Plasmonic_Assassins"] *= 0.3
            
        # Tiny mutation rate
        for key in egt.phenotypes:
            egt.phenotypes[key] += 0.01
            
        total = sum(egt.phenotypes.values())
        for key in egt.phenotypes:
            egt.phenotypes[key] /= total
            history[key].append(egt.phenotypes[key])

    steady_state = {}
    for key in history:
        steady_state[key] = sum(history[key][-1000:]) / 1000.0
        
    print("\n=== RED QUEEN DYNAMICS (5000 Generations) ===")
    print("Steady State Averages (Last 1000 Gen):")
    for k, v in steady_state.items():
        print(f"  {k}: {v:.2%}")
        
    print("\nVolatility (Min - Max in last 1000 Gen):")
    for k in history:
        min_v = min(history[k][-1000:])
        max_v = max(history[k][-1000:])
        print(f"  {k}: {min_v:.2%} - {max_v:.2%}")
