export type JobState = "queued" | "processing" | "completed" | "failed";

export interface MediaInfo {
  filename: string;
  content_type: string;
  duration: number;
  has_video: boolean;
}

export interface Segment {
  id: number;
  label: string;
  start: number;
  end: number;
  duration: number;
  confidence: number;
}

export interface AnalysisJob {
  id: string;
  state: JobState;
  progress: number;
  error: string | null;
  media: MediaInfo | null;
  segments: Segment[] | null;
  media_url: string | null;
}
