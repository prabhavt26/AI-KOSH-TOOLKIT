from .base import BaseDomainScorer, DomainScoreResult

class DocumentationScorer(BaseDomainScorer):
    DOMAIN_NUMBER = 3
    DOMAIN_NAME = "Documentation & User Guidance"

    def score(self) -> DomainScoreResult:
        evidence = []
        gaps = []
        
        has_dict = self.metadata.get("data_dictionary_uploaded", False)
        has_ethics = bool(self.metadata.get("ethics_approval_ref"))
        has_consent = bool(self.metadata.get("consent_type"))
        has_repo = bool(self.metadata.get("github_repo_url"))
        
        items = 0
        if has_dict:
            items += 1
            evidence.append("Data dictionary uploaded.")
        else:
            gaps.append("Data dictionary missing.")
            
        if has_ethics:
            items += 1
            evidence.append(f"Ethics approval reference provided: {self.metadata.get('ethics_approval_ref')}")
        else:
            gaps.append("Ethics approval reference missing.")
            
        if has_consent:
            items += 1
            evidence.append(f"Consent type documented: {self.metadata.get('consent_type')}")
        else:
            gaps.append("Consent protocol description missing.")
            
        if has_repo:
            items += 1
            evidence.append(f"Public code repository provided: {self.metadata.get('github_repo_url')}")
        else:
            gaps.append("Code repository URL missing.")
            
        score = max(1, items)
        rationale = f"Score {score}: Found {items} of 4 core documentation components."
        
        return DomainScoreResult(
            domain_number=self.DOMAIN_NUMBER,
            domain_name=self.DOMAIN_NAME,
            score=score,
            rationale=rationale,
            evidence_items=evidence,
            gaps=gaps,
            confidence="Low"
        )
