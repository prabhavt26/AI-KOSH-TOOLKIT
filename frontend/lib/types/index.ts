export interface User {
  id: string;
  email: string;
  role: "user" | "reviewer" | "admin";
  is_active: boolean;
  created_at: string;
}

export interface ApiKey {
  key_id: string;
  owner_name: string;
  key_prefix: string;
  role: string;
  is_active: boolean;
  created_at: string;
  last_used_at: string | null;
  expires_at: string | null;
}

export interface MetadataForm {
  dataset_name: string;
  dataset_version?: string;
  dataset_type: string;
  study_type: string;
  target_population: string;
  geographic_coverage: string;
  age_range_min?: number;
  age_range_max?: number;
  sex_distribution?: string;
  num_sites?: number;
  collection_start_date?: string;
  collection_end_date?: string;
  annotation_methodology?: string;
  num_annotators?: number;
  irr_method?: string;
  irr_value?: number;
  annotator_qualifications?: string;
  dq_checks_applied?: string[];
  standards_used: string;
  ethics_approval_ref?: string;
  consent_type?: string;
  deidentification_method: string;
  direct_identifiers_present?: string[];
  k_anonymity_value?: number;
  location_granularity?: string;
  temporal_granularity?: string;
  rare_condition_flag?: boolean;
  differential_privacy_applied?: boolean;
  sensitivity_class: "standard" | "high_stigma" | "critical";
  persistent_identifier?: string;
  license_type: string;
  synthetic_data_pct?: number;
  synthetic_utility_evaluated?: boolean;
  synthetic_privacy_tested?: boolean;
  equity_analysis_performed?: boolean;
  community_engagement?: boolean;
  redressal_mechanism_exists?: boolean;
  dua_required?: boolean;
  named_steward_exists?: boolean;
  dpdp_compliance_status?: string;
  access_control_method: string;
  linked_model_ids?: string[];
  data_dictionary_uploaded?: boolean;
  provenance_pipeline_available?: boolean;
  github_repo_url?: string;
  version_format?: string;
  changelog_provided?: boolean;
  sustainability_info_provided?: boolean;
  feedback_mechanism_exists?: boolean;
}

export interface DomainScore {
  domain_number: number;
  domain_name: string;
  score: number | null;
  max_score: number | null;
  not_applicable: boolean;
  inferred: boolean;
  confidence: "High" | "Medium" | "Low" | null;
  rationale: string;
  evidence_items: string[];
  gaps: string[];
}

export interface CQIResult {
  value: number;
  band: string;
  total_score: number;
  max_possible: number;
  formula_trace: string;
}

export interface PRSResult {
  value: number;
  band: string;
  baseline_risk: number;
  sensitivity_class: string;
  sensitivity_multiplier: number;
  adjusted_risk: number;
  computation_trace: string;
}

export interface ReleaseClassification {
  classification: "Open" | "Controlled" | "Restricted";
  justification: string;
  policy_override_applied: boolean;
}

export interface ProfileSummary {
  rows: number;
  columns: number;
  file_format: string;
  file_size_bytes: number;
  overall_completeness_pct: number;
  direct_identifiers_detected: boolean;
  icd_codes_detected: boolean;
  sampled: boolean;
}

export interface Assessment {
  assessment_id: string;
  dataset_id: string;
  user_id: string;
  status: "queued" | "processing" | "complete" | "failed";
  toolkit_version: string;
  domain_11_applicable: boolean;
  file_format: string;
  file_size_bytes: number;
  s3_file_key: string;
  submitted_at: string;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  error_traceback: string | null;
}

export interface AssessmentResultResponse {
  assessment_id: string;
  status: "complete";
  dataset_id: string;
  dataset_name: string;
  toolkit_version: string;
  assessed_at: string;
  domain_11_applicable: boolean;
  cqi: CQIResult;
  prs: PRSResult;
  release: ReleaseClassification;
  domain_scores: DomainScore[];
  profile_summary: ProfileSummary;
  report_urls: {
    json: string | null;
    html: string | null;
    pdf: string | null;
  };
  audit_log_id: string;
}
