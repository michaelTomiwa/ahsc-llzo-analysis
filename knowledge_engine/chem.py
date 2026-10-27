"""Chemistry-aware text normalisation: material names, elements, families, dopants, units.

These rules are deliberately transparent (no hidden model) so every derived field in the
knowledge base can be audited and corrected by a domain expert.
"""
from __future__ import annotations

import math
import re

SUBSCRIPTS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
SUPERSCRIPTS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺", "0123456789-+")
DASHES = str.maketrans({"–": "-", "—": "-", "−": "-", "‐": "-", "‑": "-"})

ELEMENTS = set(
    "H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr "
    "Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm "
    "Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U".split()
)

# Abbreviations that are common in the curated records and cannot be parsed as formulas.
ABBREVIATIONS: dict[str, set[str]] = {
    "AC": {"C"}, "ACTIVATED CARBON": {"C"}, "CNT": {"C"}, "CNTS": {"C"}, "RGO": {"C"}, "GO": {"C"},
    "GRAPHENE": {"C"}, "GRAPHITE": {"C"}, "CARBON": {"C"}, "MXENE": {"Ti", "C"},
    "LFP": {"Li", "Fe", "P", "O"}, "NCM": {"Li", "Ni", "Co", "Mn", "O"}, "NMC": {"Li", "Ni", "Co", "Mn", "O"},
    "NCM622": {"Li", "Ni", "Co", "Mn", "O"}, "NCM811": {"Li", "Ni", "Co", "Mn", "O"},
    "LCO": {"Li", "Co", "O"}, "LMO": {"Li", "Mn", "O"}, "LLZO": {"Li", "La", "Zr", "O"},
    "LLZTO": {"Li", "La", "Zr", "Ta", "O"}, "LATP": {"Li", "Al", "Ti", "P", "O"}, "LLTO": {"Li", "La", "Ti", "O"},
    "LPSCL": {"Li", "P", "S", "Cl"}, "LITFSI": {"Li", "C", "F", "N", "O", "S"}, "LIFSI": {"Li", "F", "N", "O", "S"},
    "NF": {"Ni"}, "NICKEL FOAM": {"Ni"}, "LITHIUM": {"Li"}, "ZINC": {"Zn"}, "SULFUR": {"S"},
    "PEO": {"C", "H", "O"}, "PVDF": {"C", "H", "F"}, "PAN": {"C", "H", "N"}, "PPY": {"C", "H", "N"},
    "PANI": {"C", "H", "N"}, "PEDOT": {"C", "H", "O", "S"}, "PMMA": {"C", "H", "O"},
}
_FORMULA_STOPWORDS = {"NR", "NF", "CN", "NC", "PC", "SC", "IN", "AS", "BE", "NO", "HE", "AT"}


def normalize_text(text: object) -> str:
    """Unicode-normalise a raw cell: sub/superscripts, dashes, whitespace."""
    if text is None or (isinstance(text, float) and math.isnan(text)):
        return ""
    value = str(text).translate(SUBSCRIPTS).translate(SUPERSCRIPTS).translate(DASHES)
    return re.sub(r"\s+", " ", value).strip()


def is_missing(text: object) -> bool:
    value = normalize_text(text).strip(" .").upper()
    return value in {"", "NR", "NA", "N/A", "NAN", "-", "NONE", "NOT REPORTED"}


def canonical_material(name: object) -> str:
    """Stable display name for a material (drops curation notes and trailing punctuation)."""
    value = normalize_text(name)
    value = re.sub(r"\(\s*electrode material\s*\)", "", value, flags=re.I)
    value = re.sub(r"\s*\(\s*\)", "", value)
    value = value.strip(" .;,")
    return re.sub(r"\s+", " ", value)


def _decompose_formula(token: str) -> list[str] | None:
    """Split a formula-like token into element symbols, or return None if it is not one."""
    stripped = re.sub(r"[0-9.xyδ]+", " ", token)
    pieces = re.findall(r"[A-Z][a-z]?|\S", stripped.replace(" ", ""))
    if not pieces or any(piece not in ELEMENTS for piece in pieces):
        return None
    return pieces


