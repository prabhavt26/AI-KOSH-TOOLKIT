"use client"

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api/client";
import { MetadataForm } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { AlertCircle, ArrowLeft, ArrowRight, Upload, CheckCircle2, FileText, Settings, ShieldAlert, HeartHandshake, Zap, Paperclip } from "lucide-react";

interface UploadUrlResponse {
  upload_url: string;
  file_key: string;
  assessment_id: string;
}

const SECTIONS = [
  { id: "A", name: "Dataset Basics", icon: Settings },
  { id: "B", name: "Study & Population", icon: HeartHandshake },
  { id: "C", name: "Annotation & Labelling", icon: FileText },
  { id: "D", name: "Data Standards", icon: Zap },
  { id: "E", name: "Privacy & De-identification", icon: ShieldAlert },
  { id: "F", name: "Ethics & Governance", icon: HeartHandshake },
  { id: "G", name: "AI Readiness & Curation", icon: Zap },
  { id: "H", name: "Attachments", icon: Paperclip },
];

export default function UploadPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string>("");
  const [errorMsg, setErrorMsg] = useState<string>("");

  // Step 8 file states
  const [datasetFile, setDatasetFile] = useState<File | null>(null);
  const [dataDictFile, setDataDictFile] = useState<File | null>(null);
  const [provenanceFile, setProvenanceFile] = useState<File | null>(null);
  const [sopFile, setSopFile] = useState<File | null>(null);
  const [consentFile, setConsentFile] = useState<File | null>(null);

  // Form states matching types/index.ts
  const [formData, setFormData] = useState<Partial<MetadataForm>>({
    dataset_name: "",
    dataset_version: "1.0.0",
    dataset_type: "tabular",
    study_type: "observational",
    target_population: "",
    geographic_coverage: "national",
    age_range_min: undefined,
    age_range_max: undefined,
    sex_distribution: "both",
    num_sites: undefined,
    collection_start_date: "",
    collection_end_date: "",
    
    // Annotation
    annotation_methodology: "",
    num_annotators: undefined,
    irr_method: "",
    irr_value: undefined,
    annotator_qualifications: "clinician",
    
    // Standards
    dq_checks_applied: [],
    standards_used: "",
    data_dictionary_uploaded: false,
    
    // Privacy
    ethics_approval_ref: "",
    consent_type: "individual",
    deidentification_method: "HIPAA Safe Harbor",
    direct_identifiers_present: [],
    k_anonymity_value: undefined,
    location_granularity: "district",
    temporal_granularity: "month",
    rare_condition_flag: false,
    differential_privacy_applied: false,
    dp_epsilon: undefined,
    sensitivity_class: "standard",
    persistent_identifier: "",
    license_type: "Restricted — Data Use Agreement required",
    
    // AI / Curation
    synthetic_data_pct: undefined,
    synthetic_utility_evaluated: false,
    synthetic_privacy_tested: false,
    equity_analysis_performed: false,
    community_engagement: false,
    redressal_mechanism_exists: false,
    dua_required: true,
    named_steward_exists: false,
    dpdp_compliance_status: "not_applicable",
    access_control_method: "Data Use Agreement (DUA) required — verified user identity",
    linked_model_ids: [],
    provenance_pipeline_available: false,
    github_repo_url: "",
    changelog_provided: false,
    version_format: "semantic",
    sustainability_info_provided: false,
    feedback_mechanism_exists: false,
  });

  // Gate questions (local state to control visibility)
  const [hasAnnotatedData, setHasAnnotatedData] = useState<boolean>(false);
  const [hasSyntheticData, setHasSyntheticData] = useState<boolean>(false);
  const [hasEthicsApproval, setHasEthicsApproval] = useState<boolean>(false);
  const [hasNamedSteward, setHasNamedSteward] = useState<boolean>(false);
  const [hasLinkedModels, setHasLinkedModels] = useState<boolean>(false);
  const [rawLinkedModelsText, setRawLinkedModelsText] = useState<string>("");

  const updateField = (field: keyof MetadataForm, value: string | number | boolean | string[] | undefined) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const toggleArrayField = (field: "dq_checks_applied" | "direct_identifiers_present", item: string) => {
    setFormData((prev) => {
      const current = (prev[field] as string[]) || [];
      const updated = current.includes(item)
        ? current.filter((x) => x !== item)
        : [...current, item];
      return { ...prev, [field]: updated };
    });
  };

  // S3 upload worker
  const uploadToS3 = async (file: File): Promise<string> => {
    const ext = file.name.split(".").pop() || "csv";
    setUploadStatus(`Requesting upload slot for ${file.name}...`);
    const { upload_url, file_key } = await api.post<UploadUrlResponse>(
      "/api/v1/assess/upload-url",
      { filename: file.name, file_format: ext }
    );
    
    setUploadStatus(`Uploading ${file.name} to storage...`);
    const uploadResponse = await fetch(upload_url, {
      method: "PUT",
      headers: {
        "Content-Type": file.type || "application/octet-stream",
      },
      body: file,
    });

    if (!uploadResponse.ok) {
      throw new Error(`Failed to upload ${file.name} to S3 object storage.`);
    }

    return file_key;
  };

  const handleNext = () => {
    setErrorMsg("");
    // Step validation before advancing
    if (currentStep === 1) {
      if (!formData.dataset_name || formData.dataset_name.length < 5) {
        setErrorMsg("Dataset Name is required (minimum 5 characters).");
        return;
      }
      if (!formData.dataset_type) {
        setErrorMsg("Dataset Type is required.");
        return;
      }
    } else if (currentStep === 2) {
      if (!formData.target_population || formData.target_population.length < 20) {
        setErrorMsg("Target Population description is required (minimum 20 characters).");
        return;
      }
    } else if (currentStep === 3 && hasAnnotatedData) {
      if (!formData.annotation_methodology || formData.annotation_methodology.length < 50) {
        setErrorMsg("Annotation methodology description is required (minimum 50 characters).");
        return;
      }
      if (formData.num_annotators === undefined || formData.num_annotators < 1) {
        setErrorMsg("Number of annotators must be at least 1.");
        return;
      }
    }

    // Skip step 3 (Annotation) if dataset has no annotated data
    if (currentStep === 2 && !hasAnnotatedData) {
      setCurrentStep(4);
    } else {
      setCurrentStep((prev) => Math.min(prev + 1, 8));
    }
  };

  const handleBack = () => {
    setErrorMsg("");
    if (currentStep === 4 && !hasAnnotatedData) {
      setCurrentStep(2);
    } else {
      setCurrentStep((prev) => Math.max(prev - 1, 1));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    
    if (!datasetFile) {
      setErrorMsg("Please upload the main dataset file in Section H.");
      return;
    }

    setIsSubmitting(true);
    try {
      // 1. Upload main dataset file
      const mainFileKey = await uploadToS3(datasetFile);

      // 2. Upload supporting documents if present
      let ddKey = "";
      let provKey = "";
      let sopKey = "";
      let consentKey = "";

      if (dataDictFile) {
        ddKey = await uploadToS3(dataDictFile);
      }
      if (provenanceFile) {
        provKey = await uploadToS3(provenanceFile);
      }
      if (sopFile) {
        sopKey = await uploadToS3(sopFile);
      }
      if (consentFile) {
        consentKey = await uploadToS3(consentFile);
      }

      setUploadStatus("Registering quality assessment with the backend...");

      // Parse linked models
      const linked_model_ids = hasLinkedModels
        ? rawLinkedModelsText.split(",").map((x) => x.trim()).filter((x) => x.length > 0)
        : [];

      // Combine form data with S3 keys (custom payload)
      const payloadMetadata = {
        ...formData,
        data_dictionary_uploaded: !!dataDictFile || formData.data_dictionary_uploaded,
        provenance_pipeline_available: !!provenanceFile || formData.provenance_pipeline_available,
        linked_model_ids,
      };

      // Submit assessment
      const res = await api.post<{ assessment_id: string; status: string }>(
        "/api/v1/assess",
        {
          file_key: mainFileKey,
          metadata: payloadMetadata,
          data_dictionary_key: ddKey || undefined,
          pipeline_script_key: provKey || undefined,
          sop_key: sopKey || undefined,
          consent_doc_key: consentKey || undefined,
        }
      );

      setUploadStatus("Success! Redirecting to analysis dashboard...");
      router.push(`/dashboard/${res.assessment_id}`);
    } catch (err: unknown) {
      console.error(err);
      const msg = err instanceof Error ? err.message : "An error occurred during submission.";
      setErrorMsg(msg);
      setIsSubmitting(false);
    }
  };

  const progressPercentage = (currentStep / 8) * 100;

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-extrabold tracking-tight text-primary font-serif font-black">
          New Quality Assessment
        </h1>
        <p className="text-muted-foreground text-sm">
          Ingest and evaluate your dataset against the 15-domain MIDAS 2.0 quality and privacy standards.
        </p>
      </div>

      {/* Steps Visual Bar */}
      <div className="bg-secondary/35 border border-border/60 rounded-xl p-4 backdrop-blur-sm">
        <div className="flex justify-between items-center mb-3">
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Step {currentStep} of 8: {SECTIONS[currentStep - 1].name}
          </span>
          <span className="text-xs font-bold text-accent">
            {Math.round(progressPercentage)}% Complete
          </span>
        </div>
        <Progress value={progressPercentage} className="h-1.5 bg-background border border-border/30" />
        
        {/* Navigation Step Pills */}
        <div className="hidden md:flex justify-between mt-4">
          {SECTIONS.map((sec, idx) => {
            const isCompleted = idx + 1 < currentStep;
            const isActive = idx + 1 === currentStep;
            return (
              <div
                key={sec.id}
                className={`flex items-center gap-1.5 text-xs font-medium transition-colors ${
                  isActive
                    ? "text-accent"
                    : isCompleted
                    ? "text-emerald-400"
                    : "text-muted-foreground/75"
                }`}
              >
                <div
                  className={`flex h-5 w-5 items-center justify-center rounded-full text-[10px] border ${
                    isActive
                      ? "border-accent bg-accent/5"
                      : isCompleted
                      ? "border-emerald-500 bg-emerald-950/20"
                      : "border-border bg-background"
                  }`}
                >
                  {isCompleted ? "✓" : sec.id}
                </div>
                <span>{sec.name}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main Wizard Form Container */}
      <Card className="bg-card border border-border/50 shadow-lg">
        <form onSubmit={handleSubmit}>
          <CardContent className="pt-6 min-h-[400px]">
            {errorMsg && (
              <div className="mb-6 p-4 rounded-lg bg-red-950/40 border border-red-800/80 text-red-200 flex items-start gap-2.5 text-sm">
                <AlertCircle className="h-5 w-5 text-red-400 shrink-0 mt-0.5" />
                <div>{errorMsg}</div>
              </div>
            )}

            {/* STEP 1: DATASET BASICS */}
            {currentStep === 1 && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="dataset_name" className="text-foreground">Dataset Name *</Label>
                    <Input
                      id="dataset_name"
                      placeholder="e.g. Chest X-ray Tuberculosis Cohort"
                      value={formData.dataset_name}
                      onChange={(e) => updateField("dataset_name", e.target.value)}
                      className="bg-background border-border"
                    />
                    <p className="text-[11px] text-muted-foreground/75">Min 5 characters. Must be descriptive.</p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="dataset_version" className="text-foreground">Dataset Version</Label>
                    <Input
                      id="dataset_version"
                      placeholder="e.g. 1.0.0"
                      value={formData.dataset_version}
                      onChange={(e) => updateField("dataset_version", e.target.value)}
                      className="bg-background border-border"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="dataset_type" className="text-foreground">Dataset Type *</Label>
                    <select
                      id="dataset_type"
                      value={formData.dataset_type}
                      onChange={(e) => updateField("dataset_type", e.target.value)}
                      className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
                    >
                      <option value="tabular">Tabular (CSV, XLSX, Parquet)</option>
                      <option value="imaging">Imaging (DICOM, X-Ray, MRI)</option>
                      <option value="text">Text (Clinical notes, discharge summaries)</option>
                      <option value="multimodal">Multimodal (Image + tabular records)</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="persistent_identifier" className="text-foreground">Persistent Identifier (DOI / Registry ID)</Label>
                    <Input
                      id="persistent_identifier"
                      placeholder="e.g. 10.5281/zenodo.12345"
                      value={formData.persistent_identifier}
                      onChange={(e) => updateField("persistent_identifier", e.target.value)}
                      className="bg-background border-border"
                    />
                  </div>

                  <div className="space-y-2 md:col-span-2">
                    <Label htmlFor="license_type" className="text-foreground">License Type *</Label>
                    <select
                      id="license_type"
                      value={formData.license_type}
                      onChange={(e) => updateField("license_type", e.target.value)}
                      className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
                    >
                      <option value="CC BY 4.0">CC BY 4.0 (Attribution; Commercial allowed)</option>
                      <option value="CC BY-NC 4.0">CC BY-NC 4.0 (Attribution; Non-commercial)</option>
                      <option value="CC BY-NC-ND 4.0">CC BY-NC-ND 4.0 (Attribution; Non-commercial; No derivatives)</option>
                      <option value="CC BY-SA 4.0">CC BY-SA 4.0 (Share-alike)</option>
                      <option value="Government Open Data License (India)">Government Open Data License (India)</option>
                      <option value="Restricted — Data Use Agreement required">Restricted — Data Use Agreement required</option>
                      <option value="Proprietary / Custom license">Proprietary / Custom license</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* STEP 2: STUDY & POPULATION */}
            {currentStep === 2 && (
              <div className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="study_type" className="text-foreground">Study Type *</Label>
                  <select
                    id="study_type"
                    value={formData.study_type}
                    onChange={(e) => updateField("study_type", e.target.value)}
                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
                  >
                    <option value="RCT">Randomised Controlled Trial (RCT)</option>
                    <option value="cohort">Cohort study (prospective or retrospective)</option>
                    <option value="cross_sectional">Cross-sectional survey</option>
                    <option value="registry">Disease registry</option>
                    <option value="observational">Observational study (other)</option>
                    <option value="case_control">Case-control study</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="target_population" className="text-foreground">Target Population Description *</Label>
                  <textarea
                    id="target_population"
                    rows={3}
                    placeholder="Describe who was studied, including disease conditions, age limits, and setting (min 20 characters)..."
                    value={formData.target_population}
                    onChange={(e) => updateField("target_population", e.target.value)}
                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="geographic_coverage" className="text-foreground">Geographic Coverage *</Label>
                    <select
                      id="geographic_coverage"
                      value={formData.geographic_coverage}
                      onChange={(e) => updateField("geographic_coverage", e.target.value)}
                      className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
                    >
                      <option value="village">Village / Panchayat level</option>
                      <option value="taluk">Taluk / Block level</option>
                      <option value="district">District level</option>
                      <option value="state">State level</option>
                      <option value="national">National (multiple states)</option>
                      <option value="multi_country">Multi-country</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="num_sites" className="text-foreground">Number of Collection Sites</Label>
                    <Input
                      id="num_sites"
                      type="number"
                      placeholder="e.g. 5"
                      value={formData.num_sites || ""}
                      onChange={(e) => updateField("num_sites", e.target.value ? parseInt(e.target.value) : undefined)}
                      className="bg-background border-border"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="age_range_min" className="text-foreground">Min Age of Subjects</Label>
                    <Input
                      id="age_range_min"
                      type="number"
                      placeholder="e.g. 18"
                      value={formData.age_range_min ?? ""}
                      onChange={(e) => updateField("age_range_min", e.target.value ? parseInt(e.target.value) : undefined)}
                      className="bg-background border-border"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="age_range_max" className="text-foreground">Max Age of Subjects</Label>
                    <Input
                      id="age_range_max"
                      type="number"
                      placeholder="e.g. 65"
                      value={formData.age_range_max ?? ""}
                      onChange={(e) => updateField("age_range_max", e.target.value ? parseInt(e.target.value) : undefined)}
                      className="bg-background border-border"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="sex_distribution" className="text-foreground">Sex Distribution</Label>
                    <select
                      id="sex_distribution"
                      value={formData.sex_distribution}
                      onChange={(e) => updateField("sex_distribution", e.target.value)}
                      className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
                    >
                      <option value="both">Both male and female subjects</option>
                      <option value="male_only">Male subjects only</option>
                      <option value="female_only">Female subjects only</option>
                      <option value="not_specified">Not specified / not recorded</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-foreground">Collection Start & End Dates</Label>
                    <div className="flex gap-2">
                      <Input
                        type="date"
                        value={formData.collection_start_date ? String(formData.collection_start_date) : ""}
                        onChange={(e) => updateField("collection_start_date", e.target.value || undefined)}
                        className="bg-background border-border text-xs"
                      />
                      <Input
                        type="date"
                        value={formData.collection_end_date ? String(formData.collection_end_date) : ""}
                        onChange={(e) => updateField("collection_end_date", e.target.value || undefined)}
                        className="bg-background border-border text-xs"
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* STEP 3: ANNOTATION & LABELLING */}
            {currentStep === 3 && (
              <div className="space-y-6">
                <div className="p-4 rounded-lg bg-background border border-border space-y-4">
                  <Label className="text-foreground block text-base font-semibold">
                    Does this dataset contain annotated or expert-labeled data?
                  </Label>
                  <div className="flex gap-4">
                    <label className="flex items-center gap-2 cursor-pointer text-foreground">
                      <input
                        type="radio"
                        name="hasAnnotatedData"
                        checked={hasAnnotatedData}
                        onChange={() => setHasAnnotatedData(true)}
                        className="h-4 w-4 accent-accent"
                      />
                      <span>Yes, it contains labels/annotations</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer text-foreground">
                      <input
                        type="radio"
                        name="hasAnnotatedData"
                        checked={!hasAnnotatedData}
                        onChange={() => {
                          setHasAnnotatedData(false);
                          updateField("annotation_methodology", "");
                          updateField("num_annotators", undefined);
                          updateField("irr_value", undefined);
                        }}
                        className="h-4 w-4 accent-accent"
                      />
                      <span>No human-derived annotations</span>
                    </label>
                  </div>
                </div>

                {hasAnnotatedData && (
                  <div className="space-y-6 mt-4">
                    <div className="space-y-2">
                      <Label htmlFor="annotation_methodology" className="text-foreground">Annotation Methodology *</Label>
                      <textarea
                        id="annotation_methodology"
                        rows={3}
                        placeholder="Describe annotator background, software guidelines, and resolution protocol (min 50 characters)..."
                        value={formData.annotation_methodology}
                        onChange={(e) => updateField("annotation_methodology", e.target.value)}
                        className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
                      />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <Label htmlFor="annotator_qualifications" className="text-foreground">Annotator Qualifications *</Label>
                        <select
                          id="annotator_qualifications"
                          value={formData.annotator_qualifications}
                          onChange={(e) => updateField("annotator_qualifications", e.target.value)}
                          className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
                        >
                          <option value="clinician">Medical specialists (Clinicians/Radiologists)</option>
                          <option value="student">Medical students / Residents</option>
                          <option value="crowdsourced">Trained research assistants / Lay readers</option>
                          <option value="automated">Automated algorithm only</option>
                          <option value="mixed">Mixed levels</option>
                          <option value="other">Other</option>
                        </select>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="num_annotators" className="text-foreground">Number of Annotators *</Label>
                        <Input
                          id="num_annotators"
                          type="number"
                          placeholder="e.g. 2"
                          value={formData.num_annotators ?? ""}
                          onChange={(e) => updateField("num_annotators", e.target.value ? parseInt(e.target.value) : undefined)}
                          className="bg-background border-border"
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="irr_method" className="text-foreground">Inter-Rater Reliability (IRR) Method</Label>
                        <select
                          id="irr_method"
                          value={formData.irr_method}
                          onChange={(e) => updateField("irr_method", e.target.value)}
                          className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
                        >
                          <option value="">Not measured / Not applicable</option>
                          <option value="cohen_kappa">Cohen&apos;s Kappa</option>
                          <option value="fleiss_kappa">Fleiss&apos; Kappa</option>
                          <option value="icc">Intraclass Correlation (ICC)</option>
                          <option value="percentage">Percentage Agreement</option>
                        </select>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="irr_value" className="text-foreground">IRR Value (0.0 to 1.0)</Label>
                        <Input
                          id="irr_value"
                          type="number"
                          step="0.01"
                          placeholder="e.g. 0.85"
                          value={formData.irr_value ?? ""}
                          onChange={(e) => updateField("irr_value", e.target.value ? parseFloat(e.target.value) : undefined)}
                          className="bg-background border-border"
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* STEP 4: DATA STANDARDS & INTEROPERABILITY */}
            {currentStep === 4 && (
              <div className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="standards_used" className="text-foreground">Health Data Standards / Coding Systems *</Label>
                  <select
                    id="standards_used"
                    value={formData.standards_used}
                    onChange={(e) => updateField("standards_used", e.target.value)}
                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
                  >
                    <option value="SNOMED-CT">SNOMED CT</option>
                    <option value="ICD-10">ICD-10 or ICD-11</option>
                    <option value="LOINC">LOINC</option>
                    <option value="FHIR">FHIR interoperability schema</option>
                    <option value="Custom">Custom / Internal database coding</option>
                    <option value="None">No standard taxonomy applied</option>
                  </select>
                </div>

                <div className="space-y-3">
                  <Label className="text-foreground block">Automated Data Quality Checks Applied</Label>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {[
                      { id: "missing", label: "Completeness checks (missing value checks)" },
                      { id: "range", label: "Plausibility range validations (e.g. Age > 0)" },
                      { id: "schema", label: "Schema conformance checking" },
                      { id: "duplicates", label: "Duplicate record checks" },
                    ].map((check) => (
                      <label key={check.id} className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
                        <input
                          type="checkbox"
                          checked={formData.dq_checks_applied?.includes(check.id)}
                          onChange={() => toggleArrayField("dq_checks_applied", check.id)}
                          className="rounded border-border bg-background text-accent focus:ring-accent h-4 w-4"
                        />
                        <span>{check.label}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* STEP 5: PRIVACY & DE-IDENTIFICATION */}
            {currentStep === 5 && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="sensitivity_class" className="text-foreground">Data Sensitivity Class *</Label>
                    <select
                      id="sensitivity_class"
                      value={formData.sensitivity_class}
                      onChange={(e) => updateField("sensitivity_class", e.target.value)}
                      className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
                    >
                      <option value="standard">Standard (General health / Clinical cohorts)</option>
                      <option value="high_stigma">High Stigma (TB, HIV, STIs, Mental health, Caste)</option>
                      <option value="critical">Critical / Vulnerable (Refugee, Prisons, Tribal GPS)</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="deidentification_method" className="text-foreground">De-identification Method *</Label>
                    <select
                      id="deidentification_method"
                      value={formData.deidentification_method}
                      onChange={(e) => updateField("deidentification_method", e.target.value)}
                      className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
                    >
                      <option value="HIPAA Safe Harbor">HIPAA Safe Harbor (18 identifiers removed)</option>
                      <option value="k-Anonymity">k-Anonymity / l-Diversity</option>
                      <option value="Differential Privacy">Differential Privacy</option>
                      <option value="Pseudonymisation">Pseudonymisation / Tokenisation</option>
                      <option value="None">No de-identification applied</option>
                    </select>
                  </div>

                  {formData.deidentification_method === "k-Anonymity" && (
                    <div className="space-y-2">
                      <Label htmlFor="k_anonymity_value" className="text-foreground">Value of k (k-Anonymity)</Label>
                      <Input
                        id="k_anonymity_value"
                        type="number"
                        placeholder="e.g. 5"
                        value={formData.k_anonymity_value ?? ""}
                        onChange={(e) => updateField("k_anonymity_value", e.target.value ? parseInt(e.target.value) : undefined)}
                        className="bg-background border-border"
                      />
                    </div>
                  )}

                  <div className="space-y-3 md:col-span-2">
                    <Label className="text-foreground block">Direct Identifiers Present in Dataset</Label>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                      {[
                        { id: "name", label: "Full/Partial Names" },
                        { id: "phone", label: "Phone Numbers" },
                        { id: "email", label: "Email Addresses" },
                        { id: "aadhaar", label: "National ID (Aadhaar/PAN)" },
                        { id: "dob", label: "Full DOB (Day/Month/Year)" },
                        { id: "gps", label: "Exact GPS/Location" },
                      ].map((idField) => (
                        <label key={idField.id} className="flex items-center gap-2 text-xs text-foreground cursor-pointer">
                          <input
                            type="checkbox"
                            checked={formData.direct_identifiers_present?.includes(idField.id)}
                            onChange={() => toggleArrayField("direct_identifiers_present", idField.id)}
                            className="rounded border-border bg-background text-accent focus:ring-accent h-4 w-4"
                          />
                          <span>{idField.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="location_granularity" className="text-foreground">Location Granularity *</Label>
                    <select
                      id="location_granularity"
                      value={formData.location_granularity}
                      onChange={(e) => updateField("location_granularity", e.target.value)}
                      className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
                    >
                      <option value="village">Village / Block (Highly granular)</option>
                      <option value="district">District level</option>
                      <option value="state">State level</option>
                      <option value="national">National / Country only</option>
                      <option value="none">Removed</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="temporal_granularity" className="text-foreground">Temporal Granularity *</Label>
                    <select
                      id="temporal_granularity"
                      value={formData.temporal_granularity}
                      onChange={(e) => updateField("temporal_granularity", e.target.value)}
                      className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
                    >
                      <option value="day">Exact Date (Day/Month/Year)</option>
                      <option value="month">Month and Year</option>
                      <option value="year">Year only</option>
                      <option value="not_applicable">Removed</option>
                    </select>
                  </div>

                  <div className="p-3 bg-background border border-border rounded-lg flex items-center justify-between col-span-2">
                    <div className="space-y-0.5">
                      <Label htmlFor="rare_condition_flag" className="text-foreground font-semibold block">Rare Condition Flag</Label>
                      <span className="text-[11px] text-muted-foreground block">Does dataset contain rare diseases or fewer than 100 individuals?</span>
                    </div>
                    <input
                      id="rare_condition_flag"
                      type="checkbox"
                      checked={formData.rare_condition_flag}
                      onChange={(e) => updateField("rare_condition_flag", e.target.checked)}
                      className="rounded border-border bg-background text-accent focus:ring-accent h-5 w-5 cursor-pointer"
                    />
                  </div>

                  <div className="p-3 bg-background border border-border rounded-lg flex items-center justify-between col-span-2">
                    <div className="space-y-0.5">
                      <Label htmlFor="differential_privacy_applied" className="text-foreground font-semibold block">Differential Privacy Applied</Label>
                      <span className="text-[11px] text-muted-foreground block">Was calibrated mathematical noise added to the data records?</span>
                    </div>
                    <input
                      id="differential_privacy_applied"
                      type="checkbox"
                      checked={formData.differential_privacy_applied}
                      onChange={(e) => {
                        updateField("differential_privacy_applied", e.target.checked);
                        if (!e.target.checked) updateField("dp_epsilon", undefined);
                      }}
                      className="rounded border-border bg-background text-accent focus:ring-accent h-5 w-5 cursor-pointer"
                    />
                  </div>

                  {formData.differential_privacy_applied && (
                    <div className="space-y-2 col-span-2">
                      <Label htmlFor="dp_epsilon" className="text-foreground font-medium">Privacy Parameter Epsilon (ε) *</Label>
                      <Input
                        id="dp_epsilon"
                        type="number"
                        step="0.01"
                        placeholder="e.g. 1.0 (typically 0.1 - 5.0)"
                        value={formData.dp_epsilon ?? ""}
                        onChange={(e) => updateField("dp_epsilon", e.target.value ? parseFloat(e.target.value) : undefined)}
                        className="bg-background border-border"
                      />
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* STEP 6: ETHICS & GOVERNANCE */}
            {currentStep === 6 && (
              <div className="space-y-6">
                <div className="p-4 bg-background border border-border rounded-lg space-y-3">
                  <Label className="text-foreground block text-base font-semibold">Institutional Ethics Committee (IEC) Approval</Label>
                  <div className="flex gap-4">
                    <label className="flex items-center gap-2 cursor-pointer text-foreground text-sm">
                      <input
                        type="radio"
                        checked={hasEthicsApproval}
                        onChange={() => setHasEthicsApproval(true)}
                        className="h-4 w-4 accent-accent"
                      />
                      <span>Ethics Approval Granted</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer text-foreground text-sm">
                      <input
                        type="radio"
                        checked={!hasEthicsApproval}
                        onChange={() => {
                          setHasEthicsApproval(false);
                          updateField("ethics_approval_ref", "");
                        }}
                        className="h-4 w-4 accent-accent"
                      />
                      <span>No formal IRB approval / Waiver</span>
                    </label>
                  </div>
                </div>

                {hasEthicsApproval && (
                  <div className="space-y-2">
                    <Label htmlFor="ethics_approval_ref" className="text-foreground">Ethics Approval Reference ID *</Label>
                    <Input
                      id="ethics_approval_ref"
                      placeholder="e.g. AIIMS/IEC/2025/124"
                      value={formData.ethics_approval_ref}
                      onChange={(e) => updateField("ethics_approval_ref", e.target.value)}
                      className="bg-background border-border"
                    />
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="consent_type" className="text-foreground">Consent Obtained *</Label>
                    <select
                      id="consent_type"
                      value={formData.consent_type}
                      onChange={(e) => updateField("consent_type", e.target.value)}
                      className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
                    >
                      <option value="individual">Written informed individual consent</option>
                      <option value="waiver">Waiver granted by IRB</option>
                      <option value="community">Community-level consent</option>
                      <option value="not_applicable">Anonymised retrospective data</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="dpdp_compliance_status" className="text-foreground">DPDP Act (India) Compliance *</Label>
                    <select
                      id="dpdp_compliance_status"
                      value={formData.dpdp_compliance_status}
                      onChange={(e) => updateField("dpdp_compliance_status", e.target.value)}
                      className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
                    >
                      <option value="fully_compliant">Fully Compliant</option>
                      <option value="partially_compliant">Assessed (Gaps being addressed)</option>
                      <option value="not_compliant">Not yet assessed</option>
                      <option value="not_applicable">Not applicable</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[
                    { id: "equity_analysis_performed", label: "Equity / bias analysis performed" },
                    { id: "community_engagement", label: "Communities or patient groups engaged" },
                    { id: "redressal_mechanism_exists", label: "Consent withdrawal / redressal channel exists" },
                    { id: "dua_required", label: "Data Use Agreement (DUA) required for access" },
                  ].map((field) => (
                    <label key={field.id} className="flex items-center gap-2 text-sm text-foreground cursor-pointer p-2.5 rounded border border-border bg-background/30">
                      <input
                        type="checkbox"
                        checked={!!formData[field.id as keyof MetadataForm]}
                        onChange={(e) => updateField(field.id as keyof MetadataForm, e.target.checked)}
                        className="rounded border-border bg-background text-accent focus:ring-accent h-4 w-4"
                      />
                      <span>{field.label}</span>
                    </label>
                  ))}
                </div>

                <div className="p-3 bg-background border border-border rounded-lg flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label className="text-foreground font-semibold block">Named Data Steward Appointed</Label>
                    <span className="text-[11px] text-muted-foreground block">Is an individual/team officially responsible for data maintenance?</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={hasNamedSteward}
                    onChange={(e) => {
                      setHasNamedSteward(e.target.checked);
                      updateField("named_steward_exists", e.target.checked);
                    }}
                    className="rounded border-border bg-background text-accent focus:ring-accent h-5 w-5 cursor-pointer"
                  />
                </div>
              </div>
            )}

            {/* STEP 7: AI READINESS & CURATION */}
            {currentStep === 7 && (
              <div className="space-y-6">
                <div className="p-4 bg-background border border-border rounded-lg space-y-3">
                  <Label className="text-foreground block text-base font-semibold">Synthetic or Simulated Records</Label>
                  <div className="flex gap-4">
                    <label className="flex items-center gap-2 cursor-pointer text-foreground text-sm">
                      <input
                        type="radio"
                        checked={hasSyntheticData}
                        onChange={() => setHasSyntheticData(true)}
                        className="h-4 w-4 accent-accent"
                      />
                      <span>Yes, dataset includes synthetic data</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer text-foreground text-sm">
                      <input
                        type="radio"
                        checked={!hasSyntheticData}
                        onChange={() => {
                          setHasSyntheticData(false);
                          updateField("synthetic_data_pct", undefined);
                          updateField("synthetic_utility_evaluated", false);
                          updateField("synthetic_privacy_tested", false);
                        }}
                        className="h-4 w-4 accent-accent"
                      />
                      <span>Fully authentic patient data</span>
                    </label>
                  </div>
                </div>

                {hasSyntheticData && (
                  <div className="space-y-4 p-4 border border-border bg-accent/5 rounded-lg">
                    <div className="space-y-2">
                      <Label htmlFor="synthetic_data_pct" className="text-foreground">Synthetic Data Percentage (0 - 100) *</Label>
                      <Input
                        id="synthetic_data_pct"
                        type="number"
                        placeholder="e.g. 50"
                        value={formData.synthetic_data_pct ?? ""}
                        onChange={(e) => updateField("synthetic_data_pct", e.target.value ? parseFloat(e.target.value) : undefined)}
                        className="bg-background border-border"
                      />
                    </div>
                    <div className="flex flex-col gap-2 mt-3">
                      <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
                        <input
                          type="checkbox"
                          checked={formData.synthetic_utility_evaluated ?? false}
                          onChange={(e) => updateField("synthetic_utility_evaluated", e.target.checked)}
                          className="rounded border-border bg-background text-accent focus:ring-accent h-4 w-4"
                        />
                        <span>Statistical utility evaluated against authentic distribution</span>
                      </label>
                      <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
                        <input
                          type="checkbox"
                          checked={formData.synthetic_privacy_tested ?? false}
                          onChange={(e) => updateField("synthetic_privacy_tested", e.target.checked)}
                          className="rounded border-border bg-background text-accent focus:ring-accent h-4 w-4"
                        />
                        <span>Privacy risks (membership inference) tested on synthetic cohort</span>
                      </label>
                    </div>
                  </div>
                )}

                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-background border border-border rounded-lg">
                    <div>
                      <Label className="text-foreground font-semibold block">Public AI/ML Models Trained</Label>
                      <span className="text-[11px] text-muted-foreground block">Are there models built from this dataset available on AIKosh/HuggingFace?</span>
                    </div>
                    <input
                      type="checkbox"
                      checked={hasLinkedModels}
                      onChange={(e) => setHasLinkedModels(e.target.checked)}
                      className="rounded border-border bg-background text-accent focus:ring-accent h-5 w-5 cursor-pointer"
                    />
                  </div>
                  {hasLinkedModels && (
                    <Input
                      placeholder="Comma-separated model IDs (e.g. model_124, icmr-resnet-50)"
                      value={rawLinkedModelsText}
                      onChange={(e) => setRawLinkedModelsText(e.target.value)}
                      className="bg-background border-border"
                    />
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="version_format" className="text-foreground">Versioning Convention *</Label>
                    <select
                      id="version_format"
                      value={formData.version_format}
                      onChange={(e) => updateField("version_format", e.target.value)}
                      className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
                    >
                      <option value="semantic">Semantic (Major.Minor.Patch)</option>
                      <option value="arbitrary">Date-based or Arbitrary numbers</option>
                      <option value="none">No version tracking</option>
                    </select>
                  </div>

                  <div className="flex flex-col justify-end gap-3 pb-1">
                    <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.changelog_provided}
                        onChange={(e) => updateField("changelog_provided", e.target.checked)}
                        className="rounded border-border bg-background text-accent focus:ring-accent h-4 w-4"
                      />
                      <span>Changelog / Release notes provided</span>
                    </label>
                    <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.feedback_mechanism_exists}
                        onChange={(e) => updateField("feedback_mechanism_exists", e.target.checked)}
                        className="rounded border-border bg-background text-accent focus:ring-accent h-4 w-4"
                      />
                      <span>Feedback mechanism exists for users</span>
                    </label>
                  </div>

                  <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer p-3 bg-background border border-border rounded-lg col-span-2">
                    <input
                      type="checkbox"
                      checked={formData.sustainability_info_provided}
                      onChange={(e) => updateField("sustainability_info_provided", e.target.checked)}
                      className="rounded border-border bg-background text-accent focus:ring-accent h-4 w-4"
                    />
                    <div>
                      <span className="font-semibold text-foreground block">Carbon footprint or energy metrics evaluated</span>
                      <span className="text-[11px] text-muted-foreground block">Has storage/computation carbon emission or compression optimizations been calculated?</span>
                    </div>
                  </label>
                </div>
              </div>
            )}

            {/* STEP 8: ATTACHMENTS */}
            {currentStep === 8 && (
              <div className="space-y-6">
                <div className="p-4 rounded-lg border border-accent/20 bg-accent/5 space-y-4">
                  <div className="flex items-center gap-2 text-accent">
                    <Upload className="h-5 w-5" />
                    <span className="font-semibold text-sm">Primary Dataset File *</span>
                  </div>
                  <Input
                    type="file"
                    onChange={(e) => setDatasetFile(e.target.files?.[0] || null)}
                    className="bg-background border-border/50 cursor-pointer"
                  />
                  <p className="text-[11px] text-muted-foreground">Supports CSV, XLSX, Parquet, JSON. Recommended file size limit: 50MB for direct S3 upload.</p>
                  {datasetFile && (
                    <div className="text-xs text-emerald-400 flex items-center gap-1.5 mt-1 font-medium">
                      <CheckCircle2 className="h-4 w-4" /> Selected: {datasetFile.name} ({(datasetFile.size / 1024 / 1024).toFixed(2)} MB)
                    </div>
                  )}
                </div>

                <div className="space-y-4">
                  <h3 className="text-sm font-semibold text-foreground border-b border-border pb-2">Optional Supporting Documentation (Recommended)</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Q44 Data Dictionary */}
                    <div className="space-y-1.5 p-3 rounded-lg bg-background border border-border">
                      <Label className="text-xs font-semibold text-foreground">Data Dictionary (Q44)</Label>
                      <Input
                        type="file"
                        onChange={(e) => setDataDictFile(e.target.files?.[0] || null)}
                        className="bg-card border-border/50 cursor-pointer text-xs h-9"
                      />
                      {dataDictFile && <span className="text-[10px] text-emerald-400 block truncate">✓ {dataDictFile.name}</span>}
                    </div>

                    {/* Q45 Provenance Script */}
                    <div className="space-y-1.5 p-3 rounded-lg bg-background border border-border">
                      <Label className="text-xs font-semibold text-foreground">Data Processing Script / Code (Q45)</Label>
                      <Input
                        type="file"
                        onChange={(e) => setProvenanceFile(e.target.files?.[0] || null)}
                        className="bg-card border-border/50 cursor-pointer text-xs h-9"
                      />
                      {provenanceFile && <span className="text-[10px] text-emerald-400 block truncate">✓ {provenanceFile.name}</span>}
                    </div>

                    {/* Q47 Standard Operating Procedure */}
                    <div className="space-y-1.5 p-3 rounded-lg bg-background border border-border">
                      <Label className="text-xs font-semibold text-foreground">Standard Operating Procedure (SOP) (Q47)</Label>
                      <Input
                        type="file"
                        onChange={(e) => setSopFile(e.target.files?.[0] || null)}
                        className="bg-card border-border/50 cursor-pointer text-xs h-9"
                      />
                      {sopFile && <span className="text-[10px] text-emerald-400 block truncate">✓ {sopFile.name}</span>}
                    </div>

                    {/* Q48 Ethics/Consent Documentation */}
                    <div className="space-y-1.5 p-3 rounded-lg bg-background border border-border">
                      <Label className="text-xs font-semibold text-foreground">IEC Ethics Approval PDF (Q48)</Label>
                      <Input
                        type="file"
                        onChange={(e) => setConsentFile(e.target.files?.[0] || null)}
                        className="bg-card border-border/50 cursor-pointer text-xs h-9"
                      />
                      {consentFile && <span className="text-[10px] text-emerald-400 block truncate">✓ {consentFile.name}</span>}
                    </div>
                  </div>

                  <div className="space-y-2 mt-4">
                    <Label htmlFor="github_repo_url" className="text-foreground text-xs">Alternative Pipeline Code Repo URL (Q46)</Label>
                    <Input
                      id="github_repo_url"
                      placeholder="e.g. https://github.com/my-org/pipeline"
                      value={formData.github_repo_url}
                      onChange={(e) => updateField("github_repo_url", e.target.value)}
                      className="bg-background border-border text-xs h-9"
                    />
                  </div>
                </div>

                {isSubmitting && (
                  <div className="p-4 bg-card border border-border/50 rounded-lg flex items-center gap-3">
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent shrink-0"></div>
                    <span className="text-xs text-foreground font-semibold">{uploadStatus}</span>
                  </div>
                )}
              </div>
            )}
          </CardContent>

          {/* Wizard Footer Controls */}
          <div className="flex justify-between items-center bg-background/80 p-4 border-t border-border rounded-b-xl">
            <Button
              type="button"
              variant="outline"
              onClick={handleBack}
              disabled={currentStep === 1 || isSubmitting}
              className="border-border hover:bg-card hover:text-foreground text-xs"
            >
              <ArrowLeft className="h-4 w-4 mr-1.5" /> Back
            </Button>

            {currentStep < 8 ? (
              <Button
                type="button"
                onClick={handleNext}
                className="bg-primary hover:bg-primary/90 text-primary-foreground text-xs shadow-sm"
              >
                Next <ArrowRight className="h-4 w-4 ml-1.5" />
              </Button>
            ) : (
              <Button
                type="submit"
                disabled={isSubmitting}
                className="bg-primary hover:bg-primary/90 text-primary-foreground text-xs shadow-sm px-6"
              >
                {isSubmitting ? "Uploading & Analyzing..." : "Submit Quality Assessment"}
              </Button>
            )}
          </div>
        </form>
      </Card>
    </div>
  );
}
