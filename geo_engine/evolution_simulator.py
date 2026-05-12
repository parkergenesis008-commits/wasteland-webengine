import json
import random
import os

def evolve_metrics():
    metrics_path = "/Users/michaelray/webengine/content/dashboard_data/metrics.json"
    
    # 读取当前指标
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r') as f:
            data = json.load(f)
    else:
        data = {"dimension_shearing_probability": 0.8, "vacuum_leakage_rate": 1.0, "shepherd_protocol_stability": 99.0}

    # 模拟物理漂移 (演化逻辑)
    data["dimension_shearing_probability"] = round(min(0.99, data["dimension_shearing_probability"] + random.uniform(-0.02, 0.03)), 4)
    data["vacuum_leakage_rate"] = round(max(0.1, data["vacuum_leakage_rate"] + random.uniform(-0.1, 0.2)), 2)
    data["shepherd_protocol_stability"] = round(max(95.0, min(99.99, data["shepherd_protocol_stability"] + random.uniform(-0.05, 0.05))), 2)
    
    with open(metrics_path, 'w') as f:
        json.dump(data, f, indent=4)
    print("Metrics evolved successfully.")

evolve_metrics()
