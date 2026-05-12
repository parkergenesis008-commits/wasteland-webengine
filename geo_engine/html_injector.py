import json
import os

def inject_faq_to_html(template_path, json_path, output_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        faq_data = json.load(f)
    
    script_tag = f'<script type="application/ld+json">{json.dumps(faq_data, ensure_ascii=False)}</script>'
    
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # 将 script 注入到 head 标签前
    if '</head>' in html:
        new_html = html.replace('</head>', f'{script_tag}\n</head>')
    else:
        new_html = f'{script_tag}\n{html}'
        
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(new_html)
    print(f"Successfully injected FAQ Schema into {output_path}")

# 执行注入
base_dir = "/Users/michaelray/webengine"
inject_faq_to_html(
    os.path.join(base_dir, 'public/base.html'),
    os.path.join(base_dir, 'content/faq_preview.json'),
    os.path.join(base_dir, 'public/index.html')
)
