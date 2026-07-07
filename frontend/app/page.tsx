"use client"

import React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { 
  Database, ArrowRight, Layers, ChartColumn, TriangleAlert, 
  FileText, ClipboardList, HelpCircle, ShieldCheck, Menu, X
} from "lucide-react";

export default function Home() {
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans">
      {/* Standalone Public Header */}
      <header className="w-full border-b border-border/40 bg-background/80 backdrop-blur-md sticky top-0 z-50">
        <div className="container mx-auto flex h-16 items-center justify-between px-4 max-w-7xl">
          <Link href="/" className="flex items-center gap-2 font-bold text-primary transition hover:opacity-90 shrink-0">
            <Database className="h-5 w-5 text-accent" />
            <span className="tracking-wide font-serif text-lg">
              AIKOSH <span className="text-accent">TOOLKIT</span>
            </span>
          </Link>
          
          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-4 text-sm font-semibold uppercase tracking-wider text-muted-foreground">
            <Link href="/lite-version" className="hover:text-primary transition-colors text-xs">
              Lite Spec
            </Link>
            <Link href="/technical-version" className="hover:text-primary transition-colors text-xs">
              Technical Spec
            </Link>
            <Link href="/delphi-proposal" className="hover:text-primary transition-colors text-xs">
              Delphi Proposal
            </Link>
            <Link href="/login" passHref>
              <Button variant="outline" className="border-border hover:bg-muted text-xs font-bold font-sans uppercase">
                Sign In
              </Button>
            </Link>
          </div>

          {/* Mobile menu trigger */}
          <div className="flex md:hidden items-center">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="text-foreground hover:bg-muted"
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
          </div>
        </div>
      </header>

      {/* Mobile Menu Panel */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-border/40 bg-background/95 backdrop-blur-md px-4 py-4 space-y-4 animate-slide-in sticky top-16 z-55">
          <div className="space-y-1.5">
            <div className="text-[10px] uppercase font-bold tracking-widest text-muted-foreground px-2">Specifications</div>
            <Link
              href="/lite-version"
              onClick={() => setMobileMenuOpen(false)}
              className="block p-2 rounded-md text-sm font-semibold text-muted-foreground hover:bg-muted hover:text-primary transition-colors"
            >
              Lite Spec
            </Link>
            <Link
              href="/technical-version"
              onClick={() => setMobileMenuOpen(false)}
              className="block p-2 rounded-md text-sm font-semibold text-muted-foreground hover:bg-muted hover:text-primary transition-colors"
            >
              Technical Spec
            </Link>
            <Link
              href="/delphi-proposal"
              onClick={() => setMobileMenuOpen(false)}
              className="block p-2 rounded-md text-sm font-semibold text-muted-foreground hover:bg-muted hover:text-primary transition-colors"
            >
              Delphi Proposal
            </Link>
          </div>
          <div className="border-t border-border/40 pt-3">
            <Link href="/login" passHref className="block w-full">
              <Button onClick={() => setMobileMenuOpen(false)} className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-bold uppercase tracking-wider text-xs">
                Sign In
              </Button>
            </Link>
          </div>
        </div>
      )}

      <main className="flex-grow animate-fade-in">
        {/* Hero Section */}
        <section className="relative overflow-hidden py-16 lg:py-24 bg-gradient-to-b from-secondary/40 via-background to-background bg-grid-dots">
          <div className="container mx-auto px-4 max-w-7xl relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            <div className="lg:col-span-7 space-y-6 text-left">
              <div className="inline-flex items-center gap-2 bg-accent/10 border border-accent/25 rounded-full px-4 py-1 text-xs font-bold text-accent uppercase tracking-wider">
                <ShieldCheck className="h-3.5 w-3.5" />
                <span>MIDAS 2.0 Quality Framework</span>
              </div>
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-serif font-black tracking-tight text-primary leading-tight">
                Automated Health Dataset <span className="text-accent">Quality Scoring</span>
              </h1>
              <p className="text-muted-foreground text-base sm:text-lg max-w-xl font-medium leading-relaxed">
                AIKosh&apos;s standalone full-stack toolkit for scoring health research datasets across 15 domains, calculating Privacy Risk Scores, and generating release classifications.
              </p>
              <div className="flex flex-wrap gap-4 pt-4">
                <Link href="/dashboard" passHref>
                  <Button className="bg-primary hover:bg-primary/90 text-primary-foreground font-bold px-8 py-5 rounded-lg text-xs gap-2 shadow-lg shadow-primary/15 transition-all">
                    Access Toolkit Dashboard <ArrowRight className="h-4 w-4 text-accent" />
                  </Button>
                </Link>
                <Link href="/register" passHref>
                  <Button variant="outline" className="border-border hover:bg-secondary/40 font-bold px-8 py-5 rounded-lg text-xs transition-all">
                    Create Account
                  </Button>
                </Link>
              </div>
            </div>

            {/* Graphic Illustration */}
            <div className="lg:col-span-5 relative flex justify-center lg:justify-end">
              <div className="relative w-full max-w-[380px] h-[340px]">
                <div className="absolute -top-10 -left-10 w-40 h-40 bg-accent/10 rounded-full blur-2xl animate-pulse"></div>
                <div className="absolute -bottom-10 -right-10 w-40 h-40 bg-primary/10 rounded-full blur-2xl animate-pulse"></div>
                
                {/* Micro card 1 */}
                <div className="absolute top-4 left-0 w-64 p-4 rounded-xl bg-card/85 backdrop-blur shadow-lg border border-border/40 z-0 space-y-2.5">
                  <div className="flex justify-between items-center text-[10px] font-bold text-muted-foreground uppercase tracking-wide">
                    <span>Privacy Risk Analysis</span>
                    <span className="text-emerald-600 font-bold">Low Risk</span>
                  </div>
                  <div className="flex items-baseline gap-1.5">
                    <span className="text-2xl font-serif font-black text-primary">12</span>
                    <span className="text-xs text-muted-foreground">/ 100 PRS</span>
                  </div>
                  <div className="h-1.5 w-full bg-secondary/80 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-500 rounded-full" style={{ width: "12%" }}></div>
                  </div>
                  <p className="text-[9px] text-muted-foreground leading-relaxed font-semibold">
                    No direct identifiers found. Basic demographic values masked.
                  </p>
                </div>

                {/* Micro card 2 */}
                <div className="absolute bottom-4 right-0 w-72 p-5 rounded-2xl bg-card/90 backdrop-blur-md shadow-xl border border-border/50 z-10 space-y-4">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-accent">
                      <Layers className="h-3.5 w-3.5" />
                      <span>Report Summary</span>
                    </div>
                    <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-primary/10 text-primary uppercase tracking-wider border border-primary/20">
                      Diamond
                    </span>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="relative h-16 w-16 flex items-center justify-center shrink-0">
                      <svg className="absolute w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                        <path className="text-secondary" strokeWidth="2.5" stroke="currentColor" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                        <path className="text-accent" strokeDasharray="88, 100" strokeWidth="3" strokeLinecap="round" stroke="currentColor" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                      </svg>
                      <span className="text-base font-serif font-black text-primary">88</span>
                    </div>
                    <div>
                      <div className="text-xs font-serif font-bold text-primary">Composite Quality Index</div>
                      <div className="text-[10px] text-muted-foreground font-semibold leading-relaxed">
                        Excellent schema completeness and reliable metadata.
                      </div>
                    </div>
                  </div>
                  <div className="space-y-2 border-t border-border/30 pt-3">
                    <div className="flex justify-between text-[10px] font-semibold text-muted-foreground">
                      <span>Annotation Reliability</span>
                      <span className="text-primary font-bold">4.0 / 4</span>
                    </div>
                    <div className="flex justify-between text-[10px] font-semibold text-muted-foreground">
                      <span>Metadata Completeness</span>
                      <span className="text-primary font-bold">3.8 / 4</span>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          </div>
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] bg-accent/5 rounded-full blur-[140px] pointer-events-none z-0"></div>
        </section>

        {/* Stats Section */}
        <section className="py-12 border-y border-border/40 bg-secondary/20">
          <div className="container mx-auto px-4 max-w-7xl">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
              <div className="space-y-1.5 p-4 rounded-xl bg-card border border-border/30 shadow-sm">
                <div className="text-3xl font-black text-primary font-serif">15</div>
                <div className="text-xs uppercase font-bold tracking-wider text-muted-foreground">Quality Domains</div>
              </div>
              <div className="space-y-1.5 p-4 rounded-xl bg-card border border-border/30 shadow-sm">
                <div className="text-3xl font-black text-accent font-serif">0-100</div>
                <div className="text-xs uppercase font-bold tracking-wider text-muted-foreground">Composite Index (CQI)</div>
              </div>
              <div className="space-y-1.5 p-4 rounded-xl bg-card border border-border/30 shadow-sm">
                <div className="text-3xl font-black text-primary font-serif">0-100</div>
                <div className="text-xs uppercase font-bold tracking-wider text-muted-foreground">Privacy Risk Score (PRS)</div>
              </div>
              <div className="space-y-1.5 p-4 rounded-xl bg-card border border-border/30 shadow-sm">
                <div className="text-3xl font-black text-accent font-serif">3</div>
                <div className="text-xs uppercase font-bold tracking-wider text-muted-foreground">Export Formats (JSON/HTML/PDF)</div>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-20 bg-background">
          <div className="container mx-auto px-4 max-w-7xl space-y-12">
            <div className="text-center space-y-3">
              <h2 className="text-3xl sm:text-4xl font-serif font-black text-primary">Automated Ingestion & Multi-Tenant Scoring</h2>
              <p className="text-muted-foreground text-sm max-w-lg mx-auto font-medium">
                Upload datasets directly to secure S3 object storage to run our async pipeline scanners.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="p-6 rounded-xl bg-card border border-border/40 shadow-sm space-y-4 hover:shadow-md transition-shadow">
                <div className="h-10 w-10 rounded-lg bg-accent/10 flex items-center justify-center text-accent">
                  <Layers className="h-5 w-5" />
                </div>
                <h3 className="text-lg font-serif font-bold text-primary">15-Domain Evaluations</h3>
                <p className="text-muted-foreground text-xs leading-relaxed font-medium">
                  Scoring algorithms cover clinical metadata metadata completeness, annotation reliability, population representativeness, and AI readiness.
                </p>
              </div>

              <div className="p-6 rounded-xl bg-card border border-border/40 shadow-sm space-y-4 hover:shadow-md transition-shadow">
                <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                  <ChartColumn className="h-5 w-5" />
                </div>
                <h3 className="text-lg font-serif font-bold text-primary">Pandas Stat Profiler</h3>
                <p className="text-muted-foreground text-xs leading-relaxed font-medium">
                  Automatically scans columns for completion percentages, format anomalies, PII direct identifiers, and schema compliance.
                </p>
              </div>

              <div className="p-6 rounded-xl bg-card border border-border/40 shadow-sm space-y-4 hover:shadow-md transition-shadow">
                <div className="h-10 w-10 rounded-lg bg-accent/10 flex items-center justify-center text-accent">
                  <TriangleAlert className="h-5 w-5" />
                </div>
                <h3 className="text-lg font-serif font-bold text-primary">Privacy & Overrides</h3>
                <p className="text-muted-foreground text-xs leading-relaxed font-medium">
                  Adjusts baseline risk based on dataset stigma and evaluates differential privacy inputs to issue Open, Controlled, or Restricted classifications.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Specs Section */}
        <section className="py-20 bg-secondary/10 border-t border-border/40">
          <div className="container mx-auto px-4 max-w-7xl space-y-12">
            <div className="text-center space-y-3">
              <h2 className="text-3xl sm:text-4xl font-serif font-black text-primary">Specification & Framework Documentation</h2>
              <p className="text-muted-foreground text-sm max-w-lg mx-auto font-medium">
                Explore the detailed methodology rules that drive our evaluation algorithms.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="p-6 rounded-xl bg-card border border-border/40 shadow-sm flex flex-col justify-between hover:border-accent/40 transition-colors">
                <div className="space-y-3">
                  <FileText className="h-6 w-6 text-accent" />
                  <h3 className="text-lg font-serif font-bold text-primary">Lite Version Spec</h3>
                  <p className="text-muted-foreground text-xs leading-relaxed font-medium">
                    Self-assessment details mapping the 15 domains. Requires the dataset custodian to respond to the 48-question intake form.
                  </p>
                </div>
                <Link href="/lite-version" className="text-xs font-bold text-accent uppercase tracking-wider flex items-center gap-1 mt-6 hover:underline">
                  View Lite Spec <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>

              <div className="p-6 rounded-xl bg-card border border-border/40 shadow-sm flex flex-col justify-between hover:border-primary/45 transition-colors">
                <div className="space-y-3">
                  <ClipboardList className="h-6 w-6 text-primary" />
                  <h3 className="text-lg font-serif font-bold text-primary">Technical Version Spec</h3>
                  <p className="text-muted-foreground text-xs leading-relaxed font-medium">
                    Nodal center validator specifications. Requires direct database scans, programmatic evidence ingestion, and strict checks.
                  </p>
                </div>
                <Link href="/technical-version" className="text-xs font-bold text-primary uppercase tracking-wider flex items-center gap-1 mt-6 hover:underline">
                  View Technical Spec <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>

              <div className="p-6 rounded-xl bg-card border border-border/40 shadow-sm flex flex-col justify-between hover:border-accent/40 transition-colors">
                <div className="space-y-3">
                  <HelpCircle className="h-6 w-6 text-accent" />
                  <h3 className="text-lg font-serif font-bold text-primary">Delphi Proposal</h3>
                  <p className="text-muted-foreground text-xs leading-relaxed font-medium">
                    Emerging expert validation methodology. Experts rate statements on clarity scales to calculate Item-CVI and Kappa.
                  </p>
                </div>
                <Link href="/delphi-proposal" className="text-xs font-bold text-accent uppercase tracking-wider flex items-center gap-1 mt-6 hover:underline">
                  View Delphi Spec <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            </div>
          </div>
        </section>
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
