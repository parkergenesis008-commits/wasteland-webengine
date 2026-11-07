#!/usr/bin/env python3
"""
Wasteland GEO Site Builder — v2
Multi-page site generator with rich structured data.
Converts 11 lore MD files into standalone HTML pages + sitemap + robots.txt.
"""
import json, os, re, hashlib, subprocess
from datetime import datetime

# 允许沙箱/回归检查用环境变量改根目录（不改仓库文件即可渲染到临时目录）
BASE_DIR = os.environ.get("WASTELAND_BASE_DIR") or os.path.expanduser("~/webengine")
LORES_DIR = os.path.join(BASE_DIR, "content/lore")
PAGES_DIR = os.path.join(BASE_DIR, "pages")
SITE_URL = "https://parkergenesis008-commits.github.io/wasteland-webengine"
ASSETS_URL = f"{SITE_URL}/assets"

# ── 页面模板（2026-11-07 模板并回）──────────────────────────────────────
# 线上定稿的 index/book/author/llms/robots 已抽成 pipeline/templates/*，
# 生成器只替换占位符，重新生成不会再回退到旧文案（"12 retailers"、$9.99 等）。
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(REPO_ROOT, "pipeline", "templates")

BOOK_PRICE = "4.99"
PRICE_LABEL = f"US${BOOK_PRICE}"
# 封面：Apple Books 官方 1200x1200 图（线上 OG/hero 一直在用这个源）
COVER_URL = ("https://is1-ssl.mzstatic.com/image/thumb/Publication221/v4/51/bd/94/"
             "51bd9468-a006-ecc7-e881-9d0f559ed182/0004166571.jpg/1200x1200wz.jpg")

# 渠道卡片显示名（BOOK_RETAILERS 里的 key → 页面上印的名字）
RETAILER_LABELS = {"Amazon": "Amazon Kindle", "Apple Books": "Apple Books"}

AUTHOR_NAME = "Miancheng Yu"
BOOK_TITLE = "Alien Dimensions: The Shepherd's Wasteland"

# ── Book metadata for the sales landing page [P0 2026-09-02 GEO推广改进] ──
AMAZON_URL = "https://www.amazon.com/dp/B0GTMLH634/"   # 短链；长 slug 同 ASIN，两个都 200
# 🍎 [2026-09-11] Apple Books 深链**换了 id**（旧 id6479860641 已 404）。
#   新 id 通过 Apple 官方检索 API 取回: itunes.apple.com/search?term=…&entity=ebook&country=US
#   → trackViewUrl = .../id6760573514。经海外出口实测 200 且页面含书名+作者。
#   ⚠️ 直连（中国 IP）对该域返回 404 = Apple 地域拒绝，不代表链接失效。
APPLE_BOOKS_URL = "https://books.apple.com/us/book/alien-dimensions-the-shepherds-wasteland/id6760573514"
# 📖 Everand（Scribd）深链，实测可用（原为搜索页，2026-09-11 升级）
EVERAND_URL = "https://www.everand.com/book/1012259893/Alien-Dimensions-The-Shepherd-s-Wasteland"

BOOK_HOOK = ("A geological surveyor in the Qinling Mountains stumbles onto a rift in spacetime — "
             "and into a war between civilizations that treat reality as source code. Hard sci-fi "
             "where every speculative technology is anchored in real condensed-matter physics.")

BOOK_CHAPTERS = [
    ("Volume I", "The Collapse of Flesh", ["The Singularity Descends", "The Lunar Slaughterhouse", "The Last Supper"]),
    ("Volume II", "The Law of the Dark Forest", ["The Dirty Trade in Orion", "The Anchor of the Pyramid", "The Betrayal of the Void", "The Shattered Sky"]),
    ("Volume III", "The Price of Divinity", ["The Dead Knot of Time Lines", "The Gentlest Cruelty", "Succession of Divine Power"]),
    ("Volume IV", "The Shepherd's Wasteland", ["The Shepherd's Wasteland", "The Silent Clamor"]),
]

