import os
import json
import logging
import tempfile
import traceback
from decimal import Decimal
import yaml
import pandas as pd
from uuid import UUID
from datetime import datetime, timezone
from typing import Dict, Any

from app.worker.celery_app import celery_app
from app.database import SessionLocal
from app.config import settings
from app.storage.s3_client import s3_client
from app.integration.aikosh_webhook import webhook
from app.audit.logger import audit_logger

# Models
from app.models.assessment import Assessment
from app.models.dataset_metadata import DatasetMetadata
from app.models.dataset_profile import DatasetProfile
from app.models.domain_score import DomainScore
from app.models.assessment_result import AssessmentResult

# Engines
from app.engine.ingestion.parser import DatasetParser
from app.engine.profiler.profiler import DatasetProfiler
from app.engine.scoring.cqi import compute_cqi
from app.engine.scoring.prs import compute_prs
from app.engine.scoring.release_classifier import ReleaseClassificationEngine
from app.engine.domains import DOMAIN_SCORERS
from app.reports.generator import report_generator

logger = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


domains_mapping = {
    1: ("1_annotation", "Annotation / Labelling Reliability"),
    2: ("2_metadata", "Metadata Completeness"),
    3: ("3_documentation", "Documentation & User Guidance"),
    4: ("4_representativeness", "Population Representativeness"),
    5: ("5_interoperability", "Data Structure & Interoperability"),
    6: ("6_ai_readiness", "AI / Analytics Readiness"),
    7: ("7_privacy", "Privacy & Identifiability"),
    8: ("8_security", "Security & Access Governance"),
    9: ("9_provenance", "Provenance & Workflow Transparency"),
    10: ("10_ethics", "Ethical & Social Accountability"),
    11: ("11_synthetic", "Synthetic / Simulated Data"),
    12: ("12_stewardship", "Stewardship & Governance"),
    13: ("13_model_linkage", "Model Linkage Integrity"),
    14: ("14_sustainability", "Environmental Sustainability"),
    15: ("15_curation", "Continuous Curation & Feedback")
}

