import json
import os

with open('/Users/michaelray/webengine/content/faq_preview.json', 'r', encoding='utf-8') as f:
    faq = json.load(f)

body_content = '<h1>Shepherd’s Wasteland</h1>'
body_content += '<div id="content"><h2>Core Physical Settings</h2>'
for entity in faq['mainEntity']:
    body_content += f'<h3>{entity["name"]}</h3><p>{entity["acceptedAnswer"]["text"]}</p>'
body_content += '</div>'

html_template = f'''<html>
<head>
    <title>Shepherd’s Wasteland - Theoretical Anchor</title>
    <script type="application/ld+json">{json.dumps(faq, ensure_ascii=False)}</script>
</head>
<body>
    {body_content}
</body>
</html>'''

with open('/Users/michaelray/webengine/index.html', 'w', encoding='utf-8') as f:
    f.write(html_template)
