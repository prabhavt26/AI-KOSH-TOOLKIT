import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface CQIGaugeProps {
  value: number;
  band: string;
  totalScore: number;
  maxPossible: number;
  trace: string;
}

export default function CQIGauge({ value, band, totalScore, maxPossible, trace }: CQIGaugeProps) {
  // Get color based on band
  const getBandColorClass = (b: string) => {
    switch (b.toLowerCase()) {
      case "diamond":
        return "text-cyan-400 drop-shadow-[0_0_12px_rgba(34,211,238,0.5)]";
      case "platinum":
        return "text-indigo-400 drop-shadow-[0_0_12px_rgba(129,140,248,0.5)]";
      case "gold":
        return "text-amber-400 drop-shadow-[0_0_12px_rgba(251,191,36,0.5)]";
      case "silver":
        return "text-slate-300 drop-shadow-[0_0_12px_rgba(203,213,225,0.3)]";
      case "bronze":
        return "text-orange-500 drop-shadow-[0_0_12px_rgba(249,115,22,0.3)]";
      default:
        return "text-rose-500 drop-shadow-[0_0_12px_rgba(244,63,94,0.4)]";
    }
  };



  const circumference = 2 * Math.PI * 50;
  const strokeDashoffset = circumference - (value / 100) * circumference;

  return (
    <Card className="overflow-hidden border border-white/10 bg-slate-900/60 backdrop-blur-xl transition-all duration-300 hover:border-white/20">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold tracking-wider text-slate-400 uppercase">
          Quality Index (CQI)
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center pt-2">
        <div className="relative flex h-36 w-36 items-center justify-center">
          {/* Background circle */}
          <svg className="absolute top-0 left-0 h-full w-full -rotate-90">
            <circle
              cx="72"
              cy="72"
              r="50"
              className="fill-none stroke-slate-800"
              strokeWidth="10"
            />
            {/* Foreground circle with gradient */}
            <circle
              cx="72"
              cy="72"
              r="50"
              className={`fill-none transition-all duration-1000 ease-out`}
              strokeWidth="10"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              stroke="url(#cqiGradient)"
            />
            <defs>
              <linearGradient id="cqiGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" className="stop-color-cqi-start" />
                <stop offset="100%" className="stop-color-cqi-end" />
              </linearGradient>
            </defs>
            <style>{`
              .stop-color-cqi-start { stop-color: ${band.toLowerCase() === "diamond" ? "#22d3ee" : band.toLowerCase() === "platinum" ? "#818cf8" : band.toLowerCase() === "gold" ? "#fbbf24" : band.toLowerCase() === "silver" ? "#cbd5e1" : "#f97316"}; }
              .stop-color-cqi-end { stop-color: ${band.toLowerCase() === "diamond" ? "#2563eb" : band.toLowerCase() === "platinum" ? "#4f46e5" : band.toLowerCase() === "gold" ? "#d97706" : band.toLowerCase() === "silver" ? "#64748b" : "#dc2626"}; }
            `}</style>
          </svg>

          {/* Score display */}
          <div className="text-center z-10">
            <span className="text-3xl font-extrabold tracking-tight text-white">
              {value}%
            </span>
            <div className={`mt-0.5 text-xs font-bold uppercase tracking-wider ${getBandColorClass(band)}`}>
              {band}
            </div>
          </div>
        </div>

        <div className="mt-4 text-center">
          <p className="text-xs text-slate-400">
            Weighted Score: <span className="font-semibold text-slate-200">{totalScore}</span> / {maxPossible}
          </p>
          <p className="mt-1 font-mono text-[10px] text-slate-500" title="Formula calculation path">
            {trace}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
