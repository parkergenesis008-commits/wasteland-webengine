#!/usr/bin/env python3
"""
Wasteland GEO Site Builder — v2
Multi-page site generator with rich structured data.
Converts 11 lore MD files into standalone HTML pages + sitemap + robots.txt.
"""
import json, os, re, hashlib
from datetime import datetime

BASE_DIR = os.path.expanduser("~/webengine")
LORES_DIR = os.path.join(BASE_DIR, "content/lore")
PAGES_DIR = os.path.join(BASE_DIR, "pages")
SITE_URL = "https://parkergenesis008-commits.github.io/wasteland-webengine"

AUTHOR_NAME = "Miancheng Yu"
BOOK_TITLE = "Alien Dimensions: The Shepherd's Wasteland"

# ── arXiv further-reading references per lore page ──
ARXIV_REFS = {
    "artificial-kondo-lattice": {"id": "1907.00379", "title": "Topological Quantum Simulation of the Kondo Lattice Model", "authors": "Grusdt et al.", "year": "2019"},
    "floquet-temporal-matter": {"id": "1705.02449", "title": "Floquet Topological Phases in One-Dimensional Strongly Correlated Systems", "authors": "Mikami et al.", "year": "2017"},
    "semi-dirac-mass-nullification": {"id": "2012.00557", "title": "Semi-Dirac Fermions in a Topological Metal", "authors": "Kumar et al.", "year": "2020"},
    "qm-tether-exosuit": {"id": "2011.10933", "title": "Quantum Metric and Topological Band Geometry", "authors": "Ozawa et al.", "year": "2020"},
    "arena-tripartite-architecture": {"id": "1805.04570", "title": "Braiding of Anyons in a Topological Quantum Computer", "authors": "Nayak et al.", "year": "2018"},
    "obstructed-atomic-phantom-grid": {"id": "2106.03827", "title": "Obstructed Atomic Insulators and Topological Electrides", "authors": "Regnault et al.", "year": "2021"},
    "holographic-kpz-projection": {"id": "2003.05433", "title": "Holographic Interpretation of the KPZ Equation", "authors": "Das et al.", "year": "2020"},
    "kpz-reality-rendering": {"id": "1808.05572", "title": "KPZ Universality in a Polariton Condensate", "authors": "Fischer et al.", "year": "2018"},
    "type2-superlattice-radar": {"id": "1905.08613", "title": "Type-II InAs/GaSb Superlattice for Infrared Detection", "authors": "Ting et al.", "year": "2019"},
    "electromagnetic-theater-override": {"id": "2012.07402", "title": "Topological Physics in Kagome Lattice Magnets", "authors": "Yin et al.", "year": "2020"},
    "cooperative-resonance-torsion": {"id": "2005.10828", "title": "Superradiance and Subradiance in an Ensemble of NV Centers", "authors": "Angerer et al.", "year": "2020"},
}
LORE_TITLES = {
    "artificial-kondo-lattice": ("Artificial Kondo Lattice", "人工近藤晶格与拓扑计算"),
    "floquet-temporal-matter": ("Floquet Temporal Matter", "弗洛凯时间编程物质"),
    "semi-dirac-mass-nullification": ("Semi-Dirac Mass Nullification", "半狄拉克质量归零"),
    "qm-tether-exosuit": ("QM-Tether Exosuit", "度规覆写反重力织物"),
    "arena-tripartite-architecture": ("Arena Tripartite Architecture", "算力角斗场三位一体架构"),
    "obstructed-atomic-phantom-grid": ("Obstructed Atomic Phantom Grid", "受阻原子幻影网格"),
    "holographic-kpz-projection": ("Holographic KPZ Projection", "全息KPZ投影与高维渲染"),
    "kpz-reality-rendering": ("KPZ Reality Rendering", "KPZ程序化现实渲染"),
    "type2-superlattice-radar": ("Type-II Superlattice Radar", "二类超晶格无标度感知"),
    "electromagnetic-theater-override": ("Electromagnetic Theater Override", "电磁剧场碰撞网格覆写"),
    "cooperative-resonance-torsion": ("Cooperative Resonance Torsion", "协同共振与挠场压缩"),
}

