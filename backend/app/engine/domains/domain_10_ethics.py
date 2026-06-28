from .base import BaseDomainScorer, DomainScoreResult

class EthicsScorer(BaseDomainScorer):
    DOMAIN_NUMBER = 10
    DOMAIN_NAME = "Ethical & Social Accountability"

    def score(self) -> DomainScoreResult:
        evidence = []
        gaps = []
        
        ethics = self.metadata.get("ethics_approval_ref")
        consent = self.metadata.get("consent_type")
        equity = self.metadata.get("equity_analysis_performed", False)
        community = self.metadata.get("community_engagement", False)
        redress = self.metadata.get("redressal_mechanism_exists", False)
        
        if not ethics and not consent:
            gaps.append("Ethics approval reference and consent protocol missing.")
            score = 1
        elif ethics and not consent:
            evidence.append(f"Ethics approval reference: {ethics}")
            gaps.append("Consent protocol not described.")
            score = 1
        elif ethics and consent:
            evidence.append(f"Ethics approval reference: {ethics}")
            evidence.append(f"Consent type: {consent}")
            score = 2
            
            if equity or community:
                evidence.append(f"Social accountability (equity={equity}, community={community}) performed.")
                score = 3
                if redress:
                    evidence.append("Grievance redressal mechanism exists.")
                    score = 4
            else:
                gaps.append("No equity analysis or community engagement reported.")
        else:
            score = 1
            
        rationale = f"Score {score}: Ethics approval={bool(ethics)}, Consent={consent}."
        
        return DomainScoreResult(
            domain_number=self.DOMAIN_NUMBER,
            domain_name=self.DOMAIN_NAME,
            score=score,
            rationale=rationale,
            evidence_items=evidence,
            gaps=gaps,
            confidence="Low"
        )
