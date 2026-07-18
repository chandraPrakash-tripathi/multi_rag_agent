"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { ScrollArea } from "@/components/ui/scroll-area";

interface QueryResult {
  thread_id: string;
  final_answer: string;
  report: string | null;
  errors: { node?: string; error?: string }[];
  completed_agents: string[];
  execution_logs: string[];
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": process.env.NEXT_PUBLIC_API_KEY || "",
        },
        body: JSON.stringify({ query }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Request failed with status ${res.status}`);
      }

      const data: QueryResult = await res.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-black text-slate-100 flex flex-col items-center px-4 py-12">
      <div className="w-full max-w-2xl space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-semibold tracking-tight">
            Space Intelligence Platform
          </h1>
          <p className="text-sm text-slate-400">
            Ask about near-Earth objects, space weather, Earth events, and more.
          </p>
        </div>

        <Card className="bg-slate-900/60 border-slate-800">
          <CardContent className="pt-6 space-y-4">
            <Textarea
              placeholder="e.g. Are there any hazardous asteroids approaching this week?"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="bg-slate-950/50 border-slate-700 min-h-24"
            />
            <Button
              onClick={handleSubmit}
              disabled={loading || !query.trim()}
              className="w-full"
            >
              {loading ? "Consulting the cosmos…" : "Ask"}
            </Button>
          </CardContent>
        </Card>

        {loading && (
          <Card className="bg-slate-900/60 border-slate-800">
            <CardContent className="pt-6 space-y-3">
              <Skeleton className="h-4 w-3/4 bg-slate-800" />
              <Skeleton className="h-4 w-full bg-slate-800" />
              <Skeleton className="h-4 w-5/6 bg-slate-800" />
              <p className="text-xs text-slate-500 pt-2">
                Multiple agents may be gathering data — this can take a minute or two on local models.
              </p>
            </CardContent>
          </Card>
        )}

        {error && (
          <Card className="bg-red-950/40 border-red-900">
            <CardContent className="pt-6">
              <p className="text-red-300 text-sm">{error}</p>
            </CardContent>
          </Card>
        )}

        {result && (
          <Card className="bg-slate-900/60 border-slate-800">
            <CardHeader>
              <CardTitle className="text-lg">Report</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <ScrollArea className="max-h-[500px] pr-4">
                <div className="whitespace-pre-wrap text-sm text-slate-200 leading-relaxed">
                  {result.report || result.final_answer}
                </div>
              </ScrollArea>

              {result.errors.length > 0 && (
                <div className="text-xs text-amber-400 border border-amber-900/50 rounded-md p-2">
                  {result.errors.length} issue(s) were encountered while gathering data.
                </div>
              )}

              <Separator className="bg-slate-800" />

              <Collapsible>
                <CollapsibleTrigger className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-2">
                  View agent trace ({result.completed_agents.length} agent{result.completed_agents.length !== 1 ? "s" : ""} ran)
                </CollapsibleTrigger>
                <CollapsibleContent className="pt-3 space-y-3">
                  <div className="flex flex-wrap gap-2">
                    {result.completed_agents.map((agent, i) => (
                      <Badge key={i} variant="secondary" className="bg-slate-800 text-slate-300">
                        {agent}
                      </Badge>
                    ))}
                  </div>
                  <div className="text-xs text-slate-500 space-y-1 font-mono">
                    {result.execution_logs.map((log, i) => (
                      <div key={i}>{log}</div>
                    ))}
                  </div>
                </CollapsibleContent>
              </Collapsible>
            </CardContent>
          </Card>
        )}
      </div>
    </main>
  );
}