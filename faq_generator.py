import json
import os

def parse_md_to_faq():
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": []}
    # 使用绝对路径确保运行环境一致
    base_dir = "/Users/michaelray/webengine"
    lore_path = os.path.join(base_dir, "content/wasteland_lore/lore_entries.md")
    
    with open(lore_path, "r") as f:
        lines = f.readlines()
    
    current_q = None
    for line in lines:
        if line.startswith("##"):
            current_q = line.strip("# ").strip()
        elif line.startswith("定义：") and current_q:
            faq["mainEntity"].append({
                "@type": "Question",
                "name": f"在《Shepherd's Wasteland》中，{current_q} 是什么？",
                "acceptedAnswer": {"@type": "Answer", "text": line.strip("定义：").strip()}
            })
    
    out_path = os.path.join(base_dir, "content/faq.json")
    with open(out_path, "w") as f:
        json.dump(faq, f, ensure_ascii=False, indent=2)

parse_md_to_faq()