# In supercapacitor papers these acronyms usually name carbons, not lithium cathodes.
_AHSC_AMBIGUOUS = {"NCM", "NMC", "LCO", "LMO", "NF"}


def elements_in(name: object, system: str | None = None) -> list[str]:
    """Best-effort element set for a material string (formulas plus known abbreviations)."""
    text = normalize_text(name)
    found: set[str] = set()
    upper = text.upper()
    for abbreviation, elements in ABBREVIATIONS.items():
        if system == "AHSC" and abbreviation in _AHSC_AMBIGUOUS:
            continue
        if re.search(rf"(?<![A-Z]){re.escape(abbreviation)}(?![A-Z])", upper):
            found |= elements
    for token in re.findall(r"[A-Za-z0-9.]+", text):
        token = token.strip(".")
        if token.upper() in _FORMULA_STOPWORDS or len(token) < 1:
            continue
        if token.endswith("Tx"):  # MXene termination, e.g. Ti3C2Tx
            token = token[:-2]
        pieces = _decompose_formula(token)
        if not pieces:
            continue
        has_digit = any(ch.isdigit() for ch in token)
        if has_digit or len(set(pieces)) >= 2 or (len(pieces) == 1 and len(token) == len(pieces[0]) and len(token) == 2):
            found |= set(pieces)
    return sorted(found)


# (pattern, family, scope) - scope "electrolyte" rules only apply to electrolyte strings.
FAMILY_RULES: list[tuple[str, str, str]] = [
    (r"(peo|peg|pvdf|pan|pmma|poly|polymer).*(llz|garnet)|(llz|garnet).*(peo|peg|pvdf|pan|pmma|poly|polymer)",
     "Polymer-garnet composite", "any"),
    (r"llz(t)?o|garnet|li[0-9.]*la3zr", "Garnet LLZO", "any"),
    (r"lpscl|li6ps5cl|sulfide", "Sulfide solid electrolyte", "electrolyte"),
    (r"latp|llto|nasicon", "Oxide filler (LATP/LLTO)", "any"),
    (r"\bpeo\b|peg|poly\(ethylene oxide\)", "PEO/PEG polymer", "electrolyte"),
    (r"pvdf", "PVDF-based polymer", "electrolyte"),
    (r"\bpan\b", "PAN polymer", "electrolyte"),
    (r"pmma|\bmma\b", "PMMA polymer", "electrolyte"),
    (r"ionic liquid|polyil|\bils?\b|py13|\bpil\b|imidazolium", "Ionic liquid", "any"),
    (r"liquid organic|^acn\b|^vc with", "Liquid electrolyte", "electrolyte"),
    (r"starch|gelatin|pectin|chitosan|cellulose|rubber", "Bio-derived polymer", "electrolyte"),
    (r"poly|polymer|\bpcl\b|pegda|etpta|dol\b|cpe|spe|gpe|\bp\(|^p[a-z]|vec|tmc|lactide|caprolactone|methacrylate|"
     r"egdma|amps|ionene|oligomer|teg\b|lidmpa|sape|oda|pmda|sppg", "Other polymer electrolyte", "electrolyte"),
    (r"mxene|ti3c2|v2c|nb2c|c\d?t[xz]|ti3cn|-mx\b|mfmx", "MXene", "any"),
    (r"fe\(cn\)6|prussian", "Prussian blue analogue", "any"),
    (r"ldh|layered double hydroxide", "Layered double hydroxide", "any"),
    (r"lifepo4|\blfp\b", "LiFePO4 (LFP)", "any"),
    (r"ncm|nmc|lini.*co.*mn", "Layered NCM oxide", "any"),
    (r"mno2|mn3o4|mn2o3|mnox|manganese", "Manganese oxide", "any"),
    (r"nico|ni-co|co3o4|nio|ni\(oh\)|co\(oh\)|nickel|cobalt", "Ni/Co oxide-hydroxide", "any"),
    (r"s2\b|s4\b|sulfide|sulphide|ni3s2|mos2|ws2|cos|nis", "Metal sulfide", "any"),
    (r"p\b.*@|ni12p5|co2p|cu3p|nixpy|-p\b|cop\b|mop\b|phosphide|ni2p", "Metal phosphide", "any"),
    (r"nb2o5|tio2|v2o5|wo3|fe2o3|fe3o4|moo3|oxide|o3\b|o4\b", "Transition-metal oxide", "any"),
    (r"ppy|pani|pedot|polypyrrole|polyaniline", "Conducting polymer", "any"),
    (r"graphene|rgo|\bgo\b|cnt|carbon|\bac\b|biochar|biomass|ketjen|graphite|porous c|hpc|npc|pc\b|\bc\b|"
     r"^[a-z-]*(c|g|gs|gns|cs|cn)(-[0-9.]+)?$|-c\b|@c\b", "Carbon", "any"),
    (r"\bzn\b|zinc", "Zinc metal", "any"),
    (r"lithium|\bli\b", "Lithium metal", "any"),
    (r"poly|polymer|bio", "Polymer", "any"),
]


