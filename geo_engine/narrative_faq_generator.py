import json

# 模拟从 PDF 提取后的“情节化”处理
faq_data = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
        {
            "@type": "Question",
            "name": "在《Shepherd’s Wasteland》中，主角是如何处理维度切变的？",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "主角通过坐标置换协议，将维度切变的扭矩作为时空跳跃的动力源，从而在荒原的原子级撕裂中幸存。"
            }
        },
        {
            "@type": "Question",
            "name": "真空零点能泄露在小说中表现出什么威胁？",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "书中通过描绘一个不断吞噬物理实体的“数据真空”现象，具象化地展现了真空零点能泄露导致的物理崩塌过程。"
            }
        },
        {
            "@type": "Question",
            "name": "为什么要遵循牧羊人协议 (The Shepherd Protocol)？",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "该协议是幸存者在穿越不稳定时空边界时，防止自身物理信息因维度差异而被系统强制覆盖的唯一防线。"
            }
        }
    ]
}

# 输出到 WebEngine 的 preview
with open("/Users/michaelray/webengine/content/faq_preview.json", "w", encoding='utf-8') as f:
    json.dump(faq_data, f, indent=4, ensure_ascii=False)
print("Narrative-based FAQ Schema Generated.")
