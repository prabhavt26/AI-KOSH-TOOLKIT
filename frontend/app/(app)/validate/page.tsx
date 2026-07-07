"use client"

import React, { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  Scale, Users, Info, Calculator, ArrowLeft
} from "lucide-react";
import Link from "next/link";

interface DomainRating {
  id: number;
  name: string;
  agrees: number; // Experts rating 3 or 4
  total: number;  // Total experts
}

export default function DelphiValidationPage() {
  const searchParams = useSearchParams();
  const assessmentId = searchParams.get("id") || "";
  const storageKey = assessmentId ? `delphi_ratings_${assessmentId}` : "delphi_ratings_default";

  const defaultRatings: DomainRating[] = [
    { id: 1, name: "Annotation & Labelling Reliability", agrees: 11, total: 12 },
    { id: 2, name: "Metadata Completeness", agrees: 10, total: 12 },
    { id: 3, name: "Documentation & User Guidance", agrees: 9, total: 12 },
    { id: 4, name: "Population Representativeness", agrees: 11, total: 12 },
    { id: 5, name: "Data Structure & Interoperability", agrees: 10, total: 12 },
    { id: 6, name: "AI / Analytics Readiness", agrees: 8, total: 12 },
    { id: 7, name: "Privacy & Identifiability", agrees: 11, total: 12 },
    { id: 8, name: "Security & Access Governance", agrees: 10, total: 12 },
    { id: 9, name: "Provenance & Workflow Transparency", agrees: 9, total: 12 },
    { id: 10, name: "Ethical & Social Accountability", agrees: 11, total: 12 },
  ];

  const [ratings, setRatings] = useState<DomainRating[]>(defaultRatings);

  // Load from local storage when assessmentId updates
  useEffect(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        try {
          setRatings(JSON.parse(saved));
        } catch {
          setRatings(defaultRatings);
        }
      } else {
        setRatings(defaultRatings);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [storageKey]);

  // Handle local simulation adjustments
  const adjustAgreement = (id: number, delta: number) => {
    const updated = ratings.map(r => {
      if (r.id === id) {
        const nextAgrees = Math.max(0, Math.min(r.total, r.agrees + delta));
        return { ...r, agrees: nextAgrees };
      }
      return r;
    });
    setRatings(updated);
    if (typeof window !== "undefined") {
      localStorage.setItem(storageKey, JSON.stringify(updated));
    }
  };

  // Calculations:
  // I-CVI = agrees / total
  const calculateCVI = (agrees: number, total: number) => agrees / total;

  const calculateKappa = (icvi: number, agrees: number, total: number) => {
    const factorial = (n: number): number => (n <= 1 ? 1 : n * factorial(n - 1));
    const combinations = factorial(total) / (factorial(agrees) * factorial(total - agrees));
    const pc = combinations * Math.pow(0.5, total);
    
    if (pc === 1) return 0;
    return (icvi - pc) / (1 - pc);
  };

  // Overall S-CVI/Ave = Average of all I-CVIs
  const icvis = ratings.map(r => calculateCVI(r.agrees, r.total));
  const scviAve = icvis.reduce((a, b) => a + b, 0) / ratings.length;

  return (
    <div className="space-y-8 font-sans animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-border pb-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            {assessmentId && (
              <Link href={`/dashboard/${assessmentId}`} className="text-muted-foreground hover:text-foreground transition-colors mr-1">
                <ArrowLeft className="h-4 w-4" />
              </Link>
            )}
            <div className="inline-flex items-center gap-1 bg-accent/10 border border-accent/25 rounded px-2.5 py-0.5 text-[10px] font-bold text-accent uppercase tracking-wider">
              <Scale className="h-3 w-3" />
              <span>Delphi Consensus Panel</span>
            </div>
          </div>
          <h1 className="text-3xl font-serif font-black tracking-tight text-primary">
            Expert Delphi Validation Panel
          </h1>
          {assessmentId ? (
            <p className="text-muted-foreground text-sm mt-1 max-w-2xl font-medium leading-relaxed">
              Evaluating consensus metrics for Dataset ID: <span className="font-mono text-accent">{assessmentId.slice(0, 8)}...</span>. Adjust the panel scores below.
            </p>
          ) : (
            <p className="text-muted-foreground text-sm mt-1 max-w-2xl font-medium leading-relaxed">
              Submit ratings to check consensus thresholds on the emerging MIDAS 2.0 quality domains. The dashboard aggregates expert inputs and displays corrected modified Kappa indexes.
            </p>
          )}
        </div>
      </div>

      {/* Discrepancy Note banner */}
      <div className="p-4 rounded-xl border border-accent/20 bg-accent/5 flex items-start gap-3">
        <Info className="h-5 w-5 text-accent shrink-0 mt-0.5" />
        <div className="text-xs text-muted-foreground leading-relaxed font-medium">
          <strong className="text-foreground">Consensus Calculation Sandbox:</strong> The backend API does not currently support multi-user consensus validation models (Logged as `D-001`). This panel simulates active consensus indexes entirely client-side using standard Delphi mathematical coefficients.
        </div>
      </div>

      {/* Top Level Consensus Gauges */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* S-CVI Index */}
        <Card className="bg-card border border-border shadow-sm">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs uppercase tracking-wider font-bold text-muted-foreground">Scale Validity (S-CVI/Ave)</CardDescription>
            <CardTitle className="text-3xl font-serif font-black text-primary">
              {scviAve.toFixed(3)}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between items-center text-[11px] font-semibold">
              <span className="text-muted-foreground">Target Threshold:</span>
              <span className="text-accent">&ge; 0.900</span>
            </div>
            <div className="w-full bg-muted rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all duration-500 ${scviAve >= 0.9 ? "bg-emerald-500" : "bg-amber-500"}`}
                style={{ width: `${scviAve * 100}%` }}
              ></div>
            </div>
            <span className="text-[10px] text-muted-foreground/80 block font-medium">
              {scviAve >= 0.9 ? "✓ Standard Met (Excellent scale clarity)" : "⚠ Below target threshold"}
            </span>
          </CardContent>
        </Card>

        {/* Panel Size */}
        <Card className="bg-card border border-border shadow-sm">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs uppercase tracking-wider font-bold text-muted-foreground">Active Panel Experts</CardDescription>
            <CardTitle className="text-3xl font-serif font-black text-primary flex items-center gap-1.5">
              <Users className="h-6 w-6 text-accent shrink-0" />
              12
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            <span className="text-[11px] text-muted-foreground font-medium block">
              Invited reviewers representing clinical research centres.
            </span>
            <span className="text-[10px] text-accent font-semibold">
              Status: Active Delphi Round 2
            </span>
          </CardContent>
        </Card>

        {/* Overall Status */}
        <Card className="bg-card border border-border shadow-sm">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs uppercase tracking-wider font-bold text-muted-foreground">Consensus Status</CardDescription>
            <CardTitle className="text-2xl font-serif font-black text-emerald-600 dark:text-emerald-450">
              {scviAve >= 0.9 ? "VALIDATED" : "PENDING REALIGNMENT"}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            <span className="text-[11px] text-muted-foreground font-medium block">
              Scale compliance rating based on the 10 core checklist items.
            </span>
            <span className="text-[10px] text-muted-foreground/85 font-medium block italic">
              * Minimum expert agreement per item: 78% (I-CVI &ge; 0.78)
            </span>
          </CardContent>
        </Card>
      </div>

      {/* Interactive Calculator and Lists */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Core Evaluated Domains List */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-lg font-serif font-bold text-primary flex items-center gap-2">
            <Calculator className="h-5 w-5 text-accent" />
            Consensus Sandbox Adjustment
          </h3>
          <p className="text-xs text-muted-foreground font-medium leading-relaxed">
            Adjust the number of agreeing experts (rating 3 or 4) for each domain statement to simulate CVI index changes and modified Kappa boundaries in real time.
          </p>

          <div className="space-y-3.5 pt-2">
            {ratings.map((r) => {
              const icvi = calculateCVI(r.agrees, r.total);
              const kappa = calculateKappa(icvi, r.agrees, r.total);
              const isMet = icvi >= 0.78 && kappa >= 0.74;

              return (
                <div key={r.id} className="p-4 rounded-xl border border-border bg-card shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] bg-primary/10 text-primary font-bold px-1.5 py-0.5 rounded">
                        D-{r.id.toString().padStart(2, "0")}
                      </span>
                      <h4 className="font-serif font-bold text-sm text-foreground">{r.name}</h4>
                    </div>
                    <div className="flex items-center gap-3 text-[11px] text-muted-foreground font-semibold">
                      <span>I-CVI: <strong className="text-primary">{icvi.toFixed(2)}</strong></span>
                      <span>•</span>
                      <span>Modified Kappa (k*): <strong className={isMet ? "text-emerald-600 dark:text-emerald-400" : "text-amber-600"}>{kappa.toFixed(2)}</strong></span>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0 self-end sm:self-center">
                    {/* Controls to adjust agrees */}
                    <div className="flex items-center border border-border rounded-lg bg-background overflow-hidden h-9">
                      <button 
                        onClick={() => adjustAgreement(r.id, -1)}
                        className="px-3 hover:bg-muted text-foreground font-bold border-r border-border text-sm h-full"
                        disabled={r.agrees <= 0}
                      >
                        -
                      </button>
                      <span className="px-4 font-mono font-bold text-xs text-primary min-w-[70px] text-center">
                        {r.agrees} / {r.total}
                      </span>
                      <button 
                        onClick={() => adjustAgreement(r.id, 1)}
                        className="px-3 hover:bg-muted text-foreground font-bold border-l border-border text-sm h-full"
                        disabled={r.agrees >= r.total}
                      >
                        +
                      </button>
                    </div>

                    <Badge className={`text-[10px] font-bold py-1 px-2.5 rounded ${isMet ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-450 border border-emerald-500/25" : "bg-amber-500/10 text-amber-600 border border-amber-500/25"}`}>
                      {isMet ? "PASSED" : "FAILED"}
                    </Badge>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Sidebar Info Panels */}
        <div className="space-y-6">
          <Card className="bg-card border border-border shadow-sm">
            <CardHeader className="pb-3 border-b border-border">
              <CardTitle className="text-sm font-bold text-foreground">Consensus Criteria Specifications</CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-4 text-xs font-semibold leading-relaxed">
              <div className="space-y-1">
                <span className="text-muted-foreground uppercase text-[10px] block">Item Acceptance Bound</span>
                <p className="text-foreground font-serif text-sm">Item-CVI &ge; 0.78</p>
                <span className="text-[10px] text-muted-foreground font-medium block leading-normal">
                  Requires at least 10 out of 12 experts to grade the statement as relevant (3) or highly relevant (4).
                </span>
              </div>

              <div className="space-y-1 border-t border-border pt-3">
                <span className="text-muted-foreground uppercase text-[10px] block">Chance-Corrected Index</span>
                <p className="text-foreground font-serif text-sm">Modified Kappa (k*) &ge; 0.74</p>
                <span className="text-[10px] text-muted-foreground font-medium block leading-normal">
                  Corrects for random agreement likelihood, which is high across small expert panels.
                </span>
              </div>

              <div className="space-y-1 border-t border-border pt-3">
                <span className="text-muted-foreground uppercase text-[10px] block">Scale Content Validity</span>
                <p className="text-foreground font-serif text-sm">S-CVI/Ave &ge; 0.90</p>
                <span className="text-[10px] text-muted-foreground font-medium block leading-normal">
                  Average clarity score computed across the entire standard structure must exceed 90%.
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
