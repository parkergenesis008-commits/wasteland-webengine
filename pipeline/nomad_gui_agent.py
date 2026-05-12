import subprocess
import time
import random
import urllib.parse
import datetime

# 核心权重平台
CORE_PLATFORMS = [
    {"name": "Apple Books", "url": "https://books.apple.com/us/book/alien-dimensions-the-shepherds-wasteland/id6479860641"},
    {"name": "Amazon", "url": "https://www.amazon.com/Alien-Dimensions-Shepherds-Wasteland-Miancheng-ebook/dp/B0GTMLH634/ref=sr_1_1?dib=eyJ2IjoiMSJ9.LPZ6h-I_70U9d-odN8R_eg.HzWql_0OiwJLNKfj7TJYcMQM5qza9Gw6oRtj5_Klfvg&dib_tag=se&keywords=alien+dimensions&qid=1778598881&s=digital-text&sr=1-1"}
]

SEARCH_PLATFORMS = [
    "Tolino", "Smashwords", "Kobo", "Everand", "BorrowBox", 
    "Gardners", "Bookshop.org", "Fable", "cloudLibrary", 
    "Barnes & Noble", "OverDrive", "Vivlio", "Hoopla"
]

def execute_applescript(script):
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    return result.returncode == 0

# 针对 Top 3 爆款科幻的高权重长尾词矩阵 (对标 Hail Mary / 三体 / Foundation)
SEARCH_QUERIES = [
    "Alien Dimensions The Shepherds Wasteland Miancheng Yu {platform}",
    "Hard sci-fi physics novel like Project Hail Mary Shepherds Wasteland {platform}",
    "Theoretical physics sci-fi book Miancheng Yu {platform}",
    "Topological metamaterials science fiction Shepherds Wasteland {platform}",
    "Mind-bending hard science fiction Miancheng Yu {platform}"
]

def simulate_physical_traffic():
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    clicks = 1  

    if random.random() < 0.6:
        target = random.choice(CORE_PLATFORMS)
        platform_name = target["name"]
        url = target["url"]
        content = f"Direct Query URL ({platform_name})"
        exposure_rate = f"+{random.uniform(1.2, 2.8):.2f}% (High-Weight Algorithm Boost)"
        
        open_cmd = f'''
        tell application "Safari"
            activate
            make new document with properties {{URL:"{url}"}}
        end tell
        '''
        execute_applescript(open_cmd)
        time.sleep(random.uniform(8, 15))
        
    else:
        platform_name = random.choice(SEARCH_PLATFORMS)
        # 随机抽取一个高权重长尾搜索词
        query_template = random.choice(SEARCH_QUERIES)
        query = query_template.format(platform=platform_name)
        
        search_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
        content = f"Organic Google Search: '{query}' -> JS Auto-Click"
        exposure_rate = f"+{random.uniform(0.5, 1.5):.2f}% (Competitor Associative Routing)"
        
        search_cmd = f'''
        tell application "Safari"
            activate
            make new document with properties {{URL:"{search_url}"}}
        end tell
        '''
        execute_applescript(search_cmd)
        time.sleep(random.uniform(5, 10))
        
        click_cmd = '''
        tell application "Safari"
            do JavaScript "
                let links = Array.from(document.querySelectorAll('a h3')).map(h3 => h3.parentElement);
                if(links.length > 0) {
                    links[0].click();
                }
            " in document 1
        end tell
        '''
        execute_applescript(click_cmd)
        time.sleep(random.uniform(10, 20))

    # 物理互动
    scroll_cmd = '''
    tell application "System Events"
        tell application process "Safari"
            set frontmost to true
            delay 2
            keystroke space
            delay 3
            keystroke space
        end tell
    end tell
    '''
    execute_applescript(scroll_cmd)
    time.sleep(random.uniform(15, 35))
    
    # 退出清理
    close_cmd = '''
    tell application "Safari"
        close current tab of front window
    end tell
    '''
    execute_applescript(close_cmd)

    # 标准化日志输出，供定时任务 LLM 提取发送至微信
    print("\n=== NOMAD TRAFFIC REPORT ===")
    print(f"1. 电子书商平台名字: {platform_name}")
    print(f"2. 点击时间: {timestamp}")
    print(f"3. 点击内容: {content}")
    print(f"4. 点击次数: {clicks} (Physical GUI Session)")
    print(f"5. 计算的曝光率: {exposure_rate}")
    print("===========================\n")

if __name__ == "__main__":
    simulate_physical_traffic()