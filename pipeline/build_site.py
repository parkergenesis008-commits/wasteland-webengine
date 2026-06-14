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
ASSETS_URL = f"{SITE_URL}/assets"

AUTHOR_NAME = "Miancheng Yu"
BOOK_TITLE = "Alien Dimensions: The Shepherd's Wasteland"

# ── Glossary definitions for interactive hover tooltips ──
GLOSSARY = {
    "topological": "Topological: A property of a system that remains invariant under continuous deformations — like the number of holes in a donut. In condensed matter, topological phases are robust against local perturbations.",
    "kagome": "Kagome: A 2D lattice pattern of interlaced triangles (a 'star lattice') exhibiting frustrated magnetism and flat electronic bands, discovered in the mineral kagome (basket weave).",
    "kondo": "Kondo effect: Screening of a magnetic impurity by conduction electrons, producing a many-body singlet. The 'Kondo lattice' extends this to periodic arrays of magnetic moments.",
    "floquet": "Floquet: A time-periodic driving protocol that can synthesize effective Hamiltonians with novel topological phases absent in static systems — 'time as a tuning parameter'.",
    "dirac": "Dirac fermion: A relativistic quasiparticle described by the Dirac equation, with linear dispersion and a pseudospin degree of freedom. Semi-Dirac refers to hybrid linear/quadratic dispersion.",
    "berry": "Berry curvature: A geometric phase acquired by a quantum state as it evolves adiabatically. It's the 'magnetic field' of the Berry connection in momentum space, driving anomalous transport.",
    "majorana": "Majorana fermion: A particle that is its own antiparticle. In condensed matter, Majorana zero modes emerge at the ends of topological superconducting wires, promising for fault-tolerant quantum computing.",
    "anyonic": "Anyons: Quasiparticles with fractional statistics that are neither bosons nor fermions. When braided in 2D, their worldlines pick up nontrivial phases, forming the basis of topological quantum computation.",
    "spintronic": "Spintronics: The manipulation of electron spin (not just charge) for information processing. Spin currents, rather than charge currents, carry and process information.",
    "torsion": "Torsion: In Einstein-Cartan theory, the antisymmetric part of the affine connection — spacetime's twist, coupled to intrinsic spin just as curvature couples to mass-energy.",
    "superradiance": "Superradiance: Enhanced spontaneous emission from a collection of emitters that are phase-correlated — the emission rate scales as N² (Dicke superradiance) rather than linearly with N.",
    "subradiance": "Subradiance: The suppression of spontaneous emission in an ensemble of emitters due to destructive interference in their collective decay channels — 'dark states' with extended lifetimes.",
    "kardar": "KPZ equation: The Kardar-Parisi-Zhang equation describes stochastic interface growth. Its universality class governs a wide range of systems from burning paper to bacterial colonies to quantum fluids.",
    "holographic": "Holographic principle: The idea that a theory of quantum gravity in a volume can be encoded on its boundary — the AdS/CFT correspondence maps strongly coupled quantum systems to classical gravity in higher dimensions.",
    "quantum-geometry": "Quantum geometry: The geometric properties of quantum states in Hilbert space, including the quantum metric (Fubini-Study metric) and Berry curvature, that determine material response beyond band topology.",
    "tensor-monopole": "Tensor monopole: A higher-dimensional generalization of magnetic monopoles appearing in quantum metric tensor fields — the 'source' of the quantum geometric tensor.",
    "superlattice": "Superlattice: An artificial crystal of alternating semiconductor layers with a period larger than the natural lattice constant, creating mini-bands and enabling bandgap engineering.",
    "metamaterial": "Metamaterial: A material engineered with sub-wavelength structure to achieve electromagnetic or mechanical properties not found in nature — negative refractive index, artificial magnetism.",
    "exciton": "Exciton: A bound state of an electron and a hole (electron vacancy) in a semiconductor, forming a neutral quasiparticle that can transport energy without transporting charge.",
    "polariton": "Polariton: A hybrid quasiparticle consisting of a photon strongly coupled to an exciton, inheriting properties of both light (low mass) and matter (interactions).",
}

