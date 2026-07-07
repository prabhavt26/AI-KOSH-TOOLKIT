import React from "react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowRight, Calendar, AlertCircle } from "lucide-react";
import { Assessment } from "../lib/types";

interface ScoreHistoryProps {
  assessments: Assessment[];
  onSelect: (id: string) => void;
}

export default function ScoreHistory({ assessments, onSelect }: ScoreHistoryProps) {
  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case "complete":
        return "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20";
      case "processing":
        return "bg-sky-500/10 text-sky-600 dark:text-sky-400 border-sky-500/20 animate-pulse";
      case "queued":
        return "bg-slate-500/10 text-slate-600 dark:text-slate-400 border-slate-500/20";
      default:
        return "bg-rose-500/10 text-rose-600 dark:text-rose-450 border-rose-500/20";
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return dateStr;
    }
  };

  if (assessments.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-8 rounded-xl border border-border bg-card text-center">
        <AlertCircle className="h-8 w-8 text-muted-foreground mb-2" />
        <p className="text-sm text-muted-foreground font-medium">No assessments found. Submit a dataset to start.</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden shadow-sm">
      <Table>
        <TableHeader className="bg-muted/40 border-b border-border">
          <TableRow>
            <TableHead className="font-bold text-foreground text-xs uppercase tracking-wider">Submitted</TableHead>
            <TableHead className="font-bold text-foreground text-xs uppercase tracking-wider">Format</TableHead>
            <TableHead className="font-bold text-foreground text-xs uppercase tracking-wider">Status</TableHead>
            <TableHead className="w-[120px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {assessments.map((a) => (
            <TableRow key={a.assessment_id} className="border-b border-border/50 hover:bg-muted/50 transition-colors">
              <TableCell className="text-xs text-foreground">
                <div className="flex items-center gap-1.5 font-medium">
                  <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                  {formatDate(a.submitted_at)}
                </div>
              </TableCell>
              <TableCell className="font-mono text-xs uppercase text-muted-foreground font-semibold">
                {a.file_format}
              </TableCell>
              <TableCell>
                <Badge className={`px-2 py-0.5 border text-[10px] uppercase font-bold rounded-md ${getStatusBadge(a.status)}`}>
                  {a.status}
                </Badge>
              </TableCell>
              <TableCell className="text-right">
                {a.status === "complete" ? (
                  <Button
                    size="sm"
                    variant="ghost"
                    className="text-xs text-accent hover:text-accent/90 hover:bg-accent/10 font-bold"
                    onClick={() => onSelect(a.assessment_id)}
                  >
                    View Result
                    <ArrowRight className="ml-1 h-3 w-3" />
                  </Button>
                ) : a.status === "failed" ? (
                  <span className="text-xs text-rose-600 dark:text-rose-400 font-semibold" title={a.error_message || "Unknown error"}>
                    Error
                  </span>
                ) : (
                  <Button
                    size="sm"
                    variant="ghost"
                    className="text-xs text-primary hover:text-primary/90 hover:bg-primary/10 font-bold animate-pulse"
                    onClick={() => onSelect(a.assessment_id)}
                  >
                    Polling...
                  </Button>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
