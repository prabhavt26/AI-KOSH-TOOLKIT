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

def compute_prs(profile: Dict[str, Any], metadata: Dict[str, Any], criteria: Optional[Dict[str, Any]] = None) -> PRSResult:
    # Step 1: Identification risk
    pii_scan = profile.get("pii_scan", {})
    if pii_scan.get("direct_identifiers_detected", False):
        baseline = 50.0
        basis = "direct_identifiers_present"
    elif metadata.get("differential_privacy_applied"):
        baseline = 20.0
        basis = "differential_privacy_applied"
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
    prs_config = criteria.get("prs", {}) if isinstance(criteria, dict) else {}
    sens_mult = prs_config.get("sensitivity_multipliers", SENSITIVITY_MULTIPLIERS)
    multiplier = float(sens_mult.get(sensitivity, SENSITIVITY_MULTIPLIERS.get(sensitivity, 1.0)))
    adjusted = baseline * multiplier
    prs = min(100, int(adjusted + 0.5))

    prs_bands_cfg = prs_config.get("bands", {})
    if prs_bands_cfg:
        high_max = int(prs_bands_cfg.get("high_max", 70))
        mod_max = int(prs_bands_cfg.get("moderate_max", 40))
        low_max = int(prs_bands_cfg.get("low_max", 15))
        if prs > high_max:
            band = "Very High"
        elif prs > mod_max:
            band = "High"
        elif prs > low_max:
            band = "Moderate"
        else:
            band = "Low"
    else:
        band = next(label for threshold, label in PRS_BANDS if prs >= threshold)

    trace = f"baseline={baseline} ({basis}) × multiplier={multiplier} ({sensitivity}) = {adjusted} → PRS={prs}"


    return PRSResult(
        baseline_risk=baseline,
        sensitivity_class=sensitivity,
        sensitivity_multiplier=multiplier,
        adjusted_risk=adjusted,
        prs=prs,
        band=band,
        computation_trace=trace
    )
