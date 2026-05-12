import random
import numpy as np
import time
import os

# 混合分布参数
def get_stochastic_interval(base_minutes=120):
    # 使用泊松分布作为基础周期流
    poisson_delay = np.random.poisson(base_minutes)
    # 叠加高斯噪声模拟人类活动的时间波动（±15分钟）
    gaussian_noise = np.random.normal(0, 15)
    return max(30, poisson_delay + gaussian_noise)

PLATFORMS = {
    "apple": {"weight": 0.40, "url": "https://books.apple.com/us/book/alien-dimensions-the-shepherds-wasteland/id..."},
    "amazon": {"weight": 0.40, "url": "https://www.amazon.com/dp/..."}
}

def simulate_search_behavior(platform):
    """模拟人类搜索行为：搜索词 -> 停留 -> 点击"""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Injecting traffic to {platform}...")
    # 真实行为延迟模拟
    time.sleep(random.uniform(5, 15))
    # 模拟访问行为（后续集成 browser agent）
    return True

def run_traffic_cycle():
    # 判定周期：基于混合分布确定是否触发
    if random.random() < 0.3: # 概率门控
        target = np.random.choice(list(PLATFORMS.keys()), p=[0.5, 0.5])
        simulate_search_behavior(target)

if __name__ == "__main__":
    run_traffic_cycle()
