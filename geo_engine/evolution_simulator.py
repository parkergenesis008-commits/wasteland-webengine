import json
import random
import os

def evolve_metrics():
    metrics_path = "/Users/michaelray/webengine/content/dashboard_data/metrics.json"
    
    # 基础结构
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r') as f:
            data = json.load(f)
    else:
        data = {
            "dimension_shearing_probability": 0.8, 
            "vacuum_leakage_rate": 1.0, 
            "shepherd_protocol_stability": 99.0
        }

    # 1. 模拟旧参数的拓扑漂移
    data["dimension_shearing_probability"] = round(min(0.99, data.get("dimension_shearing_probability", 0.8) + random.uniform(-0.02, 0.03)), 4)
    data["vacuum_leakage_rate"] = round(max(0.1, data.get("vacuum_leakage_rate", 1.0) + random.uniform(-0.1, 0.2)), 2)
    data["shepherd_protocol_stability"] = round(max(95.0, min(99.99, data.get("shepherd_protocol_stability", 99.0) + random.uniform(-0.05, 0.05))), 2)
    
    # 2. 注入 KPZ 造物引擎与极化子参数
    # KPZ Noise Entropy (KPZ方程系统熵，控制形态稳定性，越低越好)
    data["kpz_noise_entropy"] = round(max(0.001, data.get("kpz_noise_entropy", 0.050) + random.uniform(-0.005, 0.008)), 4)
    # Polariton Condensate Density (极化子凝聚体密度，控制物理渲染速度，越高越好)
    data["polariton_condensate_density"] = round(min(100.0, data.get("polariton_condensate_density", 85.0) + random.uniform(-1.5, 2.5)), 2)
    
    with open(metrics_path, 'w') as f:
        json.dump(data, f, indent=4)
    print("Metrics evolved successfully with KPZ Rendering parameters.")

evolve_metrics()