def material_family(name: object, role: str = "electrode") -> str:
    """Coarse material family used for graph analytics and gap maps."""
    text = canonical_material(name).lower()
    if not text:
        return "Unspecified"
    for pattern, family, scope in FAMILY_RULES:
        if scope == "electrolyte" and role != "electrolyte":
            continue
        if re.search(pattern, text):
            return family
    return "Other"


DOPANT_ELEMENTS = ("Ta", "Al", "Ga", "Nb", "W", "Mo", "Ce", "Te", "Sb", "Y", "Ca", "Sr", "Ba", "Bi", "Fe", "Mg", "Zn")


def dopants_in(name: object) -> list[str]:
    """Dopants on a garnet LLZO composition (e.g. 'LLZO-0.5Ta', 'Li6.5La3Zr1.5Ta0.5O12', 'LLZTO')."""
    text = normalize_text(name)
    found: set[str] = set()
    for match in re.finditer(r"LLZO\s*-\s*([0-9.]*)\s*([A-Z][a-z]?)", text):
        if match.group(2) in DOPANT_ELEMENTS:
            found.add(match.group(2))
    if re.search(r"LLZTO", text, re.I):
        found.add("Ta")
    if re.search(r"LLZ[AG]O", text):
        found.add("Al" if "LLZAO" in text else "Ga")
    for formula in re.findall(r"Li[0-9.]*La[0-9.]*Zr[0-9.]*[A-Za-z0-9.]*O12", text):
        for symbol in re.findall(r"[A-Z][a-z]?", formula):
            if symbol in DOPANT_ELEMENTS:
                found.add(symbol)
    for match in re.finditer(r"\b(Ta|Al|Ga|Nb|W|Mo)\s*-\s*doped", text):
        found.add(match.group(1))
    return sorted(found)


def additives_in(name: object) -> list[str]:
    """Salts, fillers and co-components named inside an electrolyte string (e.g. 'PEO (with LiTFSI)')."""
    text = normalize_text(name)
    inner = " ".join(re.findall(r"\((.*?)\)", text)) + " " + " ".join(re.findall(r"with ([^()]*)", text, re.I))
    parts = re.split(r",|\band\b|\+|;|/", inner)
    cleaned = {re.sub(r"^(with|containing)\s+", "", part.strip(" .()-"), flags=re.I) for part in parts}
    return sorted(part for part in cleaned if 1 < len(part) < 40)