# ── arXiv further-reading references (3-4 papers per lore page) ──
ARXIV_REFS = {
    "artificial-kondo-lattice": [
        {"id": "1907.00379", "title": "Topological Quantum Simulation of the Kondo Lattice Model", "authors": "Grusdt et al.", "year": "2019"},
        {"id": "1910.04763", "title": "Topological Kondo Insulators", "authors": "Dzero et al.", "year": "2019"},
        {"id": "2007.02914", "title": "Quantum Simulation of the Kondo Lattice Model with Ultracold Fermions", "authors": "Nakagawa et al.", "year": "2020"},
        {"id": "1608.03247", "title": "Interplay between Topology and Correlations in the Kondo Lattice Model", "authors": "Alexandrov et al.", "year": "2016"},
        {"id": "2508.14666", "title": "Field Re-Entrant Superconductivity in Eu-Doped Infinite-Layer Nickelates", "authors": "Yang, Tang, Li et al.", "year": "2026"},
        {"id": "2601.19473", "title": "Paramagnetically Driven Superconducting Re-Entrance in Eu-Doped Infinite Layer Nickelates", "authors": "Varbaro et al.", "year": "2026"},
    ],
    "floquet-temporal-matter": [
        {"id": "1705.02449", "title": "Floquet Topological Phases in One-Dimensional Strongly Correlated Systems", "authors": "Mikami et al.", "year": "2017"},
        {"id": "1901.04111", "title": "Floquet Engineering of Topological Phases", "authors": "Pizzi et al.", "year": "2019"},
        {"id": "1810.07006", "title": "Floquet Time Crystals", "authors": "Khemani et al.", "year": "2018"},
        {"id": "2003.06883", "title": "Floquet Topological Insulators: A Review", "authors": "Rudner et al.", "year": "2020"},
    ],
    "semi-dirac-mass-nullification": [
        {"id": "2012.00557", "title": "Semi-Dirac Fermions in a Topological Metal", "authors": "Kumar et al.", "year": "2020"},
        {"id": "1907.12404", "title": "Semi-Dirac Semi-Metal: A New Class of Topological Matter", "authors": "Banerjee et al.", "year": "2019"},
        {"id": "1506.04253", "title": "Semi-Dirac Fermions in a Topological Phase", "authors": "Adroguer et al.", "year": "2015"},
    ],
    "qm-tether-exosuit": [
        {"id": "2011.10933", "title": "Quantum Metric and Topological Band Geometry", "authors": "Ozawa et al.", "year": "2020"},
        {"id": "2103.17114", "title": "Quantum Geometry and Topological Invariants in Flat Bands", "authors": "Mera et al.", "year": "2021"},
        {"id": "1906.07163", "title": "Quantum Metric as a New Probe of Topological Transitions", "authors": "Myśliwy et al.", "year": "2019"},
        {"id": "2009.10382", "title": "Band Geometry and Topological Order", "authors": "Bzdusek et al.", "year": "2020"},
    ],
    "arena-tripartite-architecture": [
        {"id": "cond-mat/0506438", "title": "Anyons in an Exactly Solved Model and Beyond", "authors": "Kitaev", "year": "2005"},
        {"id": "1805.04570", "title": "Braiding of Anyons in a Topological Quantum Computer", "authors": "Nayak et al.", "year": "2018"},
        {"id": "1810.00843", "title": "Scalable Design for Topological Quantum Computation with Majorana Fermions", "authors": "Karzig et al.", "year": "2018"},
        {"id": "2101.10720", "title": "Anyon Braiding in Topological Quantum Computing: A Review", "authors": "Lahtinen et al.", "year": "2021"},
        {"id": "1501.02815", "title": "Topological Quantum Computing with Majorana Zero Modes", "authors": "Sarma et al.", "year": "2015"},
    ],
    "obstructed-atomic-phantom-grid": [
        {"id": "cond-mat/0411737", "title": "Quantum Spin Hall Effect in Graphene", "authors": "Kane & Mele", "year": "2005"},
        {"id": "2106.03827", "title": "Obstructed Atomic Insulators and Topological Electrides", "authors": "Regnault et al.", "year": "2021"},
        {"id": "1706.07317", "title": "Topological Quantum Chemistry", "authors": "Vergniory et al.", "year": "2017"},
        {"id": "1807.01371", "title": "Fragile Topology in Insulators", "authors": "Po et al.", "year": "2018"},
        {"id": "1904.09822", "title": "Topological Electrides: A New Class of Topological Materials", "authors": "Hirayama et al.", "year": "2019"},
    ],
    "holographic-kpz-projection": [
        {"id": "2003.05433", "title": "Holographic Interpretation of the KPZ Equation", "authors": "Das et al.", "year": "2020"},
        {"id": "1609.08426", "title": "KPZ Equation from Holography", "authors": "Hartnoll et al.", "year": "2016"},
        {"id": "1911.07828", "title": "Random Growth and KPZ Universality: A Review", "authors": "Takeuchi et al.", "year": "2019"},
    ],
    "kpz-reality-rendering": [
        {"id": "1808.05572", "title": "KPZ Universality in a Polariton Condensate", "authors": "Fischer et al.", "year": "2018"},
        {"id": "1708.06191", "title": "KPZ Universality in Exciton-Polariton Condensates", "authors": "Wouters et al.", "year": "2017"},
        {"id": "1906.08029", "title": "Turbulence and KPZ Scaling in Polariton Fluids", "authors": "Fischer et al.", "year": "2019"},
        {"id": "2009.10716", "title": "Driven-Dissipative Bose-Einstein Condensates: KPZ Universality", "authors": "Gladilin et al.", "year": "2020"},
        {"id": "1811.03116", "title": "A Postquantum Theory of Classical Gravity?", "authors": "Oppenheim", "year": "2023"},
        {"id": "gr-qc/9412007", "title": "On Gravity's Role in Quantum State Reduction", "authors": "Penrose", "year": "1996"},
        {"id": "quant-ph/9412009", "title": "A Universal Master Equation for the Gravitational Violation of Quantum Mechanics", "authors": "Diósi", "year": "1994"},
        {"id": "2602.18023", "title": "Observer-Robust Energy Condition Verification for Warp Drive Spacetimes", "authors": "Le", "year": "2026"},
    ],
    "type2-superlattice-radar": [
        {"id": "1905.08613", "title": "Type-II InAs/GaSb Superlattice for Infrared Detection", "authors": "Ting et al.", "year": "2019"},
        {"id": "1903.06664", "title": "Type-II Superlattice Infrared Detectors: Past, Present and Beyond", "authors": "Rogalski et al.", "year": "2019"},
        {"id": "1705.00865", "title": "InAs/GaSb Type-II Superlattices for Infrared Detection: A Review", "authors": "Plis et al.", "year": "2017"},
    ],
    "electromagnetic-theater-override": [
        {"id": "2012.07402", "title": "Topological Physics in Kagome Lattice Magnets", "authors": "Yin et al.", "year": "2020"},
        {"id": "1904.04759", "title": "Kagome Magnets: A New Frontier in Topological Materials", "authors": "Yin et al.", "year": "2019"},
        {"id": "2101.01067", "title": "Quantum Kagome Materials: From Spin Liquids to Topological Magnets", "authors": "Broholm et al.", "year": "2021"},
        {"id": "2008.12412", "title": "Topological Magnons in Kagome Lattice Ferromagnets", "authors": "Mook et al.", "year": "2020"},
        {"id": "2602.18023", "title": "Observer-Robust Energy Condition Verification for Warp Drive Spacetimes", "authors": "Le", "year": "2026"},
        {"id": "2102.06824", "title": "Introducing Physical Warp Drives", "authors": "Bobrick & Martire", "year": "2021"},
    ],
    "cooperative-resonance-torsion": [
        {"id": "1903.05468", "title": "Superradiance and Subradiance in Atomic Arrays", "authors": "Kirton et al.", "year": "2019"},
        {"id": "0810.0668", "title": "Torsion Gravity", "authors": "Hammond", "year": "2009"},
        {"id": "gr-qc/0606062", "title": "Einstein-Cartan Theory", "authors": "Hehl et al.", "year": "2006"},
        {"id": "2005.10828", "title": "Superradiance and Subradiance in an Ensemble of NV Centers", "authors": "Angerer et al.", "year": "2020"},
        {"id": "1907.03199", "title": "Collective Superradiance in Quantum Systems", "authors": "Gross et al.", "year": "2019"},
        {"id": "2011.10580", "title": "Dicke Superradiance in Solid-State Systems", "authors": "Parra-Murillo et al.", "year": "2020"},
        {"id": "1803.07643", "title": "Subradiance and Superradiance in Quantum Optics", "authors": "Asenjo-Garcia et al.", "year": "2018"},
        {"id": "2508.14666", "title": "Field Re-Entrant Superconductivity in Eu-Doped Infinite-Layer Nickelates", "authors": "Yang, Tang, Li et al.", "year": "2026"},
        {"id": "2601.19473", "title": "Paramagnetically Driven Superconducting Re-Entrance in Eu-Doped Infinite Layer Nickelates", "authors": "Varbaro et al.", "year": "2026"},
        {"id": "2102.06824", "title": "Introducing Physical Warp Drives", "authors": "Bobrick & Martire", "year": "2021"},
        {"id": "2006.07125", "title": "Breaking the Warp Barrier: Hyper-Fast Solitons in Einstein-Maxwell-Plasma Theory", "authors": "Lentz", "year": "2021"},
        {"id": "2512.18008", "title": "A Warp Drive with Predominantly Positive Invariant Energy Density", "authors": "Rodal", "year": "2025"},
        {"id": "2605.03653", "title": "Novel Realizations of Warp Drive Spacetimes as Solutions of General Relativity", "authors": "Buchert & Frackowiak", "year": "2026"},
    ],
    "warp-drive-torsion-propagation": [
        {"id": "gr-qc/0110086", "title": "Warp Drive With Zero Expansion", "authors": "Natário", "year": "2001"},
        {"id": "2102.06824", "title": "Introducing Physical Warp Drives", "authors": "Bobrick & Martire", "year": "2021"},
        {"id": "2006.07125", "title": "Breaking the Warp Barrier: Hyper-Fast Solitons in Einstein-Maxwell-Plasma Theory", "authors": "Lentz", "year": "2021"},
        {"id": "2512.18008", "title": "A Warp Drive with Predominantly Positive Invariant Energy Density", "authors": "Rodal", "year": "2025"},
        {"id": "2605.03653", "title": "Novel Realizations of Warp Drive Spacetimes as Solutions of General Relativity", "authors": "Buchert & Frackowiak", "year": "2026"},
        {"id": "2602.18023", "title": "Observer-Robust Energy Condition Verification for Warp Drive Spacetimes", "authors": "Le", "year": "2026"},
        {"id": "2605.20443", "title": "Interpreting Bohm Quantum Potentials: Computing Quantum Waves Exactly from Classical Action", "authors": "Lohmiller & Slotine", "year": "2026"},
    ],
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
    "warp-drive-torsion-propagation": ("Warp Drive: Torsion Bubble Propagation", "曲速引擎挠场气泡传播"),
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

def inject_glossary_tooltips(text):
    """Replace glossary terms with hover-tooltip spans."""
    # Sort by length descending so longer matches (like 'quantum-geometry') win over shorter ('quantum')
    sorted_terms = sorted(GLOSSARY.keys(), key=len, reverse=True)
    def replacer(m):
        term = m.group(0).lower().replace(' ', '-').replace("'", "").replace(",", "").replace(".", "")
        # Check all glossary keys
        for key in sorted_terms:
            if key in term or term in key:
                return f'<span class="glossary-term" data-tip="{GLOSSARY[key]}">{m.group(0)}</span>'
        return m.group(0)
    # Match standalone words (word boundaries)
    for key in sorted_terms:
        # Build pattern matching the key in multiple forms: exact, capitalized, dash-form
        display_forms = [key, key.replace('-', ' '), key.capitalize(), key.title()]
        for form in set(display_forms):
            if not form:
                continue
            escaped = re.escape(form)
            text = re.sub(r'\b' + escaped + r'\b', lambda m, k=key: f'<span class="glossary-term" data-tip="{GLOSSARY[k]}">{m.group(0)}</span>', text)
    return text

def md_to_html(md, slug):
    """Robust MD → HTML conversion for lore body content with glossary tooltips."""
    html = []
    in_code = False
    in_list = False
    for line in md.split('\n'):
        s = line.rstrip()
        # Skip YAML frontmatter lines completely
        if s == '---':
            continue
        
        # Code blocks
        if s.startswith('```'):
            if in_code:
                html.append('</code></pre>')
                in_code = False
            else:
                html.append('<pre><code>')
                in_code = True
            in_list = False
            continue
        if in_code:
            html.append(s)
            continue
        
        stripped = s.lstrip()
        
        # Headers
        if s.startswith('### '):
            if in_list:
                html.append('</ul>')
                in_list = False
            html.append(f'<h3>{s[4:]}</h3>')
        elif s.startswith('## '):
            if in_list:
                html.append('</ul>')
                in_list = False
            html.append(f'<h2>{s[3:]}</h2>')
        elif s.startswith('# '):
            if in_list:
                html.append('</ul>')
                in_list = False
            html.append(f'<h1>{s[2:]}</h1>')
        # Ordered list
        elif stripped and stripped[0].isdigit() and '. ' in stripped[:4]:
            if not in_list:
                html.append('<ol>')
                in_list = True
            content = stripped.split('. ', 1)[1] if '. ' in stripped else stripped
            content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
            content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)
            content = inject_glossary_tooltips(content)
            html.append(f'  <li>{content}</li>')
        # Unordered list
        elif stripped.startswith('- ') or stripped.startswith('* '):
            if not in_list:
                html.append('<ul>')
                in_list = True
            content = stripped[2:]
            content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
            content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)
            content = inject_glossary_tooltips(content)
            html.append(f'  <li>{content}</li>')
        # Empty line
        elif not s.strip():
            if in_list:
                html.append('</ul>')
                in_list = False
            html.append('')
        # Regular paragraph
        else:
            if in_list:
                html.append('</ul>')
                in_list = False
            s_processed = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
            s_processed = re.sub(r'\*(.+?)\*', r'<em>\1</em>', s_processed)
            s_processed = inject_glossary_tooltips(s_processed)
            html.append(f'<p>{s_processed}</p>')
    
    if in_list:
        html.append('</ul>')
    
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
                "about": ["Topological metamaterials", "Quantum gravity", "Einstein-Cartan theory"],
                "aggregateRating": {
                    "@type": "AggregateRating",
                    "ratingValue": "4.5",
                    "reviewCount": "12",
                    "bestRating": "5"
                },
                "offers": {
                    "@type": "Offer",
                    "price": "9.99",
                    "priceCurrency": "USD",
                    "availability": "https://schema.org/InStock",
                    "url": "https://www.amazon.com/Alien-Dimensions-Shepherds-Wasteland-Miancheng-ebook/dp/B0GTMLH634/"
                }
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
                "description": description[:300],
                "isPartOf": {
                    "@type": "Book",
                    "name": BOOK_TITLE,
                    "url": f"{SITE_URL}/"
                }
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
    
    # SEO-optimized meta descriptions per page
    SEO_DESCRIPTIONS = {
        "artificial-kondo-lattice": "Discover how Kondo lattice quantum simulation unlocks fault-tolerant qubits for next-gen computation in this hard sci-fi physics breakdown.",
        "floquet-temporal-matter": "Explore Floquet time crystals and how periodic driving fields create programmable matter — reality engineering meets condensed matter physics.",
        "semi-dirac-mass-nullification": "Can mass be canceled by topology? This article explores semi-Dirac fermion physics and the future of inertia reduction technology.",
        "qm-tether-exosuit": "A quantum metric exosuit that modifies spacetime curvature — the cutting edge of general relativity engineering in hard sci-fi.",
        "arena-tripartite-architecture": "How a computational arena bridges anyons, Majorana fermions, and topological qubits for reality-scale simulation architecture.",
        "obstructed-atomic-phantom-grid": "Radar stealth meets topological insulators. Learn how obstructed atomic phases enable electromagnetic cloaking at the atomic level.",
        "holographic-kpz-projection": "The KPZ equation meets holographic duality — simulating 3D reality from 2D boundary dynamics in this advanced physics concept.",
        "kpz-reality-rendering": "KPZ universality in polariton condensates: how random interface growth equations could programmatically render physical reality.",
        "type2-superlattice-radar": "Type-II superlattice infrared detection pushes beyond passive thermal sensing. The physics behind next-gen radar and imaging technology.",
        "electromagnetic-theater-override": "Kagome lattice magnets and topological spin currents enable macroscopic electromagnetic field override — from theory to application.",
        "cooperative-resonance-torsion": "Kagome torsion engine: superradiant mass repulsion via topological defect arrays. A practical path to Einstein-Cartan gravity manipulation.",
        "warp-drive-torsion-propagation": "Alcubierre drive reimagined: positive-energy warp bubbles via Einstein-Cartan torsion coupling. The physics of realistic warp travel.",
    }
    description = SEO_DESCRIPTIONS.get(slug, f"{en_title}: {zh_title} — explore the hard sci-fi physics behind this Shepherd's Wasteland technology.")

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
    refs = ARXIV_REFS.get(slug, [])
    if refs and not is_index:
        ref_cards = []
        for ref in refs:
            ref_cards.append(f'''<div class="ref-card">
                <div class="ref-title">{ref["title"]}</div>
                <div class="ref-meta">{ref["authors"]} ({ref["year"]})</div>
                <a href="https://arxiv.org/abs/{ref["id"]}" target="_blank" rel="noopener" class="ref-link">arXiv:{ref["id"]} →</a>
            </div>''')
        ref_grid = '\n'.join(ref_cards)
        further_reading = f'''
<div class="further-reading">
    <h3>Further Reading <span class="ref-count">({len(refs)} papers)</span></h3>
    <p>These real physics papers form the scientific foundation for this lore entry:</p>
    <div class="ref-grid">
        {ref_grid}
    </div>
    <img src="{ASSETS_URL}/bookcover.webp" alt="Shepherd&apos;s Wasteland — topological metamaterials and Reality-as-Code — the definitive hard sci-fi physics encyclopedia" class="lore-illustration" loading="lazy">
</div>'''
    else:
        further_reading = ''
    
    # ── Build HTML template with {placeholders} for safe substitution ──
    # (Using .replace() to avoid f-string { } conflict with JS/CSS)
    
    # CSS blocks (free of f-string escaping)
    base_css = '''
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0a0a0a; color: #e0e0e0; font-family: 'Georgia', 'Noto Serif SC', serif; line-height: 1.8; }
        .container { max-width: 960px; margin: 0 auto; padding: 20px; }
        header { border-bottom: 1px solid #1a3a1a; padding: 30px 0 20px; margin-bottom: 30px; }
        header h1 { color: #00FF41; font-size: 1.8em; font-family: 'Courier New', monospace; }
        header .subtitle { color: #666; font-size: 0.9em; margin-top: 5px; }
        header .author { color: #888; font-size: 0.85em; margin-top: 3px; }
        .layout { display: flex; gap: 30px; }
        .sidebar { width: 260px; flex-shrink: 0; position: sticky; top: 20px; align-self: flex-start; }
        .sidebar h3 { color: #00FF41; font-size: 0.85em; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 12px; border-bottom: 1px solid #1a3a1a; padding-bottom: 8px; }
        .sidebar ul { list-style: none; }
        .sidebar li { margin-bottom: 4px; }
        .sidebar a { color: #888; font-size: 0.85em; text-decoration: none; transition: color 0.2s; }
        .sidebar a:hover, .sidebar a.active { color: #00FF41; }
        .main { flex: 1; min-width: 0; }
        .main h1 { color: #00FF41; font-size: 1.6em; margin-bottom: 20px; border-left: 3px solid #00FF41; padding-left: 15px; }
        .main h2 { color: #ccc; font-size: 1.2em; margin: 25px 0 10px; }
        .main h3 { color: #aaa; font-size: 1.05em; margin: 20px 0 8px; }
        .main p { margin: 10px 0; color: #d0d0d0; font-size: 0.95em; }
        .main strong { color: #00FF41; }
        .main em { color: #aaa; }
        .main pre { background: #111; border: 1px solid #1a3a1a; padding: 12px; overflow-x: auto; font-size: 0.85em; color: #ccc; margin: 12px 0; }
        .main code { font-family: 'Courier New', monospace; }
        .back-home { display: inline-block; margin-top: 30px; color: #666; text-decoration: none; font-size: 0.85em; }
        .back-home:hover { color: #00FF41; }
        .further-reading { margin-top: 40px; padding-top: 20px; border-top: 1px solid #1a3a1a; }
        .further-reading h3 { color: #00FF41; font-size: 0.95em; margin-bottom: 8px; }
        .further-reading p { color: #666; font-size: 0.85em; margin-bottom: 12px; }
        .ref-card { background: #0d1a0d; border: 1px solid #1a3a1a; padding: 12px 15px; }
        .ref-title { color: #ccc; font-size: 0.9em; }
        .ref-meta { color: #666; font-size: 0.8em; margin: 4px 0 8px; }
        .ref-link { color: #00FF41; font-size: 0.85em; text-decoration: none; }
        .ref-link:hover { text-decoration: underline; }
        .lore-illustration { width: 100%; max-width: 600px; height: auto; margin-top: 15px; border: 1px solid #1a3a1a; }
        .glossary-term { color: #00FF41; cursor: help; border-bottom: 1px dashed #1a5a1a; position: relative; display: inline; }
        .glossary-term:hover::after { content: attr(data-tip); position: absolute; left: 0; bottom: calc(100% + 8px); background: #0d1a0d; color: #e0e0e0; border: 1px solid #00FF41; padding: 10px 14px; font-size: 0.8em; line-height: 1.5; width: 320px; max-width: 80vw; z-index: 100; white-space: normal; font-family: 'Georgia', 'Noto Serif SC', serif; box-shadow: 0 4px 20px rgba(0,255,65,0.15); pointer-events: none; }
        .ref-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; margin-bottom: 15px; }
        .ref-card { background: #0d1a0d; border: 1px solid #1a3a1a; padding: 12px 15px; transition: border-color 0.2s; }
        .ref-card:hover { border-color: #00FF41; }
        .ref-count { color: #666; font-size: 0.75em; font-weight: normal; }
        .toc { background: #0d1a0d; border: 1px solid #1a3a1a; padding: 15px 20px; margin-bottom: 25px; }
        .toc h3 { color: #00FF41; font-size: 0.85em; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 10px; }
        .toc a { display: block; color: #888; font-size: 0.85em; text-decoration: none; padding: 3px 0; transition: color 0.2s; }
        .toc a:hover { color: #00FF41; }
        .toc a::before { content: "\25b8 "; color: #1a5a1a; }
        .back-to-top { position: fixed; bottom: 30px; right: 30px; background: #0d1a0d; border: 1px solid #1a3a1a; color: #00FF41; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; text-decoration: none; font-size: 1.2em; opacity: 0; transition: opacity 0.3s; cursor: pointer; z-index: 50; }
        .back-to-top.visible { opacity: 0.8; }
        .back-to-top:hover { opacity: 1; border-color: #00FF41; }
        footer { border-top: 1px solid #1a3a1a; padding: 20px 0; margin-top: 50px; text-align: center; color: #444; font-size: 0.8em; }
        @media (max-width: 768px) { .layout { flex-direction: column; } .sidebar { width: 100%; position: relative; } }
    '''
    
    # JS blocks
    js_block = '''
    <script>
        (function() {
            var toc = document.getElementById('page-toc');
            if (!toc) return;
            var main = document.querySelector('.main');
            var headings = main.querySelectorAll('h2, h3');
            if (headings.length === 0) { toc.style.display = 'none'; return; }
            headings.forEach(function(h, i) {
                if (!h.id) h.id = 'sec-' + i;
                var a = document.createElement('a');
                a.href = '#' + h.id;
                a.textContent = h.textContent;
                a.style.marginLeft = h.tagName === 'H3' ? '15px' : '0';
                a.style.fontSize = h.tagName === 'H3' ? '0.8em' : '0.85em';
                toc.appendChild(a);
            });
        })();
        (function() {
            var btn = document.getElementById('back-to-top');
            if (!btn) return;
            window.addEventListener('scroll', function() {
                btn.classList.toggle('visible', window.scrollY > 300);
            });
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        })();
    </script>
    '''
    
    # Assemble HTML with string substitution
    html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>__TITLE__</title>
    <meta name="description" content="__DESC__">
    <meta name="keywords" content="Shepherd's Wasteland, __EN_TITLE__, __ZH_TITLE__, topological metamaterials, Kagome lattice, Reality-as-Code, hard sci-fi physics">
    <meta name="author" content="__AUTHOR__">
    <!-- Open Graph -->
    <meta property="og:type" content="article">
    <meta property="og:title" content="__TITLE__">
    <meta property="og:description" content="__DESC__">
    <meta property="og:url" content="__CANONICAL__">
    <meta property="og:site_name" content="Shepherd's Wasteland">
    <meta property="og:locale" content="en_US">
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="__TITLE__">
    <meta name="twitter:description" content="__DESC__">
    <!-- Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-ERCP39C12Y"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-ERCP39C12Y', {
        'page_title': '__TITLE__',
        'page_path': '__CANONICAL__'
      });
    </script>
    <!-- Favicon (inline SVG) -->
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><text y='28' font-size='28'>⧁</text></svg>">
    <link rel="canonical" href="__CANONICAL__">
    <script type="application/ld+json">__SCHEMA__</script>
    <style>__CSS__</style>
    __JS__
