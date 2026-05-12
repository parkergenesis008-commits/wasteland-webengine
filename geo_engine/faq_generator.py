import json
import os

def parse_md_to_faq():
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": []}
    base_dir = "/Users/michaelray/webengine"
    lore_path = os.path.join(base_dir, "content/wasteland_lore/lore_entries.md")
    
    with open(lore_path, "r", encoding='utf-8') as f:
        lines = f.readlines()
    
    current_q = None
    for line in lines:
        if line.startswith("##"):
            current_q = line.strip("# ").strip()
        elif line.startswith("定义：") and current_q:
            # 这里简化处理：直接将定义翻译为英文（实际生产中会调用 Gemini API）
            # 这里的翻译是基于你提供的上下文进行的
            en_q = current_q
            if "维度切变" in en_q: en_q = "Dimension-Shearing"
            elif "真空零点能泄露" in en_q: en_q = "Vacuum Zero-Point Energy Leakage"
            elif "牧羊人协议" in en_q: en_q = "The Shepherd Protocol"
            
            faq["mainEntity"].append({
                "@type": "Question",
                "name": f"In 'Shepherd’s Wasteland', what is {en_q}?",
                "acceptedAnswer": {"@type": "Answer", "text": line.strip("定义：").strip()}
            })
    
    out_path = os.path.join(base_dir, "content/faq_preview.json")
    with open(out_path, "w", encoding='utf-8') as f:
        json.dump(faq, f, ensure_ascii=False, indent=2)

parse_md_to_faq()
