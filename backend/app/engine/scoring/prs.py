from dataclasses import dataclass
from typing import Optional, Dict, Any

SENSITIVITY_MULTIPLIERS = {
    "standard": 1.0,
    "high_stigma": 1.5,
    "critical": 2.0,
}

PRS_BANDS = [
    (71, "Very High"),
    (41, "High"),
    (16, "Moderate"),
    (0,  "Low"),
]

# Step 1 identification risk lookup table (from MIDAS Lite Annexure I)
IDENTIFICATION_RISK_SCORES = {
    "direct_identifiers_present": 50.0,
    "village_rare_condition": 30.0,
    "district_or_month": 15.0,
    "state_or_region": 5.0,
    "generalised_categories": 5.0,
}

@dataclass
class PRSResult:
    baseline_risk: float
    sensitivity_class: str
    sensitivity_multiplier: float
    adjusted_risk: float
    prs: int
    band: str
    computation_trace: str
    differential_privacy_applied: bool
    epsilon: Optional[float]

def compute_prs(profile: Dict[str, Any], metadata: Dict[str, Any]) -> PRSResult:
    # Step 1: Identification risk
    pii_scan = profile.get("pii_scan", {})
    if pii_scan.get("direct_identifiers_detected", False):
        baseline = 50.0
        basis = "direct_identifiers_present"
    elif metadata.get("differential_privacy_applied"):
        epsilon = metadata.get("dp_epsilon")
        epsilon_val = float(epsilon) if epsilon is not None else 0.0
        baseline = min(100.0, 20.0 * epsilon_val)
        basis = f"differential_privacy_epsilon_{epsilon}"
    else:
        location = metadata.get("location_granularity", "district")
        rare = metadata.get("rare_condition_flag", False)
        if location == "village" and rare:
            baseline = 30.0
            basis = "village_rare_condition"
        elif location in ("district", "taluk"):
            baseline = 15.0
            basis = "district_or_month"
        elif location in ("state", "region", "national"):
            baseline = 5.0
            basis = "state_or_region"
        else:
            baseline = 15.0
            basis = "default_moderate"

    # Step 2: Sensitivity multiplier
    sensitivity = metadata.get("sensitivity_class", "standard")
    multiplier = SENSITIVITY_MULTIPLIERS.get(sensitivity, 1.0)
    adjusted = baseline * multiplier
    prs = min(100, round(adjusted))
    band = next(label for threshold, label in PRS_BANDS if prs >= threshold)
    trace = f"baseline={baseline} ({basis}) × multiplier={multiplier} ({sensitivity}) = {adjusted} → PRS={prs}"

    return PRSResult(
        baseline_risk=baseline,
        sensitivity_class=sensitivity,
        sensitivity_multiplier=multiplier,
        adjusted_risk=adjusted,
        prs=prs,
        band=band,
        computation_trace=trace,
        differential_privacy_applied=metadata.get("differential_privacy_applied", False),
        epsilon=metadata.get("dp_epsilon")
    )