</head>
<body>
    <div class="container">
        <header>
            <h1>⟁ Shepherd's Wasteland</h1>
            <div class="subtitle">Reality-as-Code — Hard Sci-Fi Physics Encyclopedia</div>
            <div class="author">By __AUTHOR__</div>
        </header>
        <div class="layout">
            <nav class="sidebar">
                <h3>Technologies</h3>
                __SIDEBAR__
                <p style="margin-top:20px;"><a href="../index.html" style="color:#666;font-size:0.8em;">← Home</a></p>
            </nav>
            <main class="main">
                <!-- Table of Contents -->
                <div class="toc" id="page-toc">
                    <h3>In This Entry</h3>
                </div>
                __BODY__
                <!-- Further Reading -->
                __FURTHER__
                <a href="../index.html" class="back-home">← Back to Encyclopedia</a>
            </main>
        </div>
        <a href="#" class="back-to-top" id="back-to-top">↑</a>
        <footer>
            <p>© 2026 __AUTHOR__. Shepherd's Wasteland — Reality-as-Code Framework.</p>
            <p style="margin-top:3px;">Hard sci-fi physics grounded in topological metamaterials, Einstein-Cartan theory, and Kagome-lattice quantum engineering.</p>
            <div class="backlinks" style="margin-top:12px; display:flex; flex-wrap:wrap; gap:8px; justify-content:center;">
                <span style="color:#555; font-size:0.75em;">References: </span>
                <a href="https://arxiv.org/abs/2103.17114" style="color:#2a7a2a; font-size:0.75em; text-decoration:none;">Quantum Geometry (arXiv)</a>
                <a href="https://arxiv.org/abs/1907.00379" style="color:#2a7a2a; font-size:0.75em; text-decoration:none;">Kondo Lattice (arXiv)</a>
                <a href="https://arxiv.org/abs/2003.06883" style="color:#2a7a2a; font-size:0.75em; text-decoration:none;">Floquet Insulators (arXiv)</a>
                <a href="https://arxiv.org/abs/cond-mat/0411737" style="color:#2a7a2a; font-size:0.75em; text-decoration:none;">QSHE Graphene (arXiv)</a>
                <a href="https://arxiv.org/abs/1811.03116" style="color:#2a7a2a; font-size:0.75em; text-decoration:none;">Postquantum Gravity (arXiv)</a>
                <a href="https://www.nature.com/articles/s41467-021-22229-y" style="color:#2a7a2a; font-size:0.75em; text-decoration:none;">Nature Comms (Topological)</a>
                <a href="https://github.com/parkergenesis008-commits/wasteland-webengine" style="color:#2a7a2a; font-size:0.75em; text-decoration:none;">GitHub Repository</a>
            </div>
        </footer>
    </div>
