"use client"

import React from "react";
import Link from "next/link";
import { Database, ArrowLeft, ListChecks } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function LiteVersionPage() {
  const domains = [
    { num: 1, name: "Annotation & Labelling Reliability", desc: "Verifies the methodology, protocols, and expertise involved in annotating the health records (e.g. expert reviewers, consensus rules)." },
    { num: 2, name: "Metadata Completeness", desc: "Evaluates standard descriptors, clinical codes (ICD), vocabulary systems, and completeness of descriptive tags." },
    { num: 3, name: "Documentation & User Guidance", desc: "Ensures comprehensive user guidelines, data dictionaries, standard operating procedures (SOPs), and pipeline documentation are provided." },
    { num: 4, name: "Population Representativeness", desc: "Assesses how well the cohort reflects target demographic spreads (age, gender, geographics, clinical subtypes)." },
    { num: 5, name: "Data Structure & Interoperability", desc: "Checks formatting compatibility with international health data models (e.g., FHIR, OMOP, DICOM)." },
    { num: 6, name: "AI / Analytics Readiness", desc: "Scores the dataset based on formatting standardisation, missingness limits, and statistical integrity for immediate AI training." },
    { num: 7, name: "Privacy & Identifiability", desc: "Analyzes direct/indirect identifiers, de-identification steps, and verify differential privacy inputs." },
    { num: 8, name: "Security & Access Governance", desc: "Evaluates authentication schemas, multi-tenant boundaries, log trails, and access authorization models." },
    { num: 9, name: "Provenance & Workflow Transparency", desc: "Traces lineage from source extraction steps, pipelines, software versions, and modification history." },
    { num: 10, name: "Ethical & Social Accountability", desc: "Verifies institutional approvals, informed consents, equity safeguards, and community engagement models." },
    { num: 11, name: "Synthetic / Simulated Data", desc: "Scores the fidelity, validity, and leakage verification steps of synthetic cohorts (if applicable)." },
    { num: 12, name: "Stewardship & Governance", desc: "Checks institutional commitments, persistent identifiers (DOIs), and long-term hosting/archival schemas." },
    { num: 13, name: "Model Linkage Integrity", desc: "Reviews the mapping consistency, version matching, and integrity when linked to computational models." },
    { num: 14, name: "Environmental Sustainability", desc: "Assesses storage compression metrics and processing efficiency ratios as sustainability proxies." },
    { num: 15, name: "Continuous Curation & Feedback", desc: "Scores version tracking schemas, feedback capture methods, and active user errata report logs." },
  ];

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans">
      {/* Standalone Public Header */}
      <header className="w-full border-b border-border/40 bg-background/80 backdrop-blur-md sticky top-0 z-50">
        <div className="container mx-auto flex h-16 items-center justify-between px-4 max-w-7xl">
          <Link href="/" className="flex items-center gap-2 font-bold text-primary transition hover:opacity-90">
            <Database className="h-5 w-5 text-accent" />
            <span className="tracking-wide font-serif text-lg">
              AIKOSH <span className="text-accent">TOOLKIT</span>
            </span>
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/login" passHref>
              <Button variant="outline" className="border-border hover:bg-muted text-xs font-bold uppercase">
                Sign In
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 container mx-auto px-4 py-12 max-w-5xl space-y-12 animate-fade-in">
        {/* Back navigation */}
        <div className="flex items-center gap-2">
          <Link href="/" className="flex items-center gap-1.5 text-xs font-bold text-muted-foreground hover:text-primary uppercase tracking-wider transition-colors">
            <ArrowLeft className="h-4 w-4" /> Back to Home
          </Link>
        </div>

        {/* Section Header */}
        <div className="space-y-4">
          <div className="inline-flex items-center gap-1.5 bg-accent/10 border border-accent/25 rounded-md px-3 py-1 text-xs font-bold text-accent uppercase tracking-wider">
            <ListChecks className="h-3.5 w-3.5" />
            <span>Specifications Reference</span>
          </div>
          <h1 className="text-4xl font-serif font-black tracking-tight text-primary">
            MIDAS 2.0 Lite Version Protocol
          </h1>
          <p className="text-muted-foreground text-sm max-w-2xl font-medium leading-relaxed">
            The Lite Version acts as a self-assessment dashboard run by dataset custodians. Through the intake wizard, creators answer 48 reverse-engineered domains questions regarding ethical permissions, schemas, standards, and data dictionary details.
          </p>
        </div>

        {/* Highlight Alert */}
        <div className="p-4 rounded-lg bg-secondary/30 border border-border/60 text-xs text-muted-foreground font-medium leading-relaxed">
          <strong>How scoring works:</strong> Each domain is evaluated on a scale of 0 to 4 based on self-reported inputs. If a domain is marked as not applicable (such as Domain 11 for non-synthetic datasets), it is excluded from the Composite Quality Index (CQI) calculations to avoid penalising the custodians.
        </div>

        {/* Spec Grid */}
        <div className="space-y-6">
          <h2 className="text-2xl font-serif font-bold text-primary border-b border-border/40 pb-2">The 15 Evaluated Quality Domains</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {domains.map((d) => (
              <div key={d.num} className="p-5 rounded-xl bg-card border border-border/30 shadow-sm space-y-2">
                <div className="flex items-center gap-2">
                  <span className="h-6 w-6 rounded-md bg-primary/10 text-primary text-xs font-bold flex items-center justify-center shrink-0">
                    {d.num}
                  </span>
                  <h3 className="font-serif font-bold text-sm text-primary">{d.name}</h3>
                </div>
                <p className="text-muted-foreground text-xs leading-relaxed font-medium pl-8">
                  {d.desc}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Calculations Info */}
        <div className="p-6 rounded-xl border border-border/40 bg-card space-y-4">
          <h3 className="text-lg font-serif font-bold text-primary">CQI-Lite and PRS-Lite Metric Calculations</h3>
          <p className="text-muted-foreground text-xs leading-relaxed font-medium">
            Once submitted, the toolkit runs an automated calculation to output two preliminary indices:
          </p>
          <ul className="list-disc list-inside text-xs text-muted-foreground space-y-2 pl-2 font-medium">
            <li><strong>CQI-Lite (Composite Quality Index)</strong>: The average score of all active domains normalized to a scale of 0–100.</li>
            <li><strong>PRS-Lite (Privacy Risk Score)</strong>: An identifiability risk rating computed based on sensitive columns, direct identifiers detected, and sensitive data class multipliers (e.g. genomic or stigma types).</li>
          </ul>
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full border-t border-border/40 bg-background py-8">
        <div className="container mx-auto px-4 max-w-7xl flex flex-col sm:flex-row justify-between items-center gap-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-2 text-primary">
            <Database className="h-4 w-4 text-accent" />
            <span className="font-serif font-bold text-sm tracking-wide">
              AIKOSH <span className="text-accent">QUALITY TOOLKIT</span>
            </span>
          </div>
          <span>&copy; {new Date().getFullYear()} AIKosh. Powered by IndiaAI Mission.</span>
        </div>
      </footer>
    </div>
  );
}
