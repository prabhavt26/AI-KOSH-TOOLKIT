"use client"

import React from "react";
import Link from "next/link";
import { Database, ArrowLeft, Award, Scale } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function DelphiProposalPage() {
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
            <Scale className="h-3.5 w-3.5" />
            <span>Methodology Proposal</span>
          </div>
          <h1 className="text-4xl font-serif font-black tracking-tight text-primary">
            Delphi Consensus Framework
          </h1>
          <p className="text-muted-foreground text-sm max-w-2xl font-medium leading-relaxed">
            The expert Delphi validation protocol establishes statistical agreement across panels to refine and finalise the emerging MIDAS 2.0 metadata domain parameters.
          </p>
        </div>

        {/* Core Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-5 rounded-xl bg-card border border-border/40 shadow-sm space-y-2">
            <div className="text-xs uppercase font-bold tracking-wider text-muted-foreground">Item-level (I-CVI)</div>
            <div className="text-3xl font-black text-primary font-serif">&ge; 0.78</div>
            <p className="text-[11px] text-muted-foreground font-medium leading-relaxed">
              Minimum agreement ratio required for each individual domain checklist statement.
            </p>
          </div>

          <div className="p-5 rounded-xl bg-card border border-border/40 shadow-sm space-y-2">
            <div className="text-xs uppercase font-bold tracking-wider text-muted-foreground">Scale-level (S-CVI/Ave)</div>
            <div className="text-3xl font-black text-accent font-serif">&ge; 0.90</div>
            <p className="text-[11px] text-muted-foreground font-medium leading-relaxed">
              Average item-level validity score required across the entire scale framework.
            </p>
          </div>

          <div className="p-5 rounded-xl bg-card border border-border/40 shadow-sm space-y-2">
            <div className="text-xs uppercase font-bold tracking-wider text-muted-foreground">Modified Kappa (k*)</div>
            <div className="text-3xl font-black text-primary font-serif">&ge; 0.74</div>
            <p className="text-[11px] text-muted-foreground font-medium leading-relaxed">
              Corrects for chance agreement. Represents excellent consensus agreement.
            </p>
          </div>
        </div>

        {/* Statistical Formulas */}
        <div className="p-6 rounded-xl border border-border/40 bg-card space-y-6">
          <h2 className="text-xl font-serif font-bold text-primary border-b border-border/30 pb-2">Mathematical Formulations</h2>
          
          <div className="space-y-6 text-xs leading-relaxed font-medium">
            {/* Formula 1 */}
            <div className="space-y-2">
              <h3 className="font-bold text-primary text-sm">1. Item Content Validity Index (I-CVI)</h3>
              <p className="text-muted-foreground">
                Item-level clarity and relevance index, calculated as the proportion of experts giving a rating of 3 (relevant) or 4 (highly relevant) on a 4-point Likert scale:
              </p>
              <div className="p-4 rounded-lg bg-secondary/35 text-center font-mono text-xs text-primary border border-border/50 max-w-md mx-auto my-2">
                I-CVI = ( n_agree ) / N
              </div>
              <p className="text-[10px] text-muted-foreground italic">
                Where <span className="font-mono">n_agree</span> is the number of experts rating 3 or 4, and <span className="font-mono">N</span> is the total size of the expert panel.
              </p>
            </div>

            {/* Formula 2 */}
            <div className="space-y-2 border-t border-border/30 pt-4">
              <h3 className="font-bold text-primary text-sm">2. Probability of Chance Agreement (Pc)</h3>
              <p className="text-muted-foreground">
                Before computing the modified Kappa, the probability of random chance agreement must be resolved:
              </p>
              <div className="p-4 rounded-lg bg-secondary/35 text-center font-mono text-xs text-primary border border-border/50 max-w-md mx-auto my-2">
                Pc = [ N! / (A! * (N - A)!) ] * 0.5^N
              </div>
              <p className="text-[10px] text-muted-foreground italic">
                Where <span className="font-mono">N</span> is total experts, and <span className="font-mono">A</span> is the number of agreeing experts.
              </p>
            </div>

            {/* Formula 3 */}
            <div className="space-y-2 border-t border-border/30 pt-4">
              <h3 className="font-bold text-primary text-sm">3. Modified Kappa Agreement (k*)</h3>
              <p className="text-muted-foreground">
                Modified Kappa statistic corrects for the likelihood of chance consensus agreement across smaller panels:
              </p>
              <div className="p-4 rounded-lg bg-secondary/35 text-center font-mono text-xs text-primary border border-border/50 max-w-md mx-auto my-2">
                k* = ( I-CVI - Pc ) / ( 1 - Pc )
              </div>
            </div>
          </div>
        </div>

        {/* Process Flow */}
        <div className="p-6 rounded-xl border border-border/40 bg-card space-y-4">
          <h3 className="text-lg font-serif font-bold text-primary flex items-center gap-1.5">
            <Award className="h-5 w-5 text-accent" />
            Consensus Validation Cycle
          </h3>
          <p className="text-muted-foreground text-xs leading-relaxed font-medium">
            The validation proposal runs in iterative cycles:
          </p>
          <ol className="list-decimal list-inside text-xs text-muted-foreground space-y-2.5 pl-2 font-medium">
            <li><strong>Expert Recruitment</strong>: Health research, bioinformatics, and legal compliance experts join the panel.</li>
            <li><strong>Clarity Rating</strong>: Panelists review the scoring definitions of the 15 domains and cast their clarity rating.</li>
            <li><strong>Kappa Computation</strong>: The toolkit validator engine aggregates votes to calculate indices. Items failing the CVI &ge; 0.78 or Kappa &ge; 0.74 bounds are flagged for revision.</li>
            <li><strong>Consensus Realignment</strong>: Definitions are updated and re-evaluated until all parameters pass the agreement thresholds.</li>
          </ol>
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