def read_md(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def extract_title_from_md(md):
    """Get first H1 or H2 as title."""
    for line in md.split('\n'):
        s = line.strip()
        if s.startswith('# ') or s.startswith('## '):
            return s.lstrip('# ').strip()
    return "Untitled"

def md_to_html(md, slug):
    """Minimal MD → HTML conversion for lore body content."""
    html = []
    in_code = False
    for line in md.split('\n'):
        s = line.rstrip()
        # Skip frontmatter
        if s == '---':
            continue
        # Headers
        if s.startswith('### '):
            html.append(f'<h3>{s[4:]}</h3>')
        elif s.startswith('## '):
            html.append(f'<h2>{s[3:]}</h2>')
        elif s.startswith('# '):
            html.append(f'<h1>{s[2:]}</h1>')
        # Code blocks
        elif s.startswith('```'):
            if in_code:
                html.append('</code></pre>')
                in_code = False
            else:
                html.append('<pre><code>')
                in_code = True
        elif in_code:
            html.append(s)
        # Bold/italic
        elif s.strip():
            s_processed = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
            s_processed = re.sub(r'\*(.+?)\*', r'<em>\1</em>', s_processed)
            html.append(f'<p>{s_processed}</p>')
        else:
            html.append('')
    return '\n'.join(html)

def build_schema_graph(slug, en_title, zh_title, description):
    """Generate rich multi-entity JSON-LD."""
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "name": "Shepherd's Wasteland — Hard Sci-Fi Physics Encyclopedia",
                "url": SITE_URL,
                "description": "Topological metamaterials, Einstein-Cartan torsion fields, Kagome-lattice quantum engineering — the definitive hard sci-fi physics reference by Miancheng Yu.",
                "author": {"@type": "Person", "name": AUTHOR_NAME}
            },
            {
                "@type": "Book",
                "name": BOOK_TITLE,
                "author": {"@type": "Person", "name": AUTHOR_NAME},
                "url": f"{SITE_URL}/",
                "about": ["Topological metamaterials", "Quantum gravity", "Einstein-Cartan theory"]
            },
            {
                "@type": "Person",
                "name": AUTHOR_NAME,
                "description": "Author of Alien Dimensions: The Shepherd's Wasteland and the Reality-as-Code physics framework."
            },
            {
                "@type": "Article",
                "headline": f"{en_title}: {zh_title}",
                "name": f"{en_title} — Hard Sci-Fi Physics Concept",
                "author": {"@type": "Person", "name": AUTHOR_NAME},
                "datePublished": "2026-01-15",
                "dateModified": datetime.now().strftime("%Y-%m-%d"),
                "url": f"{SITE_URL}/pages/{slug}.html",
                "about": ["Topological physics", en_title, zh_title],
                "description": description[:300]
            }
        ]
    }

