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

# 渠道价格会随地区/促销浮动（2026-11-07 实测 Apple $4.99 / Amazon $4.90）
PRICE_NOTE = "Retailer prices may vary by region and promotion."
SAMPLE_NOTE = "The first ~{n} words of Chapter 1 — an excerpt, not the full chapter."

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

# ── 三层口径声明：真实研究 / 作者推演 / 小说设定（2026-11-07 可信度改造）──
# 目的：读者和 AI 都不要把世界设定当已验证技术。每条按该页实际引用写，
# 不允许出现"已实现/已验证/零误差"这类越界表述。
PAGE_SCOPE = {
    "artificial-kondo-lattice": {
        "real": "Kondo physics, Kondo insulators and artificial Kondo lattices are experimentally studied systems; topological zero modes appear in specific lattice models (see the papers below).",
        "extra": "Engineering a usable qubit or anyon host out of cheap 3d metals arranged in 1D chains is a proposal, not a demonstrated platform.",
        "fiction": "Zero-error computation, survival inside a stellar core, and the specific threshold numbers are story parameters.",
    },
    "floquet-temporal-matter": {
        "real": "Floquet engineering — driving a system periodically to create phases with no static counterpart — is established in cold atoms, photonics and several solids.",
        "extra": "Using that drive to synthesise bulk 'programmable matter' at ambient conditions is not demonstrated; heating, lifetime and stability remain open problems.",
        "fiction": "Agents that retune matter by projecting rhythms, and picosecond armour reshuffling, are setting.",
    },
    "semi-dirac-mass-nullification": {
        "real": "Dirac and semi-Dirac dispersions are real band structures: the effective mass m* can vanish along one momentum axis in a handful of materials.",
        "extra": "Coupling that band-structure quantity to macroscopic inertial mass has no experimental support.",
        "fiction": "Mass nullification for ships and armour is fiction; §2 of this page states the effective-versus-inertial distinction explicitly.",
    },
    "qm-tether-exosuit": {
        "real": "The quantum metric (Fubini–Study) and spin–orbit coupling at oxide interfaces are measured physics.",
        "extra": "The chain quantum metric → spin current → torsion → metric perturbation is separately motivated but has never been demonstrated end-to-end; for a lab-scale device the effect is ~10⁻⁶⁰.",
        "fiction": "Exosuits that redirect gravity, and their catastrophic failure modes, are setting.",
    },
    "arena-tripartite-architecture": {
        "real": "Anyons, braiding, Majorana modes and high-dimensional orbital-angular-momentum entanglement are active research areas.",
        "extra": "A single machine combining an anyonic core, a 48-dimensional OAM bus and a gravity engine does not exist and has no engineering path in the literature.",
        "fiction": "The million-agent arena, the 17,000 eigenvalues and the tripartite architecture itself are worldbuilding.",
    },
    "obstructed-atomic-phantom-grid": {
        "real": "Obstructed atomic insulators and symmetry indicators are established results of topological quantum chemistry, observed in materials including some electrides.",
        "extra": "Suspending a working power grid in the interstices so it survives the armour being destroyed is not a demonstrated device.",
        "fiction": "Phantom grids and dimensional-bias weapons are setting.",
    },
    "holographic-kpz-projection": {
        "real": "The KPZ equation and the holographic (AdS/CFT) correspondence are each real, well-tested bodies of work.",
        "extra": "There is no established mapping that renders 3D matter from a 2D KPZ boundary; the 'holographic rendering' step is invented for the novel.",
        "fiction": "Reality rendered from boundary code, and its 'hollow shell' weakness, are story.",
    },
    "kpz-reality-rendering": {
        "real": "KPZ universality is measured in interface growth, bacterial colonies, liquid-crystal fronts and polariton condensates.",
        "extra": "Growing macroscopic objects by injecting KPZ parameters is not a physical protocol; the equation describes statistics of growth, not a construction kit.",
        "fiction": "Noise-injection attacks and picosecond disintegration are setting.",
    },
    "type2-superlattice-radar": {
        "real": "Type-II InAs/GaSb superlattices are real infrared detector materials; Auger suppression is a real design goal.",
        "extra": "Reading a distant mass through vacuum-fluctuation tunnelling is many orders of magnitude beyond demonstrated detector sensitivity.",
        "fiction": "Scale-free perception and the efficiency figures once quoted on this page are setting.",
    },
    "electromagnetic-theater-override": {
        "real": "Macroscopic contact is electromagnetic repulsion constrained by Pauli exclusion — textbook physics; Kagome magnets are real materials.",
        "extra": "Locally cancelling that repulsion with a torsion field has never been observed in any experiment.",
        "fiction": "Phasing through matter and 'collision mesh' rewrites are setting.",
    },
    "cooperative-resonance-torsion": {
        "real": "Superradiance and subradiance in NV ensembles and atomic arrays are measured; Einstein–Cartan torsion is a real, untested extension of general relativity.",
        "extra": "The N²-amplified spin → torsion → metric chain falls short of any detectable signal by roughly thirty orders of magnitude (see §4.5).",
        "fiction": "Baryonic torsion engines and mass repulsion are setting.",
    },
    "warp-drive-torsion-propagation": {
        "real": "Alcubierre's metric and the positive-energy variants (Bobrick–Martire, Lentz, Rodal) are peer-reviewed results in general relativity.",
        "extra": "No laboratory realisation exists, and the Kagome-torsion generator's energy budget is short by tens of orders of magnitude.",
        "fiction": "Warp bubbles as a communication protocol, and the δg ~ 10⁻⁶ target, are story.",
    },
}

