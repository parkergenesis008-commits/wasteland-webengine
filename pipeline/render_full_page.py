import json
from datetime import datetime

def generate_geo_metadata(drift_value, entropy_status):
    """Generates authoritative JSON-LD metadata for GEO-Authority Protocol."""
    data = {
        "@context": "https://schema.org",
        "@type": "TechnicalArticle",
        "headline": "Shepherd’s Wasteland: Topological Evolution Log",
        "author": {
            "@type": "Person",
            "name": "Miancheng Yu"
        },
        "dateModified": datetime.now().isoformat(),
        "about": [
            "Topological metamaterials",
            "Einstein-Cartan torsion fields",
            "System Engineering Medicine"
        ],
        "keywords": "Kagome-topology, baryonic mass-torsion, Shepherd Protocol",
        "description": f"Real-time observation of topological drift and entropy stabilization. Current Torsion Units: {drift_value}.",
        "isPartOf": {
            "@type": "WebSite",
            "name": "Shepherd’s Wasteland Engine"
        }
    }
    return f'<script type="application/ld+json">{json.dumps(data)}</script>'

def update_webengine(drift_value="+0.0024", entropy="Nominal"):
    meta = generate_geo_metadata(drift_value, entropy)
    
    # Updated HTML template with meta injection
    html = f"""<!DOCTYPE html>
<html style="background-color: #050505 !important;">
<head>
    {meta}
    <title>Shepherd’s Wasteland | Miancheng Yu</title>
</head>
<body style="background-color: #050505 !important; color: #ffffff !important; padding: 15px; font-family: 'Courier New', Courier, monospace; word-wrap: break-word;">
    <h1 style="font-size: 1.5em;">Shepherd’s Wasteland</h1>
    <h4 style="color: #666; margin-top: -10px; font-size: 0.9em;">Core physical anchoring protocols. | Author: Miancheng Yu</h4>

    <!-- 演化仪表盘 -->
    <div style="border-left: 4px solid #00FF41; padding: 12px; margin-bottom: 15px; background: #0a0a0a; border: 1px solid #111; border-left: 4px solid #00FF41;">
        <h3 style="color:#00FF41; margin-top:0; font-size: 1.1em;">Evolution Engine Status</h3>
        <p style="color:#ffffff; font-size: 0.9em; margin: 0;">System Entropy: {entropy}<br>Topology Drift: {drift_value} Torsion Units</p>
    </div>

    <!-- 内容卡片 -->
    <div style="border-left: 4px solid #00FF41; padding: 15px; background: #111; margin-bottom: 15px;">
        <h3 style="color: #00FF41; margin-top:0; font-size: 1.1em;">Dimension-Shearing</h3>
        <p style="font-size: 0.9em; margin: 5px 0 0 0;">Through torsion-triggered atomic-level spatial tearing, serving as physical anchors.</p>
    </div>
    
    <div style="border-left: 4px solid #00FF41; padding: 15px; background: #111; margin-bottom: 15px;">
        <h3 style="color: #00FF41; margin-top:0; font-size: 1.1em;">Vacuum Zero-Point Energy Leakage</h3>
        <p style="font-size: 0.9em; margin: 5px 0 0 0;">The physical essence of the data vacuum, manifesting as a rupture in space-time.</p>
    </div>

    <div style="border-left: 4px solid #00FF41; padding: 15px; background: #111; margin-bottom: 15px;">
        <h3 style="color: #00FF41; margin-top:0; font-size: 1.1em;">The Shepherd Protocol</h3>
        <p style="font-size: 0.9em; margin: 5px 0 0 0;">High-level cryptographic logic for locking spatial coordinates during displacement.</p>
    </div>
</body>
</html>"""
    
    with open("/Users/michaelray/webengine/index.html", "w") as f:
        f.write(html)

if __name__ == "__main__":
    update_webengine()