# Real opening of Chapter 1, extracted from the manuscript — used as the free sample hook
BOOK_SAMPLE = (
    "The deep autumn wind of the Qinling Mountains carried a scent like ground rust as it squeezed "
    "forcibly through the fissures of Ghost Sorrow Canyon, stinging the skin like a blade. Lin Shen "
    "wiped a sheen of sweat from his forehead. The salty liquid ran down his brow bone and into his "
    "eyes, stinging with a fiery burn. Squinting against the damnable afterglow of the setting sun, "
    "he adjusted the heavy 3D laser scanner set up before him. "
    "\u201cLin, are you done gathering yet?\u201d Captain Zhang\u2019s gritty voice crackled over the "
    "walkie-talkie, mixed with the static hiss of current, sounding like someone chewing on gravel. "
    "\u201cIt\u2019s getting dark. That place is cursed; even the local hunters don\u2019t dare stay "
    "there overnight. Pull out, now.\u201d "
    "\u201cLast set of point cloud data. Five minutes,\u201d Lin Shen pressed the talk button and replied. "
    "As a contractor for the Provincial Surveying and Mapping Institute, Lin Shen\u2019s job was "
    "monotonous and dry: carrying equipment weighing over fifty pounds, climbing every fold of the "
    "Qinling Mountains like a goat, all to fill in the final few blank spots for the government\u2019s "
    "\u201cDigital Qinling\u201d project. The place he stood now had no name on the map; the coordinates "
    "simply displayed \u201cUnnamed Valley.\u201d The vegetation here was tinted an uncomfortable shade "
    "of deep purple. It was quiet\u2014too quiet. There was not even the chirping of insects, only the "
    "whistling sound of the wind passing through dead tree branches."
)

# ── Retailer availability ────────────────────────────────────────────────
# 🛒 [2026-09-11 全量核查] 逐链实测（HTTP 状态 + 页面是否真含书名/作者）后重写本清单。
#   保留（全部实测含本书）:
#     · Amazon          深链 200，title 命中 "Alien Dimensions…Miancheng" ✅
#     · Everand         深链 200，命中书名+作者（搜索页→深链，体验更好）✅
#     · Google Play     搜索页 200，结果含本书 ✅（新增）
#     · OverDrive       搜索页 200，页面显示 "1 results for alien dimensions shepherd" ✅
#     · Hoopla          搜索页 200，含书名 ✅
#   删除（实测失效，避免"点开是空/找不到书"）:
#     · Apple Books     深链 **404**（id 已失效）
#     · Barnes & Noble  搜索页 **404**
#     · Vivlio          搜索页 **404**
#     · Smashwords      搜索页 **302→登录页**（访客看不到结果）
#     · Kobo            403 + 站内检索无本书收录
#     · Bookshop.org    Cloudflare 拦截 + 无收录
#     · Tolino          HTTP 500 且原链接只是商店首页（非本书页面）
#     · Fable           200 但为纯 JS 壳，页面无本书信息
#   复核脚本与原始输出: ~/Downloads/bookstore_link_audit_2026-09-11.md
BOOK_RETAILERS = [
    # 2026-11-06: 只保留两个自营渠道（Amazon 直链 + Apple Books 直链，$4.99）
    ("Amazon", AMAZON_URL),
    ("Apple Books", APPLE_BOOKS_URL),
]
# Distributor-submitted library channels (read via local library apps):
BOOK_LIBRARY_CHANNELS = ""
LIB_NOTE_HTML = ('<div class="lib-note">' + BOOK_LIBRARY_CHANNELS + '</div>') if BOOK_LIBRARY_CHANNELS else ''

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
    "artificial-kondo-lattice": ("Artificial Kondo Lattice", ""),
    "floquet-temporal-matter": ("Floquet Temporal Matter", ""),
    "semi-dirac-mass-nullification": ("Semi-Dirac Mass Nullification", ""),
    "qm-tether-exosuit": ("QM-Tether Exosuit", ""),
    "arena-tripartite-architecture": ("Arena Tripartite Architecture", ""),
    "obstructed-atomic-phantom-grid": ("Obstructed Atomic Phantom Grid", ""),
    "holographic-kpz-projection": ("Holographic KPZ Projection", ""),
    "kpz-reality-rendering": ("KPZ Reality Rendering", ""),
    "type2-superlattice-radar": ("Type-II Superlattice Radar", ""),
    "electromagnetic-theater-override": ("Electromagnetic Theater Override", ""),
    "cooperative-resonance-torsion": ("Cooperative Resonance Torsion", ""),
    "warp-drive-torsion-propagation": ("Warp Drive: Torsion Bubble Propagation", ""),
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

