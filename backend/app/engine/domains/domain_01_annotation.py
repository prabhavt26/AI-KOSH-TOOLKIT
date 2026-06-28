from .base import BaseDomainScorer, DomainScoreResult

class AnnotationReliabilityScorer(BaseDomainScorer):
    DOMAIN_NUMBER = 1
    DOMAIN_NAME = "Annotation / Labelling Reliability"

    def score(self) -> DomainScoreResult:
        evidence = []
        gaps = []
        data_signals = 0
        meta_signals = 4

        annotation_methodology = self.metadata.get("annotation_methodology")
        num_annotators = self.metadata.get("num_annotators")
        irr_method = self.metadata.get("irr_method")
        irr_value = self.metadata.get("irr_value")
        annotator_qualifications = self.metadata.get("annotator_qualifications")

        if not annotation_methodology:
            gaps.append("No annotation methodology documented.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER,
                domain_name=self.DOMAIN_NAME,
                score=1,
                rationale="Annotation methodology not documented.",
                evidence_items=evidence,
                gaps=gaps,
                confidence="Low"
            )

        evidence.append("Annotation methodology documented.")
        
        # Check IRR
        if irr_value is None:
            gaps.append("No Inter-Rater Reliability (IRR) value reported.")
            score = 1
        else:
            irr_val_float = float(irr_value)
            evidence.append(f"IRR value reported: {irr_val_float} using method {irr_method or 'unknown'}")
            
            thresholds = self.criteria.get("thresholds", {}) if isinstance(self.criteria, dict) else {}
            irr_adequate = float(thresholds.get("irr_adequate", 0.6))
            irr_exemplary = float(thresholds.get("irr_exemplary", 0.8))
            
            if irr_val_float < irr_adequate:
                gaps.append(f"IRR value below acceptable threshold (<{irr_adequate}).")
                score = 2
            elif irr_val_float >= irr_adequate and irr_val_float < irr_exemplary:
                evidence.append(f"IRR value is adequate (>={irr_adequate}).")
                score = 3
            else:
                evidence.append(f"IRR value is exemplary (>={irr_exemplary}).")
                score = 4

        if num_annotators and int(num_annotators) >= 2:
            evidence.append(f"Multi-annotator team: {num_annotators} annotators.")
        else:
            gaps.append("Dataset was annotated by a single or unknown number of annotators.")
            if score > 2:
                score = 2

        if annotator_qualifications:
            evidence.append(f"Annotator qualifications documented: {annotator_qualifications}")
        else:
            gaps.append("Annotator credentials/qualifications not reported.")
            if score == 4:
                score = 3

        confidence = self._determine_confidence(data_signals, meta_signals)
        rationale = f"Score {score}: Annotation documented, IRR is {irr_value or 'absent'}."
        
        return DomainScoreResult(
            domain_number=self.DOMAIN_NUMBER,
            domain_name=self.DOMAIN_NAME,
            score=score,
            rationale=rationale,
            evidence_items=evidence,
            gaps=gaps,
            confidence=confidence
        )
