import type { AnalysisJob } from "./types";

async function parseResponse(response: Response): Promise<AnalysisJob> {
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail ?? `Request failed (${response.status})`);
  }
  return response.json() as Promise<AnalysisJob>;
}

export async function uploadMedia(file: File): Promise<AnalysisJob> {
  const body = new FormData();
  body.append("file", file);
  return parseResponse(
    await fetch("/api/jobs", {
      method: "POST",
      body,
    }),
  );
}

export async function getJob(id: string): Promise<AnalysisJob> {
  return parseResponse(await fetch(`/api/jobs/${id}`));
}

export async function removeJob(id: string): Promise<void> {
  await fetch(`/api/jobs/${id}`, { method: "DELETE" });
}