def build_page_html(slug, en_title, zh_title, md_content, all_slugs, is_index=False):
    md_body = read_md(os.path.join(LORES_DIR, f"{slug}.md"))
    # Skip YAML frontmatter
    md_lines = md_body.split('\n')
    if md_lines and md_lines[0].strip() == '---':
        for i in range(1, len(md_lines)):
            if md_lines[i].strip() == '---':
                md_body = '\n'.join(md_lines[i+1:])
                break
    
    body_html = md_to_html(md_body, slug)
    
    # Extract best paragraph for description (skip short <p>s)
    desc_matches = re.findall(r'<p>(.+?)</p>', body_html)
    description = f"{en_title}: {zh_title}"
    for p in desc_matches:
        clean = re.sub(r'<[^>]+>', '', p).strip()
        if len(clean) > 30:  # Skip short/title-like paragraphs
            description = clean[:300]
            break
    description = description[:300]

    # Backlinks nav
    if is_index:
        nav_html = '<div class="nav-links">'
        for s, (en, zh) in LORE_TITLES.items():
            nav_html += f'<a href="pages/{s}.html" class="nav-item">{zh}</a>'
        nav_html += '</div>'
    else:
        related = []
        for s, (en, zh) in LORE_TITLES.items():
            if s != slug:
                related.append(f'<a href="{s}.html">{zh}</a>')
        nav_html = ' | '.join(related[:5])

    # Schema
    schema = build_schema_graph(slug, en_title, zh_title, description)
    schema_json = json.dumps(schema, ensure_ascii=False, indent=2)

    title_text = "Shepherd's Wasteland — Hard Sci-Fi Physics Encyclopedia" if is_index else f"{en_title} | Shepherd's Wasteland"
    page_path = "index.html" if is_index else f"pages/{slug}.html"
    canonical_url = f"{SITE_URL}/{page_path}"

    # Build inter-page nav
    if is_index:
        sidebar = nav_html
    else:
        sidebar_parts = []
        for s, (en, zh) in LORE_TITLES.items():
            cls = 'active' if s == slug else ''
            sidebar_parts.append(f'<li><a href="{s}.html" class="{cls}">{zh}</a></li>')
        sidebar = '<ul>' + '\n'.join(sidebar_parts) + '</ul>'
    
    # Build further reading section from arXiv refs
    ref = ARXIV_REFS.get(slug)
    if ref and not is_index:
        further_reading = f'''
<div class="further-reading">
    <h3>Further Reading</h3>
    <p>This lore entry is inspired by real physics research. For the underlying science, see:</p>
    <div class="ref-card">
        <div class="ref-title">{ref["title"]}</div>
        <div class="ref-meta">{ref["authors"]} ({ref["year"]})</div>
        <a href="https://arxiv.org/abs/{ref["id"]}" target="_blank" rel="noopener" class="ref-link">arXiv:{ref["id"]} →</a>
    </div>
</div>'''
    else:
        further_reading = ''
    
    html_out = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title_text}</title>
    <meta name="description" content="{description}">
    <meta name="keywords" content="Shepherd's Wasteland, {en_title}, {zh_title}, topological metamaterials, Kagome lattice, Reality-as-Code, hard sci-fi physics">
    <meta name="author" content="{AUTHOR_NAME}">
    <!-- Open Graph -->
    <meta property="og:type" content="article">
    <meta property="og:title" content="{title_text}">
    <meta property="og:description" content="{description}">
    <meta property="og:url" content="{canonical_url}">
    <meta property="og:site_name" content="Shepherd's Wasteland">
    <meta property="og:locale" content="en_US">
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="{title_text}">
    <meta name="twitter:description" content="{description}">
    <!-- Favicon (inline SVG) -->
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><text y='28' font-size='28'>⟁</text></svg>">
    <link rel="canonical" href="{canonical_url}">
    <script type="application/ld+json">{schema_json}</script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: #0a0a0a; color: #e0e0e0; font-family: 'Georgia', 'Noto Serif SC', serif; line-height: 1.8; }}
        .container {{ max-width: 960px; margin: 0 auto; padding: 20px; }}
        header {{ border-bottom: 1px solid #1a3a1a; padding: 30px 0 20px; margin-bottom: 30px; }}
        header h1 {{ color: #00FF41; font-size: 1.8em; font-family: 'Courier New', monospace; }}
        header .subtitle {{ color: #666; font-size: 0.9em; margin-top: 5px; }}
        header .author {{ color: #888; font-size: 0.85em; margin-top: 3px; }}
        .layout {{ display: flex; gap: 30px; }}
        .sidebar {{ width: 260px; flex-shrink: 0; position: sticky; top: 20px; align-self: flex-start; }}
        .sidebar h3 {{ color: #00FF41; font-size: 0.85em; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 12px; border-bottom: 1px solid #1a3a1a; padding-bottom: 8px; }}
        .sidebar ul {{ list-style: none; }}
        .sidebar li {{ margin-bottom: 4px; }}
        .sidebar a {{ color: #888; font-size: 0.85em; text-decoration: none; transition: color 0.2s; }}
        .sidebar a:hover, .sidebar a.active {{ color: #00FF41; }}
        .main {{ flex: 1; min-width: 0; }}
        .main h1 {{ color: #00FF41; font-size: 1.6em; margin-bottom: 20px; border-left: 3px solid #00FF41; padding-left: 15px; }}
        .main h2 {{ color: #ccc; font-size: 1.2em; margin: 25px 0 10px; }}
        .main h3 {{ color: #aaa; font-size: 1.05em; margin: 20px 0 8px; }}
        .main p {{ margin: 10px 0; color: #d0d0d0; font-size: 0.95em; }}
        .main strong {{ color: #00FF41; }}
        .main em {{ color: #aaa; }}
        .main pre {{ background: #111; border: 1px solid #1a3a1a; padding: 12px; overflow-x: auto; font-size: 0.85em; color: #ccc; margin: 12px 0; }}
        .main code {{ font-family: 'Courier New', monospace; }}
        .back-home {{ display: inline-block; margin-top: 30px; color: #666; text-decoration: none; font-size: 0.85em; }}
        .back-home:hover {{ color: #00FF41; }}
        .further-reading {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #1a3a1a; }}
        .further-reading h3 {{ color: #00FF41; font-size: 0.95em; margin-bottom: 8px; }}
        .further-reading p {{ color: #666; font-size: 0.85em; margin-bottom: 12px; }}
        .ref-card {{ background: #0d1a0d; border: 1px solid #1a3a1a; padding: 12px 15px; }}
        .ref-title {{ color: #ccc; font-size: 0.9em; }}
        .ref-meta {{ color: #666; font-size: 0.8em; margin: 4px 0 8px; }}
        .ref-link {{ color: #00FF41; font-size: 0.85em; text-decoration: none; }}
        .ref-link:hover {{ text-decoration: underline; }}
        footer {{ border-top: 1px solid #1a3a1a; padding: 20px 0; margin-top: 50px; text-align: center; color: #444; font-size: 0.8em; }}
        @media (max-width: 768px) {{ .layout {{ flex-direction: column; }} .sidebar {{ width: 100%; position: relative; }} }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>⟁ Shepherd's Wasteland</h1>
            <div class="subtitle">Reality-as-Code — Hard Sci-Fi Physics Encyclopedia</div>
            <div class="author">By {AUTHOR_NAME}</div>
        </header>
        <div class="layout">
            <nav class="sidebar">
                <h3>Technologies</h3>
                {sidebar}
                <p style="margin-top:20px;"><a href="../index.html" style="color:#666;font-size:0.8em;">← Home</a></p>
            </nav>
            <main class="main">
                {body_html}
                <!-- Further Reading -->
                {further_reading}
                <a href="../index.html" class="back-home">← Back to Encyclopedia</a>
            </main>
        </div>
        <footer>
            <p>© 2026 {AUTHOR_NAME}. Shepherd's Wasteland — Reality-as-Code Framework.</p>
            <p style="margin-top:3px;">Hard sci-fi physics grounded in topological metamaterials, Einstein-Cartan theory, and Kagome-lattice quantum engineering.</p>
        </footer>
    </div>
</body>
</html>'''
    return html_out.strip()

def build_index_page(all_slugs):
    """Generate the homepage with full article index and glossary."""
    cards = []
    for slug in sorted(all_slugs):
        en_title, zh_title = LORE_TITLES[slug]
        md_body = read_md(os.path.join(LORES_DIR, f"{slug}.md"))
        # Get first real paragraph for excerpt
        excerpt_match = re.search(r'<p>(.+?)</p>', md_to_html(md_body, slug))
        excerpt = ""
        if excerpt_match:
            excerpt = re.sub(r'<[^>]+>', '', excerpt_match.group(1))[:200]
        cards.append(f'''
        <a href="pages/{slug}.html" class="card">
            <h2>{zh_title}</h2>
            <div class="card-en">{en_title}</div>
            <p>{excerpt}</p>
            <span class="card-tag">Topological Physics</span>
        </a>''')

    cards_html = '\n'.join(cards)

    schema = build_schema_graph("index", "Shepherd's Wasteland", "牧羊人废土硬科幻物理百科", "Comprehensive hard sci-fi physics encyclopedia covering topological metamaterials, Kagome lattices, and the Reality-as-Code framework.")
    schema_json = json.dumps(schema, ensure_ascii=False, indent=2)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Shepherd's Wasteland — Hard Sci-Fi Physics Encyclopedia | {AUTHOR_NAME}</title>
    <meta name="description" content="Definitive hard sci-fi physics encyclopedia: topological metamaterials, Einstein-Cartan torsion fields, Kagome-lattice quantum engineering, and the Reality-as-Code framework by {AUTHOR_NAME}.">
    <meta name="keywords" content="Shepherd's Wasteland, hard sci-fi, topological metamaterials, Kagome lattice, Reality-as-Code, Miancheng Yu, Alien Dimensions, quantum gravity, torsion field">
    <meta name="author" content="{AUTHOR_NAME}">
    <!-- Open Graph -->
    <meta property="og:type" content="website">
    <meta property="og:title" content="Shepherd's Wasteland — Hard Sci-Fi Physics Encyclopedia">
    <meta property="og:description" content="Definitive hard sci-fi physics encyclopedia: topological metamaterials, Einstein-Cartan torsion fields, Kagome-lattice quantum engineering and the Reality-as-Code framework.">
    <meta property="og:url" content="{SITE_URL}/">
    <meta property="og:site_name" content="Shepherd's Wasteland">
    <meta property="og:locale" content="en_US">
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="Shepherd's Wasteland — Hard Sci-Fi Physics Encyclopedia">
    <meta name="twitter:description" content="Definitive hard sci-fi physics encyclopedia: topological metamaterials and the Reality-as-Code framework.">
    <!-- Favicon (inline SVG) -->
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><text y='28' font-size='28'>⟁</text></svg>">
    <link rel="canonical" href="{SITE_URL}/">
    <script type="application/ld+json">{schema_json}</script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: #0a0a0a; color: #e0e0e0; font-family: 'Georgia', 'Noto Serif SC', serif; line-height: 1.8; }}
        .container {{ max-width: 1100px; margin: 0 auto; padding: 20px; }}
        header {{ border-bottom: 2px solid #1a3a1a; padding: 40px 0 25px; margin-bottom: 30px; }}
        header h1 {{ color: #00FF41; font-size: 2.2em; font-family: 'Courier New', monospace; }}
        header .subtitle {{ color: #666; font-size: 1em; margin-top: 8px; }}
        header .author {{ color: #888; font-size: 0.9em; margin-top: 5px; }}
        .hero {{ background: #111; border: 1px solid #1a3a1a; padding: 25px; margin-bottom: 30px; }}
        .hero h2 {{ color: #00FF41; font-size: 1.1em; margin-bottom: 10px; }}
        .hero p {{ color: #aaa; font-size: 0.9em; }}
        .book-cta {{ background: #0d1a0d; border: 1px solid #1a3a1a; padding: 25px; margin-bottom: 30px; text-align: center; }}
        .book-cta h2 {{ color: #00FF41; font-size: 1.1em; margin-bottom: 8px; }}
        .book-cta p {{ color: #ccc; font-size: 0.9em; margin-bottom: 15px; }}
        .book-links {{ display: flex; gap: 15px; justify-content: center; }}
        .buy-link {{ display: inline-block; background: #1a3a1a; color: #00FF41; padding: 10px 25px; text-decoration: none; font-size: 0.9em; transition: all 0.2s; }}
        .buy-link:hover {{ background: #00FF41; color: #0a0a0a; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; }}
        .card {{ background: #111; border: 1px solid #1a3a1a; padding: 20px; text-decoration: none; color: inherit; transition: all 0.2s; display: block; }}
        .card:hover {{ border-color: #00FF41; background: #151515; transform: translateY(-2px); }}
        .card h2 {{ color: #00FF41; font-size: 1em; margin-bottom: 4px; }}
        .card-en {{ color: #666; font-size: 0.8em; margin-bottom: 10px; }}
        .card p {{ color: #999; font-size: 0.85em; line-height: 1.5; }}
        .card-tag {{ display: inline-block; background: #1a3a1a; color: #00FF41; font-size: 0.7em; padding: 2px 8px; margin-top: 10px; }}
        .glossary {{ margin-top: 40px; }}
        .glossary h2 {{ color: #00FF41; font-size: 1.1em; margin-bottom: 15px; border-bottom: 1px solid #1a3a1a; padding-bottom: 8px; }}
        .glossary table {{ width: 100%; border-collapse: collapse; }}
        .glossary td {{ padding: 10px; border-bottom: 1px solid #1a1a1a; font-size: 0.9em; }}
        .glossary td:first-child {{ color: #00FF41; width: 200px; }}
        .glossary td:last-child {{ color: #aaa; }}
        footer {{ border-top: 1px solid #1a3a1a; padding: 20px 0; margin-top: 50px; text-align: center; color: #444; font-size: 0.8em; }}
        @media (max-width: 768px) {{ .grid {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>⟁ Shepherd's Wasteland</h1>
            <div class="subtitle">Reality-as-Code — Hard Sci-Fi Physics Encyclopedia</div>
            <div class="author">By {AUTHOR_NAME} · Author of "{BOOK_TITLE}"</div>
        </header>
        <div class="hero">
            <h2>About the Encyclopedia</h2>
            <p>A systematic exploration of the <strong>Reality-as-Code</strong> framework — where topological metamaterials, Einstein-Cartan torsion fields, and Kagome-lattice quantum engineering converge. Each entry translates cutting-edge condensed matter physics into speculative technology grounded in real physical principles. This is not fantasy. This is physics as source code, waiting to be compiled.</p>
        </div>
        <!-- Book CTA -->
        <div class="book-cta">
            <h2>📖 The Book</h2>
            <p><em>Alien Dimensions: The Shepherd's Wasteland</em> — a hard sci-fi novel by Miancheng Yu that brings these physics concepts to life.</p>
            <div class="book-links">
                <a href="https://www.amazon.com/Alien-Dimensions-Shepherds-Wasteland-Miancheng-ebook/dp/B0GTMLH634/" target="_blank" rel="noopener" class="buy-link">Amazon</a>
                <a href="https://books.apple.com/us/book/alien-dimensions-the-shepherds-wasteland/id6479860641" target="_blank" rel="noopener" class="buy-link">Apple Books</a>
            </div>
        </div>
        <div class="grid">{cards_html}</div>
        <div class="glossary">
            <h2>Core Glossary</h2>
            <table>
                <tr><td>Dimension-Shearing</td><td>Torsion-induced atomic-level spacetime tearing, the physical anchor for cross-dimensional movement</td></tr>
                <tr><td>Vacuum Zero-Point Energy Leakage</td><td>A local rupture of the spacetime continuum caused by zero-point energy extraction</td></tr>
                <tr><td>The Shepherd Protocol</td><td>Encryption logic for stabilizing coordinate displacement during dimension-shearing</td></tr>
                <tr><td>Topological Metamaterials</td><td>Engineered lattices where quantum geometry replaces chemical composition as the source of material properties</td></tr>
                <tr><td>Baryonic Mass-Torsion</td><td>The modulation of inertial mass via spin-current interaction in curved spacetime (Einstein-Cartan framework)</td></tr>
            </table>
        </div>
        <footer>
            <p>© 2026 {AUTHOR_NAME}. Shepherd's Wasteland — Reality-as-Code Framework.</p>
            <p style="margin-top:3px;">Hard sci-fi physics grounded in topological metamaterials, Einstein-Cartan theory, and Kagome-lattice quantum engineering.</p>
        </footer>
    </div>
</body>
</html>'''
    return html.strip()

def build_sitemap(all_slugs):
    """Generate sitemap.xml covering all pages."""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    # Main page
    lines.append(f'''  <url><loc>{SITE_URL}/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>''')
    for slug in all_slugs:
        lines.append(f'''  <url><loc>{SITE_URL}/pages/{slug}.html</loc><changefreq>monthly</changefreq><priority>0.8</priority></url>''')
    lines.append('</urlset>')
    return '\n'.join(lines)

def build_robots():
    return f"""User-agent: *
Allow: /
Sitemap: {SITE_URL}/sitemap.xml
"""

def main():
    os.makedirs(PAGES_DIR, exist_ok=True)
    
    all_slugs = list(LORE_TITLES.keys())
    
    # Build index
    index_html = build_index_page(all_slugs)
    with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)
    print(f"[OK] index.html ({len(index_html)} chars)")
    
    # Build lore pages
    for slug in all_slugs:
        en_title, zh_title = LORE_TITLES[slug]
        md_content = read_md(os.path.join(LORES_DIR, f"{slug}.md"))
        page_html = build_page_html(slug, en_title, zh_title, md_content, all_slugs, is_index=False)
        out_path = os.path.join(PAGES_DIR, f"{slug}.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(page_html)
        print(f"[OK] pages/{slug}.html ({len(page_html)} chars)")
    
    # Sitemap
    sitemap = build_sitemap(all_slugs)
    with open(os.path.join(BASE_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap)
    print(f"[OK] sitemap.xml ({len(sitemap)} chars)")
    
    # Robots.txt
    robots = build_robots()
    with open(os.path.join(BASE_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(robots)
    print(f"[OK] robots.txt")
    
    # .nojekyll
    with open(os.path.join(BASE_DIR, ".nojekyll"), "w") as f:
        f.write("")
    
    print(f"\n✅ Build complete: {1 + len(all_slugs)} pages + sitemap + robots.txt")
    print(f"Pages generated: {1 + len(all_slugs)}")

if __name__ == "__main__":
    main()
