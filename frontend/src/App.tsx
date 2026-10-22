import { FormEvent, useEffect, useState } from "react";

import { api, CaseRecord } from "./api";

const sample =
  "The customer says a privacy breach exposed account information. They have received no response, consider the issue urgent, and want an immediate escalation.";

function App() {
  const [token, setToken] = useState(() => localStorage.getItem("casework-token") ?? "");
  const [username, setUsername] = useState("portfolio-reviewer");
  const [password, setPassword] = useState("portfolio-demo-password");
  const [title, setTitle] = useState("Urgent privacy escalation");
  const [sourceText, setSourceText] = useState(sample);
  const [caseRecord, setCaseRecord] = useState<CaseRecord | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token || !caseRecord || !["queued", "processing"].includes(caseRecord.status)) return;
    const timer = window.setInterval(async () => {
      try {
        setCaseRecord(await api.getCase(token, caseRecord.id));
      } catch (reason) {
        setError(reason instanceof Error ? reason.message : "Unable to refresh analysis.");
      }
    }, 1200);
    return () => window.clearInterval(timer);
  }, [token, caseRecord]);

  async function authenticate(mode: "register" | "login") {
    setBusy(true);
    setError("");
    try {
      const result = await api[mode](username, password);
      localStorage.setItem("casework-token", result.token);
      setToken(result.token);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Authentication failed.");
    } finally {
      setBusy(false);
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      setCaseRecord(await api.submit(token, title, sourceText));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Submission failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-4 py-8 sm:px-8">
      <header className="mb-10 max-w-3xl">
        <p className="mb-3 font-mono text-sm font-semibold uppercase tracking-[0.2em] text-accent">
          Independent portfolio project
        </p>
        <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">AI Casework Review</h1>
        <p className="mt-5 text-lg leading-8 text-slate-700">
          Submit untrusted case text, process it asynchronously, and review only findings linked to quoted evidence.
        </p>
      </header>

      {error && (
        <div role="alert" className="mb-6 rounded-lg border border-red-300 bg-red-50 p-4 text-red-900">
          {error}
        </div>
      )}

      {!token ? (
        <section aria-labelledby="auth-title" className="max-w-xl rounded-2xl border bg-white p-6 shadow-sm">
          <h2 id="auth-title" className="text-2xl font-semibold">Reviewer access</h2>
          <div className="mt-5 grid gap-4">
            <label className="grid gap-2 font-medium">
              Username
              <input className="rounded-lg border p-3" value={username} onChange={(event) => setUsername(event.target.value)} />
            </label>
            <label className="grid gap-2 font-medium">
              Password
              <input className="rounded-lg border p-3" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
            </label>
            <div className="flex flex-wrap gap-3">
              <button className="rounded-lg bg-accent px-5 py-3 font-semibold text-white disabled:opacity-50" disabled={busy} onClick={() => authenticate("register")}>
                Create demo account
              </button>
              <button className="rounded-lg border border-accent px-5 py-3 font-semibold text-accent disabled:opacity-50" disabled={busy} onClick={() => authenticate("login")}>
                Sign in
              </button>
            </div>
          </div>
        </section>
      ) : (
        <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
          <form onSubmit={submit} className="rounded-2xl border bg-white p-6 shadow-sm">
            <h2 className="text-2xl font-semibold">New review</h2>
            <p className="mt-2 text-sm text-slate-600">Do not enter secrets or data you are not permitted to process.</p>
            <label className="mt-5 grid gap-2 font-medium">
              Case title
              <input className="rounded-lg border p-3" maxLength={160} required value={title} onChange={(event) => setTitle(event.target.value)} />
            </label>
            <label className="mt-5 grid gap-2 font-medium">
              Case text
              <textarea className="min-h-64 rounded-lg border p-3 leading-6" minLength={30} maxLength={12000} required value={sourceText} onChange={(event) => setSourceText(event.target.value)} />
            </label>
            <div className="mt-2 text-right text-sm text-slate-500">{sourceText.length}/12,000</div>
            <button className="mt-5 w-full rounded-lg bg-accent px-5 py-3 font-semibold text-white disabled:opacity-50" disabled={busy}>
              {busy ? "Submitting..." : "Analyze case"}
            </button>
          </form>

          <section aria-live="polite" aria-labelledby="result-title" className="rounded-2xl bg-ink p-6 text-white shadow-xl">
            <h2 id="result-title" className="text-2xl font-semibold">Review result</h2>
            {!caseRecord ? (
              <p className="mt-4 text-slate-300">Submit a case to see its progress and evidence-grounded findings.</p>
            ) : (
              <div className="mt-5 space-y-6">
                <div>
                  <div className="flex justify-between text-sm">
                    <span className="capitalize">{caseRecord.status}</span><span>{caseRecord.progress}%</span>
                  </div>
                  <div className="mt-2 h-2 overflow-hidden rounded bg-slate-700">
                    <div className="h-full bg-teal-400 transition-all" style={{ width: `${caseRecord.progress}%` }} />
                  </div>
                  {caseRecord.deduplicated && <p className="mt-2 text-sm text-teal-200">Reused an identical prior submission.</p>}
                </div>
                {caseRecord.result && (
                  <>
                    <p className="text-lg">{caseRecord.result.summary}</p>
                    <div className="space-y-4">
                      {caseRecord.result.findings.map((finding, index) => (
                        <article key={`${finding.category}-${index}`} className="rounded-xl bg-white/10 p-4">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <h3 className="font-semibold capitalize">{finding.category.replace("_", " ")}</h3>
                            <span className="rounded-full bg-amber-300 px-2 py-1 text-xs font-bold uppercase text-amber-950">{finding.severity}</span>
                          </div>
                          <p className="mt-2 text-slate-200">{finding.summary}</p>
                          {finding.evidence.map((evidence, evidenceIndex) => (
                            <blockquote key={evidenceIndex} className="mt-3 border-l-2 border-teal-300 pl-3">
                              “{evidence.quote}”
                              <footer className="mt-1 text-sm text-slate-300">{evidence.rationale}</footer>
                            </blockquote>
                          ))}
                        </article>
                      ))}
                    </div>
                    <div>
                      <h3 className="font-semibold">Human review actions</h3>
                      <ul className="mt-2 list-disc space-y-1 pl-5 text-slate-200">
                        {caseRecord.result.recommended_actions.map((action) => <li key={action}>{action}</li>)}
                      </ul>
                    </div>
                    <p className="text-sm text-slate-400">Trace ID: {caseRecord.trace_id}</p>
                  </>
                )}
              </div>
            )}
          </section>
        </div>
      )}
    </main>
  );
}

export default App;
