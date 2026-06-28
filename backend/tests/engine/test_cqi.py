from app.engine.scoring.cqi import compute_cqi

def test_cqi_all_max_scores_d11_applicable():
    # All 15 domains get score 4
    domain_scores = {i: 4 for i in range(1, 16)}
    res = compute_cqi(domain_scores, domain_11_applicable=True)
    assert res.total_score == 60
    assert res.max_possible == 60
    assert res.cqi == 100.0
    assert res.band == "Diamond"

def test_cqi_all_max_scores_d11_not_applicable():
    # 14 domains get score 4, Domain 11 gets None (or omitted)
    domain_scores = {i: 4 for i in range(1, 16)}
    domain_scores[11] = None
    res = compute_cqi(domain_scores, domain_11_applicable=False)
    assert res.total_score == 56
    assert res.max_possible == 56
    assert res.cqi == 100.0
    assert res.band == "Diamond"

def test_cqi_all_ones():
    domain_scores = {i: 1 for i in range(1, 16)}
    res = compute_cqi(domain_scores, domain_11_applicable=True)
    assert res.total_score == 15
    assert res.cqi == 25.0
    assert res.band == "Bronze"

def test_cqi_mixed_scores():
    # E.g. 10 domains with score 2, 4 domains with score 3 (Domain 11 N/A)
    domain_scores = {i: 2 for i in range(1, 16)}
    for i in [1, 2, 3, 4]:
        domain_scores[i] = 3
    domain_scores[11] = None
    
    # total = 10 * 2 + 4 * 3 = 32
    # max = 56
    # CQI = (32 / 56) * 100 = 57.1%
    res = compute_cqi(domain_scores, domain_11_applicable=False)
    assert res.total_score == 32
    assert res.max_possible == 56
    assert res.cqi == 57.1
    assert res.band == "Silver"