# ── glossary 单趟替换的编译缓存（2026-09-18）──
_GLOSSARY_PAT = None
_GLOSSARY_FORMS = None


def inject_glossary_tooltips(text):
    """Replace glossary terms with hover-tooltip spans.

    2026-09-18 修复（原实现的两个真实缺陷）:
      1. 原实现对**整段 HTML** 做 re.sub，逐词循环时会把后续术语注入到刚生成的
         data-tip="..." 属性值内部 —— 因为 GLOSSARY 的释义文本里本身就含其它术语词
         （如 polariton 的释义里有 "exciton"）。结果产出
         `data-tip="...<span class="glossary-term" ...>` 这种畸形嵌套：属性被内层引号
         提前截断，HTML 非法。
      2. 由此构建**非幂等**：每次部署 13 个页面的这些行都要重写一遍（+/- 数相同），
         页面内容在两种形态之间来回震荡。
    现改为只在"标签之外的文本节点"里替换，并跳过已处于 glossary span 内的文本，
    保证输出合法且重复构建结果稳定。
    """
    sorted_terms = sorted(GLOSSARY.keys(), key=len, reverse=True)
    if not sorted_terms or not text:
        return text

    # 单趟替换：所有术语合成一条 alternation（长词优先），一次 re.sub 完成。
    # 关键点：绝不能在循环里对"已插入的标记"再跑正则——否则后一个术语会落进
    # 前一个术语 data-tip 的属性值里，产生畸形嵌套（本文件 2026-09-18 的根因）。
    global _GLOSSARY_PAT, _GLOSSARY_FORMS
    if _GLOSSARY_PAT is None:
        forms = {}
        for key in sorted_terms:
            for form in {key, key.replace('-', ' '), key.capitalize(), key.title()}:
                if form:
                    forms.setdefault(form, key)
        ordered = sorted(forms, key=len, reverse=True)
        _GLOSSARY_PAT = re.compile(r'\b(?:' + '|'.join(re.escape(f) for f in ordered) + r')\b')
        _GLOSSARY_FORMS = forms

    def wrap_segment(seg):
        return _GLOSSARY_PAT.sub(
            lambda m: (
                f'<span class="glossary-term" data-tip="{GLOSSARY[_GLOSSARY_FORMS[m.group(0)]]}">'
                f'{m.group(0)}</span>'
            ),
            seg,
        )

    # 按标签切分：tag 原样透传，只有标签外的文本参与替换。
    parts = re.split(r'(<[^>]*>)', text)
    out, depth = [], 0
    for part in parts:
        if part.startswith('<') and part.endswith('>'):
            if 'class="glossary-term"' in part:
                depth += 1
            elif part.startswith('</span>') and depth > 0:
                depth -= 1
            out.append(part)
        else:
            out.append(part if depth > 0 else wrap_segment(part))
    return ''.join(out)

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

_QA_SCHEMA_CACHE = None


