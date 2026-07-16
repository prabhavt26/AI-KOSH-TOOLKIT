import React from "react";
import Link from "next/link";
import { Database, ShieldAlert } from "lucide-react";

export default function Footer() {
  return (
    <footer className="w-full border-t border-border/40 bg-background py-8 mt-auto">
      <div className="container mx-auto px-4 max-w-7xl">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          {/* Brand */}
          <div className="flex items-center gap-2 text-primary shrink-0">
            <Database className="h-4 w-4 text-accent" />
            <span className="font-serif font-bold text-sm tracking-wide">
              MIDAS <span className="text-accent">2.0 QUALITY TOOLKIT</span>
            </span>
          </div>

          {/* Links */}
          <div className="flex flex-wrap justify-center gap-6 text-xs text-muted-foreground font-semibold uppercase tracking-wider">
            <Link href="/" className="hover:text-primary transition-colors">Home</Link>
            <Link href="/lite-version" className="hover:text-primary transition-colors">Lite Spec</Link>
            <Link href="/technical-version" className="hover:text-primary transition-colors">Technical Spec</Link>
          </div>

          {/* Copyright/Disclaimer */}
          <div className="text-[10px] text-muted-foreground text-center md:text-right">
            <span>&copy; {new Date().getFullYear()} MIDAS 2.0. Powered by IndiaAI Mission.</span>
            <div className="flex items-center justify-center md:justify-end gap-1 mt-0.5 text-rose-500 font-bold">
              <ShieldAlert className="h-3 w-3" />
              <span>Expert Consensus Sandbox</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