@celery_app.task(name="app.worker.tasks.run_assessment", bind=True, max_retries=3)
def run_assessment(self, assessment_id: str, file_key: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Celery task running Ingestion -> Profiling -> Scoring -> Classification in background."""
    logger.info(f"Starting background assessment task {assessment_id} for file {file_key}")
    
    workspace_dir = os.getenv("WORKSPACE_DIR", os.getcwd())
    if not os.path.exists(workspace_dir):
        workspace_dir = "/app"
        
    temp_dir = os.path.join(workspace_dir, "temp_data")
    os.makedirs(temp_dir, exist_ok=True)
    
    temp_file_path = None
    
    with SessionLocal() as db:
        try:
            # Step 1: Update status -> processing
            assessment = db.query(Assessment).filter(Assessment.assessment_id == assessment_id).first()
            if not assessment:
                raise ValueError(f"Assessment with ID {assessment_id} not found in database.")
            
            assessment.status = "processing"
            db.commit()
            
            # Step 2: audit_event("assessment_started")
            audit_logger.log_event_sync(
                db,
                UUID(assessment_id),
                "assessment_started",
                {"file_key": file_key},
                "worker",
                "INFO"
            )

            # Step 3: Load metadata from DB
            metadata_rec = db.query(DatasetMetadata).filter(DatasetMetadata.assessment_id == assessment_id).first()
            if not metadata_rec:
                raise ValueError(f"Metadata for assessment {assessment_id} not found.")
            metadata_dict = {k: v for k, v in metadata_rec.__dict__.items() if not k.startswith('_')}
            if metadata_rec.raw_form_json and isinstance(metadata_rec.raw_form_json, dict):
                metadata_dict.update({k: v for k, v in metadata_rec.raw_form_json.items() if k not in metadata_dict or metadata_dict[k] is None})

            # Step 4: Download dataset file from S3 using file_key
            logger.info(f"Downloading file {file_key} from S3...")
            file_bytes = s3_client.download_file(file_key)
            
            # Write file_bytes to temp file
            temp_file = tempfile.NamedTemporaryFile(dir=temp_dir, suffix=f".{assessment.file_format}", delete=False)
            temp_file.write(file_bytes)
            temp_file.close()
            temp_file_path = temp_file.name

            # Parse DataFrame based on file format
            logger.info(f"Parsing dataset file in format: {assessment.file_format}")
            fmt = (assessment.file_format or "csv").lower()
            try:
                if fmt == "csv":
                    df = DatasetParser.parse_csv(file_bytes)
                elif fmt == "parquet":
                    df = DatasetParser.parse_parquet(file_bytes)
                elif fmt in ["xlsx", "xls"]:
                    df = DatasetParser.parse_xlsx(file_bytes)
                elif fmt == "json":
                    df = DatasetParser.parse_json(file_bytes)
                elif fmt == "dcm":
                    df = DatasetParser.parse_dicom(file_bytes)
                else:
                    df = DatasetParser.parse_csv(file_bytes)
            except Exception as parser_err:
                logger.warning(f"DatasetParser failed: {parser_err}. Creating empty DataFrame.")
                df = pd.DataFrame()

            # Step 5: Run profiler -> generate profile JSON -> store profile JSON to S3 -> write dataset_profiles record to DB
            logger.info("Running dataset profiler...")
            profiler = DatasetProfiler(df)
            profile_json = profiler.profile_dataset()
            profile_json["file"]["size_bytes"] = len(file_bytes)
            profile_json["file"]["format"] = fmt
            profile_json["file"]["filename"] = os.path.basename(file_key)

            # Store profile JSON to S3
            profile_bytes = json.dumps(profile_json).encode("utf-8")
            profile_s3_key = f"profiles/{assessment_id}/profile.json"
            s3_client.upload_file(profile_bytes, profile_s3_key, content_type="application/json")

            # Write dataset_profiles record
            profile_rec = DatasetProfile(
                assessment_id=UUID(assessment_id),
                profile_json=profile_json,
                profiler_version="1.1.0"
            )
            db.add(profile_rec)
            db.commit()

            # Step 6: Run 15 domain scorers -> write 15 domain_scores records to DB
            logger.info("Running 15 real domain scorers...")
            
            # Load criteria
            criteria = {}
            try:
                criteria_path = "/app/config/domain_criteria.yaml"
                if not os.path.exists(criteria_path):
                    criteria_path = os.path.join(workspace_dir, "backend", "config", "domain_criteria.yaml")
                if os.path.exists(criteria_path):
                    with open(criteria_path, "r") as f:
                        criteria = yaml.safe_load(f) or {}
            except Exception as yaml_err:
                logger.warning(f"Could not load domain criteria yaml: {yaml_err}")

            domain_scores_list = []
            domain_scores_dict = {}
            
            for ScorerClass in DOMAIN_SCORERS:
                domain_number = ScorerClass.DOMAIN_NUMBER
                domain_name = ScorerClass.DOMAIN_NAME
                
                # Check Domain 11 applicability special case
                if domain_number == 11 and not assessment.domain_11_applicable:
                    score_val = None
                    not_applicable = True
                    rationale_val = "Dataset contains no synthetic or simulated data. Domain excluded from CQI calculation."
                    evidence_val = []
                    gaps_val = []
                    confidence_val = "Low"
                else:
                    domains_dict = criteria.get("domains", {}) if isinstance(criteria, dict) else {}
                    domain_criteria = domains_dict.get(domain_number, {}) or domains_dict.get(str(domain_number), {})
                    
                    try:
                        scorer_inst = ScorerClass(profile_json, metadata_dict, domain_criteria)
                        result = scorer_inst.score()
                        
                        # Extra protection for Domain 11 inside scorer
                        if domain_number == 11 and result.not_applicable:
                            score_val = None
                            not_applicable = True
                            rationale_val = result.rationale
                            evidence_val = []
                            gaps_val = []
                            confidence_val = "Low"
                        else:
                            score_val = result.score
                            not_applicable = result.not_applicable
                            rationale_val = result.rationale
                            evidence_val = result.evidence_items
                            gaps_val = result.gaps
                            confidence_val = result.confidence
                    except Exception as scorer_err:
                        logger.error(f"Error executing scorer for Domain {domain_number}: {scorer_err}")
                        score_val = 1
                        not_applicable = False
                        rationale_val = f"Scoring failed due to error: {str(scorer_err)} — defaulted to 1"
                        evidence_val = []
                        gaps_val = [f"Scoring failed: {str(scorer_err)}"]
                        confidence_val = "Low"
                
                ds = DomainScore(
                    assessment_id=UUID(assessment_id),
                    domain_number=domain_number,
                    domain_name=domain_name,
                    score=score_val,
                    not_applicable=not_applicable,
                    rationale=rationale_val,
                    evidence_items=evidence_val,
                    gaps=gaps_val,
                    confidence_level=confidence_val
                )
                db.add(ds)
                domain_scores_list.append(ds)
                domain_scores_dict[domain_number] = score_val
                
            db.commit()
            
            # Step 7: Compute CQI
            cqi_res = compute_cqi(domain_scores_dict, assessment.domain_11_applicable, criteria)

            # Step 8: Compute PRS
            prs_res = compute_prs(profile_json, metadata_dict, criteria)

            # Step 9: Run release classification
            domain_7_score_obj = next((ds for ds in domain_scores_list if ds.domain_number == 7), None)
            domain_7_passed = domain_7_score_obj is not None and domain_7_score_obj.score == 4
            dp_verified = bool(metadata_dict.get("differential_privacy_applied", False) and 
                               metadata_dict.get("dp_epsilon") is not None and 
                               domain_7_passed)
            
            release_res = ReleaseClassificationEngine.classify_release(
                cqi=cqi_res.cqi,
                prs=prs_res.prs,
                prs_band=prs_res.band,
                sensitivity_class=metadata_dict.get("sensitivity_class", "standard"),
                differential_privacy_verified=dp_verified,
                criteria=criteria
            )

            # Step 10: Generate reports (JSON + HTML + PDF) -> upload to S3
            report_summary = {
                "rows": profile_json.get("shape", {}).get("rows", 0),
                "columns": profile_json.get("shape", {}).get("columns", 0),
                "file_format": fmt,
                "file_size_bytes": len(file_bytes),
                "overall_completeness_pct": profile_json.get("completeness", {}).get("overall_pct", 100.0),
                "direct_identifiers_detected": profile_json.get("pii_scan", {}).get("direct_identifiers_detected", False),
                "icd_codes_detected": profile_json.get("standards_detected", {}).get("icd_codes_present", False),
                "sampled": False
            }
            
            report_data = {
                "assessment_id": assessment_id,
                "status": "complete",
                "dataset_id": assessment.dataset_id,
                "dataset_name": metadata_dict.get("dataset_name", "Unknown"),
                "toolkit_version": assessment.toolkit_version,
                "computed_at": datetime.now(timezone.utc).isoformat(),
                "domain_11_applicable": assessment.domain_11_applicable,
                "cqi": {
                    "value": cqi_res.cqi,
                    "band": cqi_res.band,
                    "total_score": cqi_res.total_score,
                    "max_possible": cqi_res.max_possible,
                    "formula_trace": cqi_res.formula_trace
                },
                "prs": {
                    "value": prs_res.prs,
                    "band": prs_res.band,
                    "baseline_risk": prs_res.baseline_risk,
                    "sensitivity_class": prs_res.sensitivity_class,
                    "sensitivity_multiplier": prs_res.sensitivity_multiplier,
                    "adjusted_risk": prs_res.adjusted_risk,
                    "computation_trace": prs_res.computation_trace,
                    "differential_privacy_applied": prs_res.differential_privacy_applied,
                    "epsilon": prs_res.epsilon
                },
                "release": {
                    "classification": release_res.classification,
                    "justification": release_res.justification,
                    "policy_override_applied": release_res.policy_override_applied
                },
                "domain_scores": [
                    {
                        "domain_number": ds.domain_number,
                        "domain_name": ds.domain_name,
                        "score": ds.score,
                        "max_score": None if ds.not_applicable else 4,
                        "not_applicable": ds.not_applicable,
                        "confidence": ds.confidence_level,
                        "rationale": ds.rationale,
                        "evidence_items": ds.evidence_items or [],
                        "gaps": ds.gaps or []
                    } for ds in domain_scores_list
                ],
                "profile_summary": report_summary
            }
            
            # Save JSON report
            json_bytes = json.dumps(report_data, indent=2, cls=DecimalEncoder).encode("utf-8")
            json_key = f"reports/{assessment_id}/report.json"
            s3_client.upload_file(json_bytes, json_key, "application/json")
            
            # Save HTML report
            html_content = report_generator.generate_html_report(report_data)
            html_bytes = html_content.encode("utf-8")
            html_key = f"reports/{assessment_id}/report.html"
            s3_client.upload_file(html_bytes, html_key, "text/html")
            
            # Save PDF report
            pdf_bytes = report_generator.generate_pdf_report(html_content)
            pdf_key = f"reports/{assessment_id}/report.pdf"
            s3_client.upload_file(pdf_bytes, pdf_key, "application/pdf")

            # Step 11: Write assessment_results record to DB
            res_record = AssessmentResult(
                assessment_id=UUID(assessment_id),
                cqi=cqi_res.cqi,
                cqi_band=cqi_res.band,
                total_domain_score=cqi_res.total_score,
                max_possible_score=cqi_res.max_possible,
                cqi_formula_trace=cqi_res.formula_trace,
                prs=prs_res.prs,
                prs_band=prs_res.band,
                prs_baseline_risk=prs_res.baseline_risk,
                prs_sensitivity_multiplier=prs_res.sensitivity_multiplier,
                prs_computation_trace=prs_res.computation_trace,
                release_classification=release_res.classification,
                classification_justification=release_res.justification,
                policy_override_applied=release_res.policy_override_applied,
                report_json_url=json_key,
                report_html_url=html_key,
                report_pdf_url=pdf_key
            )
            db.add(res_record)
            db.commit()

            # Step 12: Update assessment status -> complete, set completion_timestamp
            assessment.status = "complete"
            assessment.completion_timestamp = datetime.now(timezone.utc)
            db.commit()
            
            # Create completed audit event log
            complete_audit = audit_logger.log_event_sync(
                db,
                UUID(assessment_id),
                "assessment_complete",
                {"cqi": cqi_res.cqi, "prs": prs_res.prs, "release_classification": release_res.classification},
                "worker",
                "INFO"
            )
            
            # Step 13: Dispatch webhook task (separate Celery queue: "webhook")
            domain_slugs = {
                1: "1_annotation_labelling_reliability",
                2: "2_metadata_completeness",
                3: "3_documentation_user_guidance",
                4: "4_population_representativeness",
                5: "5_data_structure_interoperability",
                6: "6_ai_analytics_readiness",
                7: "7_privacy_identifiability",
                8: "8_security_access_governance",
                9: "9_provenance_workflow_transparency",
                10: "10_ethical_social_accountability",
                11: "11_synthetic_simulated_data",
                12: "12_stewardship_governance",
                13: "13_model_linkage_integrity",
                14: "14_environmental_sustainability",
                15: "15_continuous_curation_feedback"
            }
            formatted_domain_scores = {}
            for ds in domain_scores_list:
                slug = domain_slugs.get(ds.domain_number, f"{ds.domain_number}_domain")
                formatted_domain_scores[slug] = {
                    "score": None if ds.not_applicable else ds.score,
                    "confidence": None if ds.not_applicable else ds.confidence_level
                }

            webhook_payload = {
                "assessment_id": assessment_id,
                "dataset_id": assessment.dataset_id,
                "assessed_at": datetime.now(timezone.utc).isoformat(),
                "toolkit_version": assessment.toolkit_version,
                "cqi": float(cqi_res.cqi),
                "cqi_band": cqi_res.band,
                "prs": int(prs_res.prs),
                "prs_band": prs_res.band,
                "release_classification": release_res.classification,
                "domain_scores": formatted_domain_scores,
                "api_base_url": os.getenv("API_BASE_URL", "http://localhost:8000"),
                "report_url": f"{os.getenv('API_BASE_URL', 'http://localhost:8000')}/api/v1/assess/{assessment_id}/report?format=html",
                "audit_log_id": str(complete_audit.log_id)
            }

            
            # Trigger send_webhook
            send_webhook.delay(assessment_id, settings.AIKOSH_WEBHOOK_URL, webhook_payload)

            return {
                "assessment_id": assessment_id,
                "status": "complete"
            }

        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Assessment {assessment_id} failed: {e}\n{tb}")
            
            try:
                db.rollback()
                assessment = db.query(Assessment).filter(Assessment.assessment_id == assessment_id).first()
                if assessment:
                    assessment.status = "failed"
                    assessment.error_message = str(e)
                    assessment.error_traceback = tb
                    db.commit()
                    
                    audit_logger.log_event_sync(
                        db,
                        UUID(assessment_id),
                        "assessment_failed",
                        {"error": str(e), "traceback": tb},
                        "worker",
                        "ERROR"
                    )
            except Exception as nested_err:
                logger.error(f"Error handling assessment failure database writes: {nested_err}")
            raise e
            
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception as cleanup_err:
                    logger.warning(f"Failed to remove temp file {temp_file_path}: {cleanup_err}")

@celery_app.task(name="app.worker.tasks.send_webhook", bind=True, max_retries=5)
def send_webhook(self, assessment_id: str, webhook_url: str, payload: Dict[str, Any]):
    """Sends quality metadata to AIKosh webhook. Runs on 'webhook' queue."""
    logger.info(f"Sending webhook for assessment {assessment_id} to {webhook_url}")
    
    if not webhook_url:
        logger.warning(f"No webhook URL configured. Skipping webhook post.")
        return
        
    try:
        success = webhook.post_quality_metadata_sync(webhook_url, payload)
        
        with SessionLocal() as db:
            if success:
                audit_logger.log_event_sync(
                    db,
                    UUID(assessment_id),
                    "aikosh_webhook_sent",
                    {"webhook_url": webhook_url},
                    "worker",
                    "INFO"
                )
            else:
                audit_logger.log_event_sync(
                    db,
                    UUID(assessment_id),
                    "webhook_failed",
                    {"webhook_url": webhook_url, "error": "Outbound post failed"},
                    "worker",
                    "WARNING"
                )
                raise Exception("Webhook post failed")
                
    except Exception as e:
        logger.error(f"Webhook dispatch failed: {e}")
        raise self.retry(exc=e, countdown=2 ** self.request.retries * 30)