def _qa_faq_nodes(slug):
    """🎯 [2026-09-10 激进模式] 把当日注入的「延伸问答」暴露成 FAQPage 结构化数据。
    数据源: content/geo_hot_questions/qa_schema.json (由 pipeline/geo_qa_inject.py 生成)"""
    global _QA_SCHEMA_CACHE
    try:
        if _QA_SCHEMA_CACHE is None:
            p = os.path.join(BASE_DIR, "content/geo_hot_questions/qa_schema.json")
            if os.path.exists(p):
                with open(p, encoding="utf-8") as f:
                    _QA_SCHEMA_CACHE = json.load(f)
            else:
                _QA_SCHEMA_CACHE = {}
        items = _QA_SCHEMA_CACHE.get(slug) or []
        entities = [{"@type": "Question", "name": it.get("q", ""),
                     "acceptedAnswer": {"@type": "Answer", "text": it.get("a", "")}}
                    for it in items if it.get("q") and it.get("a")]
        if not entities:
            return []
        return [{"@type": "FAQPage", "mainEntity": entities}]
    except Exception:
        return []


def build_schema_graph(slug, en_title, zh_title, description):
    """Generate rich multi-entity JSON-LD."""
    return {
        "@context": "https://schema.org",
        "@graph": [
            *_qa_faq_nodes(slug),
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
                "offers": {
                    "@type": "Offer",
                    "price": "4.99",
                    "priceCurrency": "USD",
                    "availability": "https://schema.org/InStock",
                    "url": "https://www.amazon.com/Alien-Dimensions-Shepherds-Wasteland-Miancheng-ebook/dp/B0GTMLH634/"
                }
            },
            {
                "@type": "Person",
                "name": AUTHOR_NAME,
                "url": f"{SITE_URL}/book.html",
                "sameAs": [url for _, url in BOOK_RETAILERS[:10]],
                "description": "Author of Alien Dimensions: The Shepherd's Wasteland — a hard sci-fi novel built on the Reality-as-Code physics framework (topological metamaterials, Einstein-Cartan torsion, Kagome-lattice engineering)."
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
    zh_title = en_title  # 🌐 [2026-08-20] 全站英文化：强制中文标题回退为英文
    md_body = read_md(os.path.join(LORES_DIR, f"{slug}.md"))
    # Skip YAML frontmatter
    md_lines = md_body.split('\n')
    if md_lines and md_lines[0].strip() == '---':
        for i in range(1, len(md_lines)):
            if md_lines[i].strip() == '---':
                md_body = '\n'.join(md_lines[i+1:])
                break
    
    body_html = md_to_html(md_body, slug)

    # 正文首段后注入书页内链(2026-09-09:文章页 → book.html 购买/阅读锚点,强化内链权重)
    if not is_index and not slug.startswith('book'):
        fp = body_html.find('</p>')
        if fp != -1:
            intext = (f'<p class="body-link"><a href="book.html" class="intext">📖 Read this concept in '
                      f'<em>{BOOK_TITLE}</em></a> — the hard sci-fi novel where this physics becomes story.</p>')
            body_html = body_html[:fp + 4] + intext + body_html[fp + 4:]
    
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
            nav_html += f'<a href="pages/{s}.html" class="nav-item">{en}</a>'
        nav_html += '</div>'
    else:
        related = []
        for s, (en, zh) in LORE_TITLES.items():
            if s != slug:
                related.append(f'<a href="{s}.html">{en}</a>')
        nav_html = ' | '.join(related[:5])

    # Schema
    schema = build_schema_graph(slug, en_title, zh_title, description)
    schema_json = json.dumps(schema, ensure_ascii=False, indent=2)

    # Hook 标题(2026-09-09 GEO:关键词开头 + 信息缺口悬念,单独成 title)
    HOOK_TITLES = {
        "artificial-kondo-lattice": "Can Kondo lattice simulation unlock fault-tolerant qubits?",
        "floquet-temporal-matter": "Floquet time crystals: how light makes matter programmable",
        "semi-dirac-mass-nullification": "Can topology cancel mass? The semi-Dirac path to inertia reduction",
        "qm-tether-exosuit": "Quantum metric exosuit: engineering geometry that bends spacetime",
        "arena-tripartite-architecture": "Anyons + Majorana qubits: the reality-scale computational arena",
        "obstructed-atomic-phantom-grid": "Atomic-level radar stealth: obstructed atomic phases explained",
        "holographic-kpz-projection": "Is 3D reality projected from a 2D boundary? KPZ + holography",
        "kpz-reality-rendering": "When growth equations render reality: KPZ universality decoded",
        "type2-superlattice-radar": "Type-II superlattices: physics of next-generation IR radar",
        "electromagnetic-theater-override": "Kagome magnets: engineering a macroscopic EM field override",
        "cooperative-resonance-torsion": "Kagome torsion engine: superradiant mass repulsion in practice",
        "warp-drive-torsion-propagation": "Einstein-Cartan warp drive: real travel via positive-energy bubbles",
    }
    hook = HOOK_TITLES.get(slug)
    title_text = ("Shepherd's Wasteland — Hard Sci-Fi Physics Encyclopedia" if is_index
                  else (hook or f"{en_title}") )
    page_path = "index.html" if is_index else f"pages/{slug}.html"
    canonical_url = f"{SITE_URL}/{page_path}"

    # Build inter-page nav
    if is_index:
        sidebar = nav_html
    else:
        sidebar_parts = []
        for s, (en, zh) in LORE_TITLES.items():
            cls = 'active' if s == slug else ''
            sidebar_parts.append(f'<li><a href="{s}.html" class="{cls}">{en}</a></li>')
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

def render_template(name, **kw):
    """Render pipeline/templates/<name> by replacing {{PLACEHOLDER}} tokens.

    模板里只允许出现纯占位符；渲染后若残留 {{XXX}} 直接报错（防止静默输出坏页面）。
    """
    path = os.path.join(TEMPLATES_DIR, name)
    with open(path, encoding="utf-8") as f:
        tpl = f.read()
    values = {
        "SITE_URL": SITE_URL,
        "ASSETS_URL": ASSETS_URL,
        "BOOK_TITLE": BOOK_TITLE,
        "AUTHOR_NAME": AUTHOR_NAME,
        "BOOK_HOOK": BOOK_HOOK,
        "COVER_URL": COVER_URL,
        "PRICE": BOOK_PRICE,
        "PRICE_LABEL": PRICE_LABEL,
        "AMAZON_URL": AMAZON_URL,
        "APPLE_BOOKS_URL": APPLE_BOOKS_URL,
    }
    values.update(kw)
    for k, v in values.items():
        tpl = tpl.replace("{{%s}}" % k, v)
    leftover = re.findall(r"\{\{[A-Z0-9_]+\}\}", tpl)
    if leftover:
        raise RuntimeError(f"{name}: unrendered placeholders {sorted(set(leftover))}")
    if "{{" in tpl:
        raise RuntimeError(f"{name}: stray '{{{{' left in output")
    return tpl


def build_book_page():
    """Book sales landing page — 正文全部来自 pipeline/templates/book.html。

    [2026-11-07] 旧版函数里内联的文案是 9 月版本（12 retailers / 无 FAQ / $9.99 残留），
    与线上定稿页差 148 行，直接跑会把新内容覆盖掉。现在模板 = 线上定稿页，
    动态部分只剩章节列表、渠道卡片、样章三段和占位符。
    """
    chapters_html = []
    for vol, vol_title, chs in BOOK_CHAPTERS:
        ch_items = "".join(f"<li>{c}</li>" for c in chs)
        chapters_html.append(
            f'<div class="vol"><div class="vol-head">{vol}: {vol_title}</div><ul>{ch_items}</ul></div>'
        )
    chapters_block = "\n".join(chapters_html)

    retailer_cells = []
    for name, url in BOOK_RETAILERS:
        label = RETAILER_LABELS.get(name, name)
        retailer_cells.append(
            f'            <a href="{url}" class="retailer" rel="noopener" target="_blank">{label}'
            f'<span class="tag">{PRICE_LABEL}</span></a>'
        )
    retailers_block = "\n".join(retailer_cells)

    sentences = BOOK_SAMPLE.replace("\n", " ").split(". ")
    para1 = ". ".join(sentences[:3]) + "."
    para2 = ". ".join(sentences[3:7]) + "."
    para3 = ". ".join(sentences[7:])

    return render_template(
        "book.html",
        CHAPTERS=chapters_block,
        RETAILER_CARDS=retailers_block,
        SAMPLE_P1=para1,
        SAMPLE_P2=para2,
        SAMPLE_P3=para3,
    )


def frontmatter_title(md):
    """YAML frontmatter 的 title（长标题），用于 llms.txt 与首页卡片副标题。"""
    m = re.match(r"^---\n(.*?)\n---\n", md, flags=re.S)
    if not m:
        return ""
    for line in m.group(1).split("\n"):
        if line.startswith("title:"):
            return line.split(":", 1)[1].strip()
    return ""


def first_body_paragraph(md, limit=200):
    """正文小节首段（跳过 frontmatter/标题/列表），用于首页卡片摘要。

    2026-11-07 修复：旧实现取 md_to_html() 的首个 <p>，命中的是 frontmatter 的
    "title: ..." 行 —— 线上首页 12 张卡片摘要全是 "title: XXX"，不是正文。
    这里按"紧跟在 heading 后面的第一段散文"取，读起来才是导语；
    注意 lore 正文里标题与正文常无空行分隔，必须逐行处理而不是按空行切块。
    """
    body = re.sub(r"^---\n.*?\n---\n", "", md, count=1, flags=re.S)
    buf, after_heading, intro, fallback = [], False, None, None
    def flush():
        nonlocal buf, after_heading, intro, fallback
        para = " ".join(buf).strip()
        buf = []
        if not para:
            after_heading = False
            return
        if after_heading and len(para) >= 60 and intro is None:
            intro = para
        if fallback is None and len(para) >= 60:
            fallback = para
        after_heading = False
    for line in body.split("\n"):
        st = line.strip()
        if not st:
            flush()
        elif st.startswith("#"):
            flush()
            after_heading = True
        elif st.startswith(("- ", "* ", "|", ">", "![", "```")):
            flush()
        else:
            buf.append(st)
    flush()
    para = intro or fallback or ""
    para = re.sub(r"\*\*(.+?)\*\*", r"\1", para)
    para = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", para)
    para = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", para)
    para = re.sub(r"\s+", " ", para).strip()
    if len(para) > limit:
        para = para[:limit].rsplit(" ", 1)[0] + "…"
    return para


def build_index_page(all_slugs):
    """Homepage — 版式/文案来自 pipeline/templates/index.html，卡片由 lore 生成。"""
    cards = []
    for slug in sorted(all_slugs):
        en_title, _zh = LORE_TITLES[slug]
        md_body = read_md(os.path.join(LORES_DIR, f"{slug}.md"))
        long_title = frontmatter_title(md_body) or en_title
        excerpt = first_body_paragraph(md_body)
        en_line = (f'\n            <div class="card-en">{long_title}</div>'
                   if long_title != en_title else "")
        cards.append(f'''
        <a href="pages/{slug}.html" class="card">
            <h2>{en_title}</h2>{en_line}
            <p>{excerpt}</p>
            <span class="card-tag">Topological Physics</span>
        </a>''')
    return render_template("index.html", CARDS="\n".join(cards))


def build_author_page():
    """Author page — 2026-11-06 定稿版，模板化后不再依赖手工维护。"""
    return render_template("author.html")


def build_llms(all_slugs):
    """llms.txt（LLM 抓取入口）：书/作者 + 全部百科条目，条目列表由 lore 生成。"""
    lines = []
    for slug in sorted(all_slugs):
        md = read_md(os.path.join(LORES_DIR, f"{slug}.md"))
        title = frontmatter_title(md) or LORE_TITLES[slug][0]
        lines.append(f"- [{title}]({SITE_URL}/pages/{slug}.html)")
    return render_template("llms.txt", ENTRIES="\n".join(lines))


def git_lastmod(rel_path):
    """该文件"内容最后一次真正变化"的日期（YYYY-MM-DD），用于 sitemap <lastmod>。

    2026-09-18: 原 sitemap 完全没有 <lastmod>，爬虫拿不到任何新鲜度信号；
    而每日重复推送同一批 URL 也无法表达"哪页变了"。
    这里取 git 的最后一个触及该文件的提交日期；若文件当前有未提交改动（=本轮正要发布的变更），
    则记今天。注意：<lastmod> 只有在"确实准确"时才被 Google 采信，所以绝不无脑写今天。
    """
    try:
        dirty = subprocess.run(["git", "status", "--porcelain", "--", rel_path],
                               cwd=REPO_ROOT, capture_output=True, text=True, timeout=15)
        if dirty.stdout.strip():
            return datetime.now().strftime("%Y-%m-%d")
        out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", rel_path],
                             cwd=REPO_ROOT, capture_output=True, text=True, timeout=15)
        d = out.stdout.strip()
        return d if re.match(r"^\d{4}-\d{2}-\d{2}$", d or "") else None
    except Exception:
        return None


def _url_entry(loc, changefreq, priority, rel_path):
    lastmod = git_lastmod(rel_path)
    lm = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
    return (f"  <url><loc>{loc}</loc>{lm}"
            f"<changefreq>{changefreq}</changefreq><priority>{priority}</priority></url>")


def build_sitemap(all_slugs):
    """Generate sitemap.xml covering all pages（含准确 lastmod）。"""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    lines.append(_url_entry(f"{SITE_URL}/", "weekly", "1.0", "index.html"))
    lines.append(_url_entry(f"{SITE_URL}/book.html", "weekly", "0.9", "book.html"))
    for slug in all_slugs:
        lines.append(_url_entry(f"{SITE_URL}/pages/{slug}.html", "monthly", "0.8",
                                f"pages/{slug}.html"))
    lines.append(_url_entry(f"{SITE_URL}/author.html", "monthly", "0.7", "author.html"))
    lines.append('</urlset>')
    return '\n'.join(lines)

def build_robots():
    """robots.txt — 模板含 AI 爬虫白名单与 Pages 项目站说明。"""
    return render_template("robots.txt")


def main():
    os.makedirs(PAGES_DIR, exist_ok=True)
    
    all_slugs = list(LORE_TITLES.keys())
    
    # Build index
    index_html = build_index_page(all_slugs)
    with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)
    print(f"[OK] index.html ({len(index_html)} chars)")

    # Build book sales landing page [P0 2026-09-02]
    book_html = build_book_page()
    with open(os.path.join(BASE_DIR, "book.html"), "w", encoding="utf-8") as f:
        f.write(book_html)
    print(f"[OK] book.html ({len(book_html)} chars)")
    
    # Build lore pages
    for slug in all_slugs:
        en_title, zh_title = LORE_TITLES[slug]
        md_content = read_md(os.path.join(LORES_DIR, f"{slug}.md"))
        page_html = build_page_html(slug, en_title, zh_title, md_content, all_slugs, is_index=False)
        out_path = os.path.join(PAGES_DIR, f"{slug}.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(page_html)
        print(f"[OK] pages/{slug}.html ({len(page_html)} chars)")
    
    # Author page（2026-11-06 定稿，模板化）
    author_html = build_author_page()
    with open(os.path.join(BASE_DIR, "author.html"), "w", encoding="utf-8") as f:
        f.write(author_html)
    print(f"[OK] author.html ({len(author_html)} chars)")

    # llms.txt（LLM 抓取入口）
    llms_txt = build_llms(all_slugs)
    with open(os.path.join(BASE_DIR, "llms.txt"), "w", encoding="utf-8") as f:
        f.write(llms_txt)
    print(f"[OK] llms.txt ({len(llms_txt)} chars)")

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
    
    total = 2 + len(all_slugs)
    print(f"\n✅ Build complete: {total} HTML pages + sitemap + robots.txt + llms.txt")
    print(f"Pages generated: {total}")

if __name__ == "__main__":
    main()
