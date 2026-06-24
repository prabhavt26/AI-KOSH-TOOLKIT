from dataclasses import dataclass
from typing import Dict, Optional

CQI_BANDS = [
    (95.0, "Diamond"),
    (85.0, "Platinum"),
    (70.0, "Gold"),
    (50.0, "Silver"),
    (25.0, "Bronze"),
    (0.0,  "Remediation"),
]

@dataclass
class CQIResult:
    total_score: int
    max_possible: int
    cqi: float
    band: str
    formula_trace: str
    domain_11_applicable: bool

def compute_cqi(domain_scores: Dict[int, Optional[int]], domain_11_applicable: bool) -> CQIResult:
    scores = {k: v for k, v in domain_scores.items() if v is not None}
    total = sum(scores.values())
    max_possible = 60 if domain_11_applicable else 56
    cqi = round((total / max_possible) * 100, 1)
    band = next(label for threshold, label in CQI_BANDS if cqi >= threshold)
    trace = f"({total} / {max_possible}) × 100 = {cqi}"
    return CQIResult(
        total_score=total,
        max_possible=max_possible,
        cqi=cqi,
        band=band,
        formula_trace=trace,
        domain_11_applicable=domain_11_applicable
    )
