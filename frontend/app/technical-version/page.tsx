"use client"

import React from "react";
import Link from "next/link";
import { Database, ArrowLeft, CheckCircle2, ShieldAlert, Cpu, Search, FileCode } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function TechnicalVersionPage() {
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
          <div className="inline-flex items-center gap-1.5 bg-primary/10 border border-primary/25 rounded-md px-3 py-1 text-xs font-bold text-primary uppercase tracking-wider">
            <Cpu className="h-3.5 w-3.5" />
            <span>Specifications Reference</span>
          </div>
          <h1 className="text-4xl font-serif font-black tracking-tight text-primary">
            MIDAS 2.0 Technical Version Protocol
          </h1>
          <p className="text-muted-foreground text-sm max-w-2xl font-medium leading-relaxed">
            The Technical Version represents the automated audit scan performed by the toolkit worker pipeline. It verifies custodian claims with pandas-based structural data scans, PII validators, and cryptographic file checks.
          </p>
        </div>

        {/* Highlight Alert */}
        <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-rose-600 dark:text-rose-400 font-semibold flex items-start gap-2 leading-relaxed">
          <ShieldAlert className="h-4 w-4 shrink-0 mt-0.5" />
          <div>
            <strong>Stricter Evidence Verification:</strong> Unlike the claim-based Lite Mode, Technical Mode executes programmatic code to profile missingness, scan database schemas against standard dictionaries, verify consent artifacts, and enforce strict release thresholds.
          </div>
        </div>

        {/* Core Components */}
        <div className="space-y-6">
          <h2 className="text-2xl font-serif font-bold text-primary border-b border-border/40 pb-2">The Automated Scan Engines</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Component 1 */}
            <div className="p-5 rounded-xl bg-card border border-border/30 shadow-sm space-y-3">
              <Search className="h-5 w-5 text-accent" />
              <h3 className="font-serif font-bold text-sm text-primary">PII Regex Scanner</h3>
              <p className="text-muted-foreground text-xs leading-relaxed font-medium">
                Scans cells for sensitive structures: Aadhaar numbers, phone numbers, IP addresses, emails, and demographic identifiers.
              </p>
            </div>

            {/* Component 2 */}
            <div className="p-5 rounded-xl bg-card border border-border/30 shadow-sm space-y-3">
              <FileCode className="h-5 w-5 text-primary" />
              <h3 className="font-serif font-bold text-sm text-primary">Schema Code Alignment</h3>
              <p className="text-muted-foreground text-xs leading-relaxed font-medium">
                Checks values in tables against medical standard terminologies (e.g. validates if ICD-10 or SNOMED-CT standards are used).
              </p>
            </div>

            {/* Component 3 */}
            <div className="p-5 rounded-xl bg-card border border-border/30 shadow-sm space-y-3">
              <CheckCircle2 className="h-5 w-5 text-accent" />
              <h3 className="font-serif font-bold text-sm text-primary">Completeness Scanner</h3>
              <p className="text-muted-foreground text-xs leading-relaxed font-medium">
                Calculates the exact percentage of missing values per column, flagging columns that fall below the required 95% threshold.
              </p>
            </div>
          </div>
        </div>

        {/* Release Class Matrix */}
        <div className="p-6 rounded-xl border border-border/40 bg-card space-y-6">
          <div className="space-y-1.5">
            <h3 className="text-lg font-serif font-bold text-primary">The CQI &times; PRS Release Classification Matrix</h3>
            <p className="text-muted-foreground text-xs font-medium">
              Technical scores are cross-referenced to classify the dataset&apos;s final release status:
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-border/50 text-muted-foreground">
                  <th className="py-2 font-bold uppercase tracking-wider">CQI Score Band</th>
                  <th className="py-2 font-bold uppercase tracking-wider">PRS Low (0-15)</th>
                  <th className="py-2 font-bold uppercase tracking-wider">PRS Moderate (16-40)</th>
                  <th className="py-2 font-bold uppercase tracking-wider">PRS High/Very High</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/30 font-medium">
                <tr>
                  <td className="py-3 font-bold text-primary">Diamond / Platinum (&ge;85)</td>
                  <td className="py-3 text-emerald-600 dark:text-emerald-450 font-bold">Open</td>
                  <td className="py-3 text-amber-600 dark:text-amber-450 font-bold">Controlled</td>
                  <td className="py-3 text-rose-600 dark:text-rose-400 font-bold">Restricted</td>
                </tr>
                <tr>
                  <td className="py-3 font-bold text-primary">Gold (70-84)</td>
                  <td className="py-3 text-emerald-600 dark:text-emerald-450 font-bold">Open</td>
                  <td className="py-3 text-amber-600 dark:text-amber-450 font-bold">Controlled</td>
                  <td className="py-3 text-rose-600 dark:text-rose-400 font-bold">Restricted</td>
                </tr>
                <tr>
                  <td className="py-3 font-bold text-primary">Silver (50-69)</td>
                  <td className="py-3 text-amber-600 dark:text-amber-450 font-bold">Controlled</td>
                  <td className="py-3 text-amber-600 dark:text-amber-450 font-bold">Controlled</td>
                  <td className="py-3 text-rose-600 dark:text-rose-400 font-bold">Restricted</td>
                </tr>
                <tr>
                  <td className="py-3 font-bold text-rose-500">Bronze / Remediation (&lt;50)</td>
                  <td className="py-3 text-amber-600 dark:text-amber-450 font-bold">Controlled</td>
                  <td className="py-3 text-rose-600 dark:text-rose-400 font-bold">Restricted</td>
                  <td className="py-3 text-rose-600 dark:text-rose-400 font-bold">Restricted</td>
                </tr>
              </tbody>
            </table>
          </div>

          <p className="text-[10px] text-muted-foreground leading-relaxed font-semibold italic border-t border-border/30 pt-3">
            * Note: High-stigma clinical datasets or genomic cohorts default to Controlled status unless verified Differential Privacy (DP) controls with strict epsilon bounds are applied.
          </p>
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