SCOPE_NOTE = ("This companion guide connects real research with fictional worldbuilding. "
              "Mass nullification and torsion-based warp systems are speculative inventions, "
              "not demonstrated engineering.")

# ── 每页 2 条问答：按本页真实物理撰写，替代此前从 StackExchange 热度池抓取的问答 ──
PAGE_FAQ = {
    "artificial-kondo-lattice": [
        ("Why does the novel build its logic core from iron and cobalt instead of rare-earth topological insulators?",
         "Because the lesson of artificial Kondo lattices is that topology can be engineered from ordinary 3d magnetic moments arranged on a lattice, rather than inherited from an expensive compound. The novel takes that as permission to assemble cores from scrap metal; the actual qubit performance of such a lattice is unmeasured."),
        ("Does an artificial Kondo lattice really compute with zero errors?",
         "No. What exists is Kondo screening and topological zero modes in specific models and nanostructures. Fault-tolerance figures quoted for non-Abelian anyons (order 10⁻¹² per operation) are targets, not a measured error rate, and the 'zero-error' claim belongs to the story."),
    ],
    "floquet-temporal-matter": [
        ("What does 'Floquet engineering' actually mean?",
         "Driving a system with a periodic field so that its effective behaviour follows a synthetic Hamiltonian with no static counterpart. It has been demonstrated in cold atoms, photonic lattices and several solids."),
        ("Is Floquet 'synthetic matter' stable enough to use as armour?",
         "No. Driven phases need continuous power, heat up, and decay once the drive stops — which is precisely the vulnerability the novel uses in its own chapter on the metronome hijack."),
    ],
    "semi-dirac-mass-nullification": [
        ("If an electron's effective mass goes to zero in a Dirac cone, does the object become lighter?",
         "No. Effective mass is a band-structure quantity — the curvature of the dispersion E(k). The electron's rest mass and the object's inertial mass are untouched; this page states the distinction explicitly in §2."),
        ("What is semi-Dirac dispersion?",
         "A hybrid: linear (massless-like) along one momentum direction and quadratic along the perpendicular one, observed in a small number of materials. It is a property of quasiparticles inside a crystal, not a switch for spacecraft inertia."),
    ],
    "qm-tether-exosuit": [
        ("How is the 'quantum metric' different from spacetime curvature?",
         "The quantum metric is the Fubini–Study metric of Bloch wavefunctions in momentum space — a band-geometry object. It is not the spacetime metric; §1 of this page flags the distinction before using the phrase."),
        ("Could that coupling chain really produce a measurable gravitational effect?",
         "Each link (quantum metric → spin current → torsion → metric perturbation) is separately motivated, but the combined effect for a lab-scale device is ~10⁻⁶⁰. The N² amplification invoked to close the gap has never been demonstrated."),
    ],
    "arena-tripartite-architecture": [
        ("What are anyons, in one paragraph?",
         "Quasiparticles in two dimensions (or effectively one) whose exchange is neither bosonic nor fermionic. Braiding them implements topologically protected operations, which is the basis of topological quantum computation."),
        ("Does the 48-dimensional OAM bus correspond to a real communication scheme?",
         "High-dimensional orbital-angular-momentum entanglement is real and has been used in qudit protocols, but '48 dimensions carrying 17,000 eigenvalues' is a story number — no such bus exists."),
    ],
    "obstructed-atomic-phantom-grid": [
        ("What is an obstructed atomic insulator?",
         "A band insulator whose Wannier charge centres sit at empty positions rather than on atoms, forced by symmetry. It is a result of topological quantum chemistry, observed in materials including some electrides."),
        ("Can a circuit keep working after its atoms are destroyed?",
         "No. The 'phantom grid' is fiction: a real electronic state is still hosted by the lattice, so pulverising the lattice destroys the state."),
    ],
    "holographic-kpz-projection": [
        ("Is the holographic principle the same as 'reality is a projection'?",
         "No. AdS/CFT is a precise duality between a gravity theory in a volume and a conformal field theory on its boundary. It is not a claim that everyday 3D objects are rendered from 2D code."),
        ("Why is 3D KPZ hard?",
         "Above two dimensions the KPZ renormalisation flow runs to strong coupling, perturbation theory fails, and no exact solution is known. The page uses that as its fictional 'dimensionality curse'."),
    ],
    "kpz-reality-rendering": [
        ("Where has KPZ universality actually been measured?",
         "In interface growth experiments, bacterial colonies, liquid-crystal fronts and polariton condensates. The shared exponents are the point, not the specific material."),
        ("Can you 'hack' an object by changing its KPZ noise?",
         "No. Noise is a statistical descriptor of a growth process; no known coupling lets an external agent retune an object's structure by editing it."),
    ],
    "type2-superlattice-radar": [
        ("Why use a Type-II superlattice for infrared detection?",
         "Alternating InAs/GaSb layers create minibands whose effective bandgap is set by layer thickness, covering mid- and long-wave infrared with better uniformity than older detector materials."),
        ("What is Auger suppression?",
         "Suppressing non-radiative Auger recombination — a real design goal in infrared detectors and lasers, used to cut dark current and raise operating temperature."),
    ],
    "electromagnetic-theater-override": [
        ("Why does the page say that touch is electromagnetic?",
         "Because macroscopic contact forces come from electron-cloud repulsion constrained by Pauli exclusion. That part is textbook physics, and it is the only part the page treats as established."),
        ("Can a field make matter pass through matter?",
         "Not in any observed regime. The 'collision mesh override' assumes an external field can locally cancel that repulsion, and no experiment supports it."),
    ],
    "cooperative-resonance-torsion": [
        ("What is superradiance?",
         "Collective spontaneous emission from N phase-correlated emitters, with intensity scaling faster than N. It is observed in NV ensembles, atomic arrays and quantum wells."),
        ("Does synchronised spin coherence produce gravity-like effects?",
         "No measurable one. Einstein–Cartan torsion couples spin to geometry in theory, but the predicted metric perturbation from lab-scale spin currents is ~10⁻⁶⁰, and §4.5 shows the amplification path falling roughly thirty orders of magnitude short."),
    ],
    "warp-drive-torsion-propagation": [
        ("Did positive-energy warp drives solve the energy problem?",
         "Partly. Bobrick–Martire, Lentz and Rodal constructed warp metrics that need no negative energy, but they still require enormous positive energy densities and have no laboratory realisation."),
        ("What about the 10⁻⁶ metric perturbation this site used to quote?",
         "It was a narrative target, not a derivation: with N ≈ 10¹² nodes and N² gain, a 10⁻⁶⁰ perturbation only reaches ~10⁻³⁶. The page now states that explicitly instead of implying the gap was closed."),
    ],
}