UNIT_PATTERNS: list[tuple[str, str]] = [
    (r"mah\s*/?\s*g|mah\s*g\s*-?1", "mAh/g"),
    (r"mah\s*/?\s*cm\s*-?2|mah\s*cm", "mAh/cm2"),
    (r"mf\s*/?\s*cm\s*-?2|mf\s*cm\s*-?2", "mF/cm2"),
    (r"mf\s*/?\s*cm\s*-?3|mf\s*cm\s*-?3", "mF/cm3"),
    (r"mf\s*/?\s*cm", "mF/cm"),
    (r"\bf\s*/?\s*cm\s*-?3|\bf\s*cm\s*-?3", "F/cm3"),
    (r"\bf\s*/?\s*cm\s*-?2|\bf\s*cm\s*-?2", "F/cm2"),
    (r"\bc\s*/?\s*g|\bc\s*g\s*-?1", "C/g"),
    (r"\bf\s*/?\s*g|\bf\s*g\s*-?1|\bfg\s*-?1", "F/g"),
    (r"µwh|μwh|uwh", "uWh/cm2"),
    (r"mwh\s*/?\s*cm\s*-?3|mwh\s*cm", "mWh/cm3"),
    (r"wh\s*/?\s*kg|wh\s*kg", "Wh/kg"),
    (r"mw\s*/?\s*cm|mw\s*cm", "mW/cm3"),
    (r"kw\s*/?\s*kg|kw\s*kg", "kW/kg"),
    (r"w\s*/?\s*kg|w\s*kg", "W/kg"),
]


def detect_unit(raw: object, default: str) -> tuple[str, bool]:
    """Return (unit, explicit) where `explicit` says the unit was written in the source text."""
    text = normalize_text(raw).lower()
    head = re.split(r"@|\bat\b", text)[0]  # rate conditions (A/g, W/kg) follow '@' or 'at'
    for pattern, unit in UNIT_PATTERNS:
        if re.search(pattern, head):
            return unit, True
    return default, False


_SCI = re.compile(r"(?:(\d+(?:\.\d+)?)\s*(?:[x×*]\s*)?)?10\s*\^?\s*(-?\s*\d+)")


def parse_conductivity(raw: object) -> tuple[float | None, str]:
    """Parse an ionic-conductivity string into S/cm. Returns (value, note).

    Handles '2.9 × 10⁻⁴ S cm⁻¹', '10⁻⁴ to 10⁻³' (range -> geometric mean, flagged) and
    plain decimals. Values are assumed to be in S/cm, the unit used throughout the thesis.
    """
    text = normalize_text(raw)
    if is_missing(text):
        return None, "missing"
    text_ms = text.lower()
    values = []
    for mantissa, exponent in _SCI.findall(text):
        exponent_value = int(exponent.replace(" ", ""))
        if exponent_value > 0:  # '10^4' style typo; skip rather than invent
            continue
        values.append((float(mantissa) if mantissa else 1.0) * 10.0 ** exponent_value)
    if not values:
        plain = re.findall(r"\d+(?:\.\d+)?(?:e-?\d+)?", text_ms)
        if not plain:
            return None, "unparsed"
        values = [float(plain[0])]
    range_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:to|-)\s*(\d+(?:\.\d+)?)\s*[x×]\s*10", text)
    if range_match and len(values) == 1:
        low = float(range_match.group(1)) * values[0] / float(range_match.group(2))
        return math.sqrt(low * values[0]), "range reported; geometric mean of bounds"
    if len(values) >= 2 and re.search(r"\bto\b", text_ms):
        return math.sqrt(values[0] * values[1]), "range reported; geometric mean of bounds"
    value = values[0]
    if "ms" in text_ms.replace(" ", "") and "ms/cm" in text_ms.replace(" ", ""):
        value /= 1000.0
    return value, "parsed"


def parse_temperature(raw: object) -> str | None:
    text = normalize_text(raw)
    match = re.search(r"(-?\d+(?:\.\d+)?)\s*°?\s*C\b", text)
    if match:
        return f"{match.group(1)} °C"
    if re.search(r"\bRT\b|room temp", text, re.I):
        return "room temperature"
    match = re.search(r"\bat\s+(\d{2,3})\b", text)
    if match:
        return f"{match.group(1)} °C (unit implied)"
    return None


def parse_rate(raw: object) -> str | None:
    text = normalize_text(raw)
    match = re.search(r"(?:@|\bat\b)\s*([0-9.]+\s*(?:m?A\s*/?\s*g\s*-?1?|m?A\s*/?\s*cm\s*-?2|C\b|mV\s*/?\s*s\s*-?1?|W\s*kg\s*-?1))", text, re.I)
    return re.sub(r"\s+", " ", match.group(1)).strip() if match else None
