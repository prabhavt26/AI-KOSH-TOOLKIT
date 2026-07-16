"use client"

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAssessments } from "@/hooks/use-assessment";
import { useApiKeys, useCreateApiKey, useRevokeApiKey } from "@/hooks/use-auth";
import ScoreHistory from "@/components/score-history";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Plus, Key, Trash2, Clipboard, Check, Database, ShieldAlert } from "lucide-react";

export default function DashboardPage() {
  const router = useRouter();
  const { data: assessments = [], isLoading: isLoadingAssessments } = useAssessments();
  const { data: apiKeys = [], isLoading: isLoadingKeys } = useApiKeys();
  const createApiKeyMutation = useCreateApiKey();
  const revokeApiKeyMutation = useRevokeApiKey();

  const [newKeyName, setNewKeyName] = useState("");
  const [createdKeyRaw, setCreatedKeyRaw] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyName.trim()) return;
    try {
      const res = await createApiKeyMutation.mutateAsync({ owner_name: newKeyName, role: "submitter" });
      setCreatedKeyRaw(res.raw_key);
      setNewKeyName("");
    } catch (err) {
      console.error(err);
    }
  };

  const handleRevokeKey = async (keyId: string) => {
    if (confirm("Are you sure you want to revoke this API key? External systems using it will be cut off immediately.")) {
      try {
        await revokeApiKeyMutation.mutateAsync(keyId);
      } catch (err) {
        console.error(err);
      }
    }
  };

  const handleCopyKey = () => {
    if (createdKeyRaw) {
      navigator.clipboard.writeText(createdKeyRaw);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Stats calculation
  const totalAssessments = assessments.length;
  const completedAssessments = assessments.filter(a => a.status === "complete").length;
  const processingAssessments = assessments.filter(a => a.status === "processing" || a.status === "queued").length;

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Dashboard Top Row */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-primary font-serif font-black">
            Quality & Privacy Dashboard
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Submit datasets for evaluation, review historical assessment runs, and manage developer keys.
          </p>
        </div>
        <Link href="/upload" passHref>
          <Button className="bg-primary hover:bg-primary/90 text-primary-foreground text-foreground text-xs font-semibold py-5 shadow-lg shadow-indigo-650/15">
            <Plus className="h-4 w-4 mr-1.5" /> New Assessment
          </Button>
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-card border-border shadow-sm">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs uppercase tracking-wider font-semibold text-muted-foreground">Total Runs</CardDescription>
            <CardTitle className="text-3xl font-black text-foreground">{totalAssessments}</CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-[10px] text-muted-foreground/75 font-medium">All dataset evaluations submitted</span>
          </CardContent>
        </Card>

        <Card className="bg-card border-border shadow-sm">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs uppercase tracking-wider font-semibold text-muted-foreground">Completed</CardDescription>
            <CardTitle className="text-3xl font-black text-emerald-600 dark:text-emerald-450">{completedAssessments}</CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-[10px] text-muted-foreground/75 font-medium">Reports generated successfully</span>
          </CardContent>
        </Card>

        <Card className="bg-card border-border shadow-sm">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs uppercase tracking-wider font-semibold text-muted-foreground">Processing</CardDescription>
            <CardTitle className="text-3xl font-black text-sky-600 dark:text-sky-400">{processingAssessments}</CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-[10px] text-muted-foreground/75 font-medium">Evaluating pipelines/scorers...</span>
          </CardContent>
        </Card>

        <Card className="bg-card border-border shadow-sm">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs uppercase tracking-wider font-semibold text-muted-foreground">API Keys</CardDescription>
            <CardTitle className="text-3xl font-black text-accent">{apiKeys.length}</CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-[10px] text-muted-foreground/75 font-medium">Active integration endpoints</span>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Assessment Runs Table */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center gap-2">
            <Database className="h-5 w-5 text-accent" />
            <h2 className="text-lg font-bold text-foreground">Historical Assessments</h2>
          </div>
          
          {isLoadingAssessments ? (
            <div className="h-64 rounded-xl border border-border bg-slate-900/20 flex flex-col items-center justify-center gap-2">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent"></div>
              <span className="text-xs text-muted-foreground font-medium">Retrieving evaluations...</span>
            </div>
          ) : (
            <ScoreHistory
              assessments={assessments}
              onSelect={(id) => router.push(`/dashboard/${id}`)}
            />
          )}
        </div>

        {/* API Key Management */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Key className="h-5 w-5 text-accent" />
            <h2 className="text-lg font-bold text-foreground">API Keys</h2>
          </div>

          <Card className="bg-card border-border shadow-md">
            <CardHeader className="pb-4 border-b border-border">
              <CardTitle className="text-sm font-bold text-foreground">Developer Integrations</CardTitle>
              <CardDescription className="text-xs text-muted-foreground">
                Create Bearer API keys to trigger assessment evaluations programmatically.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-4 space-y-4">
              {/* Display newly created key alert */}
              {createdKeyRaw && (
                <div className="p-3.5 rounded-lg bg-accent/5 border border-accent/25 text-foreground space-y-2.5">
                  <div className="flex items-start gap-2">
                    <ShieldAlert className="h-4 w-4 text-accent mt-0.5 shrink-0" />
                    <div className="text-[11px] font-semibold text-accent">
                      Copy this key now. It will not be shown again.
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      readOnly
                      value={createdKeyRaw}
                      className="w-full bg-background border border-border rounded px-2 py-1 font-mono text-[10px] text-accent select-all focus:outline-none"
                    />
                    <Button
                      size="sm"
                      onClick={handleCopyKey}
                      className="bg-primary hover:bg-primary/90 text-primary-foreground text-xs px-2 h-7 rounded"
                    >
                      {copied ? <Check className="h-3 w-3" /> : <Clipboard className="h-3 w-3" />}
                    </Button>
                  </div>
                </div>
              )}

              {/* Generate Key Form */}
              <form onSubmit={handleCreateKey} className="flex gap-2">
                <Input
                  placeholder="Key name (e.g. MIDAS 2.0 Production)"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  className="bg-background border-border text-xs h-9"
                />
                <Button
                  type="submit"
                  disabled={createApiKeyMutation.isPending || !newKeyName.trim()}
                  className="bg-primary hover:bg-primary/90 text-primary-foreground text-xs h-9"
                >
                  Generate
                </Button>
              </form>

              {/* List of keys */}
              {isLoadingKeys ? (
                <div className="flex justify-center py-4">
                  <div className="h-5 w-5 animate-spin rounded-full border border-primary border-t-transparent"></div>
                </div>
              ) : apiKeys.length === 0 ? (
                <p className="text-xs text-muted-foreground/75 text-center py-4">No active API keys created.</p>
              ) : (
                <div className="space-y-2.5">
                  {apiKeys.map((key) => (
                    <div
                      key={key.key_id}
                      className="flex items-center justify-between p-3 rounded-lg border border-border bg-background/40 hover:bg-background/70 transition-all"
                    >
                      <div className="space-y-0.5 max-w-[70%]">
                        <span className="text-xs font-bold text-slate-350 block truncate">{key.owner_name}</span>
                        <div className="flex items-center gap-1 text-[10px] text-muted-foreground/75">
                          <span className="font-mono bg-slate-900 border border-border px-1 rounded text-accent">
                            {key.key_prefix}...
                          </span>
                          <span>•</span>
                          <span>Created {new Date(key.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleRevokeKey(key.key_id)}
                        className="text-rose-500 hover:text-rose-400 hover:bg-rose-500/10 h-8 w-8 p-0"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