def scope_block(slug):
    """渲染"什么是真的 / 什么是想象"三层声明。"""
    d = PAGE_SCOPE.get(slug)
    if not d:
        return ""
    return f'''
<div class="scope">
    <h2>What is real here, and what is fiction</h2>
    <ul>
        <li><span class="tag real">Real research</span>{d["real"]}</li>
        <li><span class="tag extra">Author's extrapolation</span>{d["extra"]}</li>
        <li><span class="tag fiction">Fiction / story setting</span>{d["fiction"]}</li>
    </ul>
    <p class="scope-note">{SCOPE_NOTE}</p>
</div>'''


def faq_block(slug):
    """渲染本页作者自撰问答（2 条）。"""
    items = PAGE_FAQ.get(slug) or []
    if not items:
        return ""
    rows = "".join(f'''
    <div class="faq-item">
        <h3>{q}</h3>
        <p>{a}</p>
    </div>''' for q, a in items)
    return f'''
<div class="faq" id="faq">
    <h2>Questions this page answers</h2>{rows}
</div>'''



# ── arXiv further-reading references (3-4 papers per lore page) ──
ARXIV_REFS = {
    "artificial-kondo-lattice": [
        {"id": "1004.4276", "title": "The Realization of Artificial Kondo Lattices in Nanostructured Arrays", "authors": "D. K. Singh et al.", "year": "2010"},
        {"id": "2609.08467", "title": "Theory of Kondo hybridization wave in Kondo lattice", "authors": "Yin Zhong", "year": "2026"},
        {"id": "2602.17349", "title": "Emergence of a symmetry-broken Chern insulator near a moiré Kondo breakdown", "authors": "Wanghao Tian et al.", "year": "2026"},
        {"id": "2408.01493", "title": "Strong pairing and symmetric pseudogap metal in double Kondo lattice model: from nickelate superconductor to tetralayer optical lattice", "authors": "Hui Yang et al.", "year": "2024"},
        {"id": "2211.15682", "title": "Kondo lattice model in magic-angle twisted bilayer graphene", "authors": "Yang-Zhi Chou et al.", "year": "2022"},
        {"id": "2512.09926", "title": "Connecting single-layer $t$-$J$ to Kondo lattice models: Exploration with cold atoms", "authors": "Hannah Lange et al.", "year": "2025"},
    ],
    "floquet-temporal-matter": [
        {"id": "2407.17917", "title": "Optical control of electrons in a Floquet topological insulator", "authors": "Daniel M. B. Lesko et al.", "year": "2024"},
        {"id": "1507.01415", "title": "PT Symmetric Floquet Topological Phase", "authors": "C. Yuce", "year": "2015"},
        {"id": "1901.09457", "title": "Three dimensional two-band Floquet topological insulator with $Z_2$ index", "authors": "Yan He et al.", "year": "2019"},
        {"id": "1705.04694", "title": "Floquet Topological Magnons", "authors": "S. A. Owerre", "year": "2017"},
        {"id": "1703.02553", "title": "Floquet topological phases protected by time glide symmetry", "authors": "Takahiro Morimoto et al.", "year": "2017"},
        {"id": "1803.10646", "title": "Quantum noise detects Floquet topological phases", "authors": "M. Rodriguez-Vega et al.", "year": "2018"},
    ],
    "semi-dirac-mass-nullification": [
        {"id": "2001.11188", "title": "Non-Hermitian semi-Dirac semi-metals", "authors": "Ayan Banerjee et al.", "year": "2020"},
        {"id": "1508.05145", "title": "Anderson localizaion for semi-Dirac semi-Weyl semi-metal", "authors": "Swapnonil Banerjee", "year": "2015"},
        {"id": "1612.08458", "title": "Semi-Dirac Semimetal in Silicene Oxide", "authors": "Chengyong Zhong et al.", "year": "2016"},
        {"id": "2005.14394", "title": "Quantum Hall studies of a Semi-Dirac Nanoribbon", "authors": "Priyanka Sinha et al.", "year": "2020"},
        {"id": "1312.0201", "title": "Semi-Dirac dispersion relation in photonic crystals", "authors": "Ying Wu", "year": "2013"},
        {"id": "2106.07793", "title": "Semi-Dirac and Weyl Fermions in Transition Metal Oxides", "authors": "Narayan Mohanta et al.", "year": "2021"},
    ],
    "qm-tether-exosuit": [
        {"id": "1606.00661", "title": "Quantum metrics on noncommutative spaces", "authors": "Maysam Maysami Sadr", "year": "2016"},
        {"id": "2105.15142", "title": "Revealing Chern number from quantum metric", "authors": "Anwei Zhang", "year": "2021"},
        {"id": "2605.03987", "title": "Quantum Metric Localization and Quantum Metric Protection", "authors": "Wen-Bo Dai et al.", "year": "2026"},
        {"id": "1605.08335", "title": "Gauge Invariance and the Quantum Metric Tensor", "authors": "J. Alvarez-Jimenez et al.", "year": "2016"},
        {"id": "2412.02753", "title": "Effects of the Hubbard interaction on the quantum metric", "authors": "Pavlo Sukhachov et al.", "year": "2024"},
        {"id": "math/0308207", "title": "Compact Quantum Metric Spaces", "authors": "Marc A. Rieffel", "year": "2003"},
    ],
    "arena-tripartite-architecture": [
        {"id": "1406.2887", "title": "Focus on topological quantum computation", "authors": "Jiannis K. Pachos et al.", "year": "2014"},
        {"id": "1802.06176", "title": "Introduction to topological quantum computation with non-Abelian anyons", "authors": "Bernard Field et al.", "year": "2018"},
        {"id": "2404.01779", "title": "Diagonal Coset Approach to Topological Quantum Computation with Fibonacci Anyons", "authors": "Lachezar S. Georgiev et al.", "year": "2024"},
        {"id": "0808.1933", "title": "Measurement-Only Topological Quantum Computation via Anyonic Interferometry", "authors": "Parsa Bonderson et al.", "year": "2008"},
        {"id": "2008.03542", "title": "Compiling single-qubit braiding gate for Fibonacci anyons topological quantum computation", "authors": "Mohamed Taha Rouabah", "year": "2020"},
        {"id": "0707.1889", "title": "Non-Abelian Anyons and Topological Quantum Computation", "authors": "Chetan Nayak et al.", "year": "2007"},
    ],
    "obstructed-atomic-phantom-grid": [
        {"id": "2506.23713", "title": "Photonic obstructed atomic insulator", "authors": "Hongyu Chen", "year": "2025"},
        {"id": "2301.13048", "title": "The destiny of obstructed atomic insulator under correlation", "authors": "Kun Jiang et al.", "year": "2023"},
        {"id": "2106.10276", "title": "Filling-Enforced Obstructed Atomic Insulators", "authors": "Yuanfeng Xu et al.", "year": "2021"},
        {"id": "2412.18943", "title": "Topologically constrained obstructed atomic limits in quasi-one-dimensional systems", "authors": "Milan Damnjanovic et al.", "year": "2024"},
        {"id": "2406.05380", "title": "Observation of floating surface state in obstructed atomic insulator candidate NiP$_2$", "authors": "Xiang-Rui Liu et al.", "year": "2024"},
        {"id": "2107.00647", "title": "Topology invisible to eigenvalues in obstructed atomic insulators", "authors": "Jennifer Cano et al.", "year": "2021"},
    ],
    "holographic-kpz-projection": [
        {"id": "1209.2417", "title": "Aging Logarithmic Conformal Field Theory : a holographic view", "authors": "Seungjoon Hyun et al.", "year": "2012"},
        {"id": "2011.04600", "title": "Lifshitz tails at spectral edge and holography with a finite cutoff", "authors": "Alexander Gorsky et al.", "year": "2020"},
        {"id": "1702.03910", "title": "Reflected Brownian motions in the KPZ universality class", "authors": "Thomas Weiss et al.", "year": "2017"},
        {"id": "2006.00431", "title": "Crossover from BKT-Rough to KPZ-Rough Surfaces for Interface-Limited Crystal Growth/Recession", "authors": "Noriko Akutsu", "year": "2020"},
        {"id": "1502.06661", "title": "Fluctuating hydrodynamics for a discrete Gross-Pitaevskii equation: mapping to Kardar-Parisi-Zhang universality class", "authors": "Manas Kulkarni et al.", "year": "2015"},
        {"id": "cond-mat/0509541", "title": "Strong-Coupling Fixed Point of the Kardar-Parisi-Zhang Equation", "authors": "Léonie Canet", "year": "2005"},
    ],
    "kpz-reality-rendering": [
        {"id": "2604.15095", "title": "Kardar-Parisi-Zhang physics in optically-confined continuous polariton condensates", "authors": "Mikhail Misko et al.", "year": "2026"},
        {"id": "2009.05177", "title": "Searching for the Kardar-Parisi-Zhang phase in microcavity polaritons", "authors": "A. Ferrier et al.", "year": "2020"},
        {"id": "2607.28106", "title": "Three-Dimensional Kardar--Parisi--Zhang Scaling in Polariton Condensates", "authors": "Junhui Cao et al.", "year": "2026"},
        {"id": "2207.03886", "title": "Kardar-Parisi-Zhang universality in discrete two-dimensional driven-dissipative exciton polariton condensates", "authors": "Konstantinos Deligiannis et al.", "year": "2022"},
        {"id": "2010.06435", "title": "Accessing Kardar-Parisi-Zhang universality sub-classes with exciton polaritons", "authors": "Konstantinos Deligiannis et al.", "year": "2020"},
        {"id": "1712.03709", "title": "Kardar-Parisi-Zhang universality in the phase distributions of one-dimensional exciton-polaritons", "authors": "Davide Squizzato et al.", "year": "2017"},
    ],
    "type2-superlattice-radar": [
        {"id": "2312.01604", "title": "Insights into optical absorption and dark currents of the 6.1Å Type-II superlattice absorbers for MWIR and SWIR applications", "authors": "Anuja Singh et al.", "year": "2023"},
        {"id": "1907.05592", "title": "High Speed Mid-Infrared Interband Cascade Photodetector Based on InAs/GaSb Type-II Superlattice", "authors": "Yaojiang Chen et al.", "year": "2019"},
        {"id": "2301.04858", "title": "Advancing carrier transport models for InAs/GaSb type-II superlattice MWIR photodetectors", "authors": "Rohit Kumar et al.", "year": "2023"},
        {"id": "1906.07351", "title": "Demonstration of Si based InAs/GaSb type-II superlattice p-i-n photodetector", "authors": "Zhuo Deng et al.", "year": "2019"},
        {"id": "2103.08717", "title": "Carrier localization and miniband modeling of InAs/GaSb based type-II superlattice infrared detectors", "authors": "Swarnadip Mukherjee et al.", "year": "2021"},
        {"id": "2111.13358", "title": "Simulation of the band structure of InAs/GaSb type II superlattices utilizing multiple energy band theories", "authors": "Shuiliu Fang et al.", "year": "2021"},
    ],
    "electromagnetic-theater-override": [
        {"id": "2310.18559", "title": "Quantum Interactions in Topological R166 Kagome Magnet", "authors": "Xitong Xu et al.", "year": "2023"},
        {"id": "2110.07563", "title": "Topological charge-entropy scaling in kagome Chern magnet TbMn$_6$Sn$_6$", "authors": "Xitong Xu et al.", "year": "2021"},
        {"id": "2110.06012", "title": "Anisotropically large anomalous and topological Hall effect in a kagome magnet", "authors": "Gyanendra Dhakal et al.", "year": "2021"},
        {"id": "2205.07806", "title": "Magneto-Transport Properties of Kagome Magnet TmMn$_6$Sn$_6$", "authors": "Bin Wang et al.", "year": "2022"},
        {"id": "2311.05839", "title": "Visualizing symmetry-breaking electronic orders in epitaxial Kagome magnet FeSn films", "authors": "Huimin Zhang et al.", "year": "2023"},
        {"id": "1605.01423", "title": "Emergent Order in the Kagome Ising Magnet Dy3Mg2Sb3O14", "authors": "Joseph A. M. Paddison et al.", "year": "2016"},
    ],
    "cooperative-resonance-torsion": [
        {"id": "2105.12350", "title": "A Superradiant Maser with Nitrogen-Vacancy Center Spins", "authors": "Qilong Wu et al.", "year": "2021"},
        {"id": "2407.09755", "title": "Superradiance from Nitrogen Vacancy Centers Coupled to An Ultranarrow Optical Cavity", "authors": "Yi-Dan Qu et al.", "year": "2024"},
        {"id": "2009.12194", "title": "Exciton-polariton mediated interaction between two nitrogen-vacancy color centers in diamond using two-dimensional transition metal dichalcogenides", "authors": "J. C. G. Henriques et al.", "year": "2020"},
        {"id": "1802.07100", "title": "Superradiant Hybrid Quantum Devices", "authors": "Andreas Angerer et al.", "year": "2018"},
        {"id": "1002.1244", "title": "Optical Superradiance from Nuclear Spin Environment of Single Photon Emitters", "authors": "E. M. Kessler et al.", "year": "2010"},
        {"id": "2606.28935", "title": "Optically Switched Phonon Superradiance of Surface Acoustic Wave in Diamond", "authors": "Zhiwei Chen et al.", "year": "2026"},
    ],
    "warp-drive-torsion-propagation": [
        {"id": "2401.15136", "title": "On the Wormhole--Warp Drive Correspondence", "authors": "R. Garattini et al.", "year": "2024"},
        {"id": "2207.06458", "title": "Warp Drive Aerodynamics", "authors": "Carlos Barceló et al.", "year": "2022"},
        {"id": "gr-qc/0110086", "title": "Warp Drive With Zero Expansion", "authors": "Jose Natario", "year": "2001"},
        {"id": "2103.05610", "title": "Warp drive basics", "authors": "Miguel Alcubierre et al.", "year": "2021"},
        {"id": "2205.02780", "title": "Alcubierre Warp Drive in Bohmian Quantum Gravity", "authors": "Sijo K. Joseph", "year": "2022"},
        {"id": "2404.03095", "title": "Analyzing Warp Drive Spacetimes with Warp Factory", "authors": "Christopher Helmerich et al.", "year": "2024"},
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
    """FAQPage 结构化数据：只放本页作者自撰问答（PAGE_FAQ）。

    2026-11-07: 原实现读 content/geo_hot_questions/qa_schema.json —— 那些问答来自
    StackExchange 热度池，与页面主题相关性弱、且带采集元数据，已整体移除。
    """
    items = PAGE_FAQ.get(slug) or []
    entities = [{"@type": "Question", "name": q,
                 "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items]
    return [{"@type": "FAQPage", "mainEntity": entities}] if entities else []


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
                "url": f"{SITE_URL}/author.html",
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

    # 三层口径声明：紧跟正文 H1（2026-11-07）
    if not is_index:
        _sc = scope_block(slug)
        if _sc:
            _h1_end = body_html.find("</h1>")
            if _h1_end != -1:
                body_html = body_html[:_h1_end + 5] + _sc + body_html[_h1_end + 5:]
            else:
                body_html = _sc + body_html

    # 正文首段后注入书页内链(2026-09-09:文章页 → book.html 购买/阅读锚点,强化内链权重)
    if not is_index and not slug.startswith('book'):
        fp = body_html.find('</p>')
        if fp != -1:
            intext = (f'<p class="body-link"><a href="book.html" class="intext">📖 Read this concept in '
                      f'<em>{BOOK_TITLE}</em></a> — the hard sci-fi novel where this physics becomes story.</p>')
            body_html = body_html[:fp + 4] + intext + body_html[fp + 4:]
    
    # SEO-optimized meta descriptions per page
    SEO_DESCRIPTIONS = {
        "artificial-kondo-lattice": "Artificial Kondo lattices and topological zero modes: the real condensed-matter physics behind the novel's logic core, with a clear line between research and fiction.",
        "floquet-temporal-matter": "Floquet engineering explained: periodic driving, Floquet topological phases, and the stability limits that make the novel's 'programmable matter' fiction.",
        "semi-dirac-mass-nullification": "Semi-Dirac fermions give quasiparticles zero effective mass along one axis. What that means, and why it does not make a spacecraft lighter.",
        "qm-tether-exosuit": "The quantum metric is not spacetime curvature. A guide to the coupling chain the QM-Tether suit borrows — and where the numbers stop working.",
        "arena-tripartite-architecture": "Anyons, braiding, Majorana modes and high-dimensional orbital angular momentum: the real research behind the Computational Arena setting.",
        "obstructed-atomic-phantom-grid": "Obstructed atomic insulators place charge centres between atoms. The real band theory, and the fictional phantom grid built on it.",
        "holographic-kpz-projection": "AdS/CFT and the KPZ equation are both real; projecting 3D matter from a 2D boundary is not. Where the novel's rendering engine departs from physics.",
        "kpz-reality-rendering": "KPZ universality in growth, bacteria and polariton condensates — the measured physics behind the novel's procedural 'reality rendering'.",
        "type2-superlattice-radar": "Type-II InAs/GaSb superlattices, tunable bandgaps and Auger suppression: the real infrared detector physics, without the invented radar.",
        "electromagnetic-theater-override": "Macroscopic contact is electromagnetic repulsion plus Pauli exclusion. The textbook part, and the fictional collision-mesh override built on top of it.",
        "cooperative-resonance-torsion": "Superradiance in NV ensembles and Einstein-Cartan torsion: what is measured, what is theory, and why the mass-repulsion engine stays fiction.",
        "warp-drive-torsion-propagation": "Alcubierre's metric and the positive-energy warp solutions of Bobrick-Martire, Lentz and Rodal — with an honest accounting of the remaining energy gap.",
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
        "artificial-kondo-lattice": "Artificial Kondo lattices: what the physics supports, and where the novel takes over",
        "floquet-temporal-matter": "Floquet engineering: driving matter with light, minus the fiction",
        "semi-dirac-mass-nullification": "Semi-Dirac fermions: zero effective mass inside a crystal, and why objects stay heavy",
        "qm-tether-exosuit": "Quantum metric, spin current, torsion: the coupling chain behind the QM-Tether suit",
        "arena-tripartite-architecture": "Anyons, Majorana modes and high-dimensional OAM: the physics under the Computational Arena",
        "obstructed-atomic-phantom-grid": "Obstructed atomic insulators: electrons that live between the atoms",
        "holographic-kpz-projection": "KPZ and holography: two real theories, one fictional rendering engine",
        "kpz-reality-rendering": "KPZ universality: the equation that shapes growing interfaces",
        "type2-superlattice-radar": "Type-II superlattices: the real physics of infrared detection",
        "electromagnetic-theater-override": "Why touch is electromagnetic — and why 'phasing through matter' is fiction",
        "cooperative-resonance-torsion": "Superradiance, torsion and the thirty-orders-of-magnitude problem",
        "warp-drive-torsion-propagation": "Warp drive physics: Alcubierre, positive-energy bubbles, and what stays fiction",
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
        .scope { background: #101a10; border: 1px solid #2a5a2a; border-left: 4px solid #00FF41; padding: 18px 22px; margin: 0 0 28px; }
        .scope h2 { color: #00FF41; font-size: 0.95em; text-transform: uppercase; letter-spacing: 1.5px; margin: 0 0 12px; }
        .scope ul { list-style: none; margin: 0; }
        .scope li { font-size: 0.88em; color: #c8c8c8; margin-bottom: 10px; line-height: 1.6; }
        .scope .tag { display: inline-block; font-size: 0.68em; text-transform: uppercase; letter-spacing: 1px; padding: 2px 7px; margin-right: 8px; border: 1px solid #2a5a2a; color: #9a9a9a; white-space: nowrap; }
        .scope .tag.real { color: #00FF41; border-color: #00FF41; }
        .scope .tag.extra { color: #d0b050; border-color: #6a5a20; }
        .scope .tag.fiction { color: #c06a6a; border-color: #6a2a2a; }
        .scope-note { color: #888; font-size: 0.82em; margin: 12px 0 0; border-top: 1px solid #1a3a1a; padding-top: 10px; }
        .faq { margin-top: 40px; padding-top: 20px; border-top: 1px solid #1a3a1a; }
        .faq h2 { color: #00FF41; font-size: 1em; margin-bottom: 14px; }
        .faq-item { margin-bottom: 18px; }
        .faq-item h3 { color: #ccc; font-size: 0.95em; margin-bottom: 5px; }
        .faq-item p { color: #b0b0b0; font-size: 0.9em; }
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
                __FAQ__
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
                <span style="color:#555; font-size:0.75em;">Sources: </span>
                __FOOTREFS__
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
        .replace('__FOOTREFS__', ' '.join(
            f'<a href="https://arxiv.org/abs/{r["id"]}" style="color:#2a7a2a; font-size:0.75em; text-decoration:none;">{r["title"][:48]}… (arXiv)</a>'
            for r in (ARXIV_REFS.get(slug, [])[:3])) or '<span style="color:#555; font-size:0.75em;">see Further Reading</span>')
        .replace('__FAQ__', faq_block(slug) if not is_index else '')
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
        "PRICE_NOTE": PRICE_NOTE,
        "SAMPLE_WORDS": str(len(re.findall(r"[A-Za-z][A-Za-z'\u2019\-]*", BOOK_SAMPLE))),
        "SAMPLE_NOTE": SAMPLE_NOTE.format(
            n=len(re.findall(r"[A-Za-z][A-Za-z'\u2019\-]*", BOOK_SAMPLE))),
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
