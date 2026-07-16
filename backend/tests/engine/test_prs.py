from app.engine.scoring.prs import compute_prs

def test_prs_direct_identifiers():
    profile = {"pii_scan": {"direct_identifiers_detected": True}}
    metadata = {"sensitivity_class": "standard"}
    res = compute_prs(profile, metadata)
    assert res.baseline_risk == 50.0
    assert res.prs == 50
    assert res.band == "High"

def test_prs_differential_privacy():
    profile = {"pii_scan": {"direct_identifiers_detected": False}}
    metadata = {
        "differential_privacy_applied": True,
        "sensitivity_class": "standard"
    }
    res = compute_prs(profile, metadata)
    assert res.baseline_risk == 20.0
    assert res.prs == 20
    assert res.band == "Moderate"

def test_prs_location_granularity():
    profile = {"pii_scan": {"direct_identifiers_detected": False}}
    
    # Village + rare condition
    metadata = {
        "location_granularity": "village",
        "rare_condition_flag": True,
        "sensitivity_class": "standard"
    }
    res = compute_prs(profile, metadata)
    assert res.baseline_risk == 30.0
    assert res.prs == 30
    assert res.band == "Moderate"

    # District
    metadata = {
        "location_granularity": "district",
        "rare_condition_flag": False,
        "sensitivity_class": "standard"
    }
    res = compute_prs(profile, metadata)
    assert res.baseline_risk == 15.0
    assert res.prs == 15
    assert res.band == "Low"  # 15 is < 16, so Low

    # State
    metadata = {
        "location_granularity": "state",
        "rare_condition_flag": False,
        "sensitivity_class": "standard"
    }
    res = compute_prs(profile, metadata)
    assert res.baseline_risk == 5.0
    assert res.prs == 5
    assert res.band == "Low"

def test_prs_sensitivity_multipliers():
    profile = {"pii_scan": {"direct_identifiers_detected": False}}
    
    # District (baseline 15) with high_stigma (1.5) -> 22.5 -> rounded to 23
    metadata = {
        "location_granularity": "district",
        "rare_condition_flag": False,
        "sensitivity_class": "high_stigma"
    }
    res = compute_prs(profile, metadata)
    assert res.baseline_risk == 15.0
    assert res.prs == 23
    assert res.band == "Moderate"

    # District (baseline 15) with critical (2.0) -> 30.0 -> 30
    metadata = {
        "location_granularity": "district",
        "rare_condition_flag": False,
        "sensitivity_class": "critical"
    }
    res = compute_prs(profile, metadata)
    assert res.prs == 30
    assert res.band == "Moderate"
