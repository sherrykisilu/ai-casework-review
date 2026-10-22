import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";

afterEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
});

describe("App", () => {
  it("registers and submits a case", async () => {
    const user = userEvent.setup();
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({ token: "demo-token" }), { status: 201 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        id: "case-1",
        title: "Urgent privacy escalation",
        source_text: "text",
        status: "completed",
        progress: 100,
        result: {
          summary: "One signal found.",
          findings: [],
          recommended_actions: ["Review evidence."],
          limitations: [],
          confidence: 0.8
        },
        error_code: "",
        error_message: "",
        trace_id: "trace-1",
        deduplicated: false
      }), { status: 201 }));

    render(<App />);
    await user.click(screen.getByRole("button", { name: /create demo account/i }));
    await user.click(await screen.findByRole("button", { name: /analyze case/i }));
    expect(await screen.findByText("One signal found.")).toBeInTheDocument();
    expect(screen.getByText(/Trace ID: trace-1/)).toBeInTheDocument();
  });
});