</body>
</html>'''
    
    html_out = (html_template
        .replace('__TITLE__', title_text)
        .replace('__DESC__', description)
        .replace('__EN_TITLE__', en_title)
        .replace('__ZH_TITLE__', zh_title)
        .replace('__AUTHOR__', AUTHOR_NAME)
        .replace('__CANONICAL__', canonical_url)
        .replace('__SCHEMA__', schema_json)
        .replace('__CSS__', base_css)
        .replace('__JS__', js_block)
        .replace('__SIDEBAR__', sidebar)
        .replace('__BODY__', body_html)
        .replace('__FURTHER__', further_reading)
    )
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
    <!-- Google Search Console verification -->
    <meta name="google-site-verification" content="Fv0VnknT4HV64X5p3phBFitifk5WKSvRFb9XcdQdtII" />
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
    <!-- Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-ERCP39C12Y"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', 'G-ERCP39C12Y', {{
        'page_title': "Shepherd's Wasteland — Hard Sci-Fi Physics Encyclopedia",
        'page_path': '{SITE_URL}/'
      }});
    </script>
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
        .book-cover-img {{ width: 200px; height: auto; margin-bottom: 12px; border: 1px solid #1a3a1a; }}
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
            <img src="{ASSETS_URL}/bookcover.webp" alt="Alien Dimensions: The Shepherd&apos;s Wasteland - hard sci-fi novel by Miancheng Yu" class="book-cover-img" loading="lazy">
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
