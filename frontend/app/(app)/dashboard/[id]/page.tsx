"use client"

import React from "react";
import Link from "next/link";
import { useAssessmentStatus } from "@/hooks/use-assessment";
import CQIGauge from "@/components/cqi-gauge";
import PRSGauge from "@/components/prs-gauge";
import ReleaseBadge from "@/components/release-badge";
import DomainRadarChart from "@/components/domain-radar-chart";
import DomainScoreTable from "@/components/domain-score-table";
import GapPanel from "@/components/gap-panel";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { 
  ArrowLeft, Download, FileJson, FileText, CheckCircle2, AlertTriangle, ShieldCheck, 
  HelpCircle, BarChart3, Database, Calendar, Server, Info, ShieldAlert
} from "lucide-react";
import { AssessmentResultResponse } from "@/lib/types";

interface PageProps {
  params: { id: string };
}

export default function AssessmentDetailsPage({ params }: PageProps) {
  const id = params.id;
  const { data, isLoading, error } = useAssessmentStatus(id);

  if (isLoading) {
    return (
      <div className="flex h-[60vh] flex-col items-center justify-center gap-4">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent"></div>
        <span className="text-sm font-semibold tracking-wider text-slate-400">Loading assessment details...</span>
      </div>
    );
  }

  if (error || !data) {
    return (
      <Card className="max-w-xl mx-auto border-red-500/20 bg-red-950/10 p-6 text-center">
        <AlertTriangle className="h-12 w-12 text-rose-500 mx-auto mb-4" />
        <CardTitle className="text-lg text-slate-200">Failed to Load Assessment</CardTitle>
        <CardDescription className="text-sm text-slate-400 mt-2">
          {error?.message || "Assessment records could not be retrieved from the server."}
        </CardDescription>
        <Link href="/dashboard" passHref className="block mt-6">
          <Button variant="outline" className="border-slate-800 hover:bg-slate-900 text-xs">
            <ArrowLeft className="h-4 w-4 mr-1.5" /> Return to Dashboard
          </Button>
        </Link>
      </Card>
    );
  }

  // Active / Processing States
  if (data.status === "queued" || data.status === "processing") {
    return (
      <div className="max-w-2xl mx-auto space-y-6 pt-12">
        <Card className="bg-slate-900/60 backdrop-blur-md border-slate-800 p-8 text-center shadow-2xl space-y-6">
          <div className="relative h-20 w-20 mx-auto">
            <div className="absolute inset-0 rounded-full border-4 border-slate-800"></div>
            <div className="absolute inset-0 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <Server className="h-8 w-8 text-indigo-400 animate-pulse" />
            </div>
          </div>

          <div className="space-y-2">
            <CardTitle className="text-xl font-bold text-slate-100">Analyzing Dataset Quality</CardTitle>
            <CardDescription className="text-sm text-slate-400 max-w-md mx-auto">
              Our asynchronous Celery pipeline is currently parsing files, extracting profile statistics, and scoring the 15 quality dimensions.
            </CardDescription>
          </div>

          {/* Stepper display */}
          <div className="border border-slate-850 rounded-xl bg-slate-950/40 p-4 text-left max-w-md mx-auto space-y-3.5">
            <div className="flex items-center justify-between text-xs border-b border-slate-850 pb-2">
              <span className="text-slate-400">Assessment ID:</span>
              <span className="font-mono text-indigo-400">{data.assessment_id.slice(0, 8)}...</span>
            </div>
            
            <div className="space-y-2.5">
              <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400">
                <CheckCircle2 className="h-4 w-4" />
                <span>1. Ingesting from Object Storage</span>
              </div>
              <div className={`flex items-center gap-2 text-xs font-semibold ${data.status === "processing" ? "text-indigo-400" : "text-slate-500"}`}>
                <div className={`h-4 w-4 rounded-full border-2 ${data.status === "processing" ? "border-indigo-500 border-t-transparent animate-spin" : "border-slate-800"}`}></div>
                <span>2. Extracting Pandas Profiles & PII Scans</span>
              </div>
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-500">
                <div className="h-4 w-4 rounded-full border-2 border-slate-800"></div>
                <span>3. Executing 15-Domain Scorers</span>
              </div>
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-500">
                <div className="h-4 w-4 rounded-full border-2 border-slate-800"></div>
                <span>4. Generating Quality CQI, PRS & Webhooks</span>
              </div>
            </div>
          </div>

          <p className="text-[11px] text-slate-500 animate-pulse">
            This page will automatically refresh as processing finishes.
          </p>
        </Card>
      </div>
    );
  }

  // Failed State
  if (data.status === "failed") {
    return (
      <div className="max-w-2xl mx-auto pt-8">
        <Card className="border-rose-500/20 bg-rose-950/5 border p-8 space-y-6 shadow-2xl">
          <div className="flex items-center gap-3.5 border-b border-rose-950 pb-4">
            <ShieldAlert className="h-10 w-10 text-rose-500 shrink-0" />
            <div>
              <CardTitle className="text-lg font-bold text-slate-200">Assessment Execution Failed</CardTitle>
              <CardDescription className="text-xs text-rose-450 mt-0.5">
                The analysis worker encountered a fatal exception.
              </CardDescription>
            </div>
          </div>

          <div className="space-y-2">
            <Label className="text-xs text-slate-400 font-bold uppercase tracking-wider">Error Details</Label>
            <div className="rounded-lg bg-slate-950 border border-slate-850 p-4 font-mono text-xs text-rose-300 leading-relaxed overflow-x-auto">
              {data.error_message || "Unknown Celery worker execution error."}
            </div>
          </div>

          <div className="flex justify-between items-center pt-2">
            <Link href="/dashboard" passHref>
              <Button variant="outline" className="border-slate-800 hover:bg-slate-900 text-xs">
                <ArrowLeft className="h-4 w-4 mr-1.5" /> Return to Dashboard
              </Button>
            </Link>
            <Link href="/upload" passHref>
              <Button className="bg-indigo-600 hover:bg-indigo-500 text-xs">
                Retry Assessment Form
              </Button>
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  // Complete State - Render full AssessmentResultResponse
  const res = data as AssessmentResultResponse;
  
  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch (_) {
      return dateStr;
    }
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Detail Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-850 pb-6">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <Link href="/dashboard" className="text-slate-400 hover:text-slate-250 transition-colors">
              <ArrowLeft className="h-4 w-4" />
            </Link>
            <span className="text-xs font-mono uppercase tracking-wider text-slate-500 bg-slate-900 border border-slate-850 px-2 py-0.5 rounded-md">
              Assessment ID: {res.assessment_id.slice(0, 8)}
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-black text-slate-100">{res.dataset_name}</h1>
          
          <div className="flex flex-wrap items-center gap-3.5 text-xs text-slate-400 pt-1">
            <div className="flex items-center gap-1">
              <Calendar className="h-3.5 w-3.5 text-slate-500" />
              <span>Assessed: {formatDate(res.assessed_at)}</span>
            </div>
            <span>•</span>
            <div className="flex items-center gap-1">
              <Info className="h-3.5 w-3.5 text-slate-500" />
              <span>Toolkit v{res.toolkit_version}</span>
            </div>
          </div>
        </div>

        {/* Download Buttons */}
        <div className="flex gap-2 shrink-0">
          {res.report_urls?.pdf && (
            <a href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}${res.report_urls.pdf}`} target="_blank" rel="noopener noreferrer">
              <Button variant="outline" className="border-slate-800 hover:bg-slate-900 text-xs gap-1.5">
                <FileText className="h-4 w-4 text-rose-450" /> PDF Report
              </Button>
            </a>
          )}
          {res.report_urls?.html && (
            <a href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}${res.report_urls.html}`} target="_blank" rel="noopener noreferrer">
              <Button variant="outline" className="border-slate-800 hover:bg-slate-900 text-xs gap-1.5">
                <Download className="h-4 w-4 text-indigo-400" /> HTML Report
              </Button>
            </a>
          )}
          {res.report_urls?.json && (
            <a href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}${res.report_urls.json}`} target="_blank" rel="noopener noreferrer">
              <Button variant="outline" className="border-slate-800 hover:bg-slate-900 text-xs gap-1.5">
                <FileJson className="h-4 w-4 text-emerald-400" /> JSON Data
              </Button>
            </a>
          )}
        </div>
      </div>

      {/* Row 1: Core Metrics (Gauges + Classification) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <CQIGauge
          value={res.cqi.value}
          band={res.cqi.band}
          totalScore={res.cqi.total_score}
          maxPossible={res.cqi.max_possible}
          trace={res.cqi.formula_trace}
        />
        <PRSGauge
          value={res.prs.value}
          band={res.prs.band}
          baseline={res.prs.baseline_risk}
          multiplier={res.prs.sensitivity_multiplier}
          sensitivity={res.prs.sensitivity_class}
          trace={res.prs.computation_trace}
        />
        <ReleaseBadge
          classification={res.release.classification}
          justification={res.release.justification}
          policyOverrideApplied={res.release.policy_override_applied}
        />
      </div>

      {/* Row 2: Radar + Profile Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <DomainRadarChart scores={res.domain_scores} />

        {/* Profile Summary Card */}
        <Card className="border border-white/10 bg-slate-900/60 backdrop-blur-xl">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold tracking-wider text-slate-400 uppercase flex items-center gap-1.5">
              <BarChart3 className="h-4 w-4 text-indigo-400" />
              Dataset Statistics
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-2 space-y-4">
            <div className="grid grid-cols-2 gap-4 border-b border-slate-850 pb-4">
              <div className="space-y-0.5">
                <span className="text-[10px] uppercase font-bold text-slate-500">Row Count</span>
                <span className="text-xl font-bold text-slate-100">{res.profile_summary.rows.toLocaleString()}</span>
              </div>
              <div className="space-y-0.5">
                <span className="text-[10px] uppercase font-bold text-slate-500">Column Count</span>
                <span className="text-xl font-bold text-slate-100">{res.profile_summary.columns}</span>
              </div>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between items-center py-1">
                <span className="text-slate-400 font-medium">Format:</span>
                <span className="font-mono text-slate-200 uppercase">{res.profile_summary.file_format}</span>
              </div>
              <div className="flex justify-between items-center py-1">
                <span className="text-slate-400 font-medium">File Size:</span>
                <span className="text-slate-200">{(res.profile_summary.file_size_bytes / 1024 / 1024).toFixed(3)} MB</span>
              </div>
              <div className="flex justify-between items-center py-1">
                <span className="text-slate-400 font-medium">Completeness:</span>
                <span className="text-slate-200 font-semibold">{res.profile_summary.overall_completeness_pct.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between items-center py-1 border-t border-slate-850 pt-2 mt-2">
                <span className="text-slate-400 font-medium">PII Heuristics Detected:</span>
                <span className={`font-bold ${res.profile_summary.direct_identifiers_detected ? "text-rose-400" : "text-emerald-400"}`}>
                  {res.profile_summary.direct_identifiers_detected ? "Yes (PII Risk)" : "No"}
                </span>
              </div>
              <div className="flex justify-between items-center py-1">
                <span className="text-slate-400 font-medium">Standards Detected (ICD):</span>
                <span className={`font-bold ${res.profile_summary.icd_codes_detected ? "text-emerald-400" : "text-slate-500"}`}>
                  {res.profile_summary.icd_codes_detected ? "Present" : "None"}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Row 3: Detail Scores Table + Remediation Gaps */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-3">
          <h2 className="text-lg font-bold text-slate-100">15-Domain Score Breakdown</h2>
          <DomainScoreTable scores={res.domain_scores} />
        </div>
        <div className="space-y-3">
          <h2 className="text-lg font-bold text-slate-100">Remediation Guidance</h2>
          <GapPanel scores={res.domain_scores} />
        </div>
      </div>
    </div>
  );
}
