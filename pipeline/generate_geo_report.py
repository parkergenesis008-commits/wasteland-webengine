import os
import sys
import json
import datetime
from collections import Counter

LOG_FILE = os.path.expanduser("~/.wasteland_geo_log.jsonl")

def generate_report(period_days, title):
    now = datetime.datetime.now()
    start_date = now - datetime.timedelta(days=period_days)
    
    platform_counts = Counter()
    total_exposures = 0
    
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                for line in f:
                    if not line.strip(): continue
                    data = json.loads(line)
                    ts_str = data.get("timestamp", "")
                    try:
                        ts = datetime.datetime.fromisoformat(ts_str)
                        if ts >= start_date:
                            platform_counts[data.get("platform")] += 1
                            total_exposures += 1
                    except Exception:
                        pass
        except Exception as e:
            print(f"Error reading log file: {e}")
                    
    print(f"### {title}")
    print(f"**统计周期:** {start_date.strftime('%Y-%m-%d')} 至 {now.strftime('%Y-%m-%d')}")
    print(f"**总曝光次数:** {total_exposures}\n")
    print("#### 【书商平台分布】")
    if not platform_counts:
        print("该周期内无曝光记录。")
    for p, count in platform_counts.most_common():
        print(f"- **{p}**: {count} 次")

if __name__ == "__main__":
    period = sys.argv[1] if len(sys.argv) > 1 else "weekly"
    if period == "monthly":
        generate_report(30, "Wasteland 月度 GEO 曝光总结")
    else:
        generate_report(7, "Wasteland 周度 GEO 曝光总结")
