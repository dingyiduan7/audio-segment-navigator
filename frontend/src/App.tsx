import { useEffect, useRef, useState } from "react";

import { getJob, removeJob, uploadMedia } from "./api";
import { MediaUploader } from "./components/MediaUploader";
import { SegmentList } from "./components/SegmentList";
import { SegmentPlayer, type SegmentPlayerHandle } from "./components/SegmentPlayer";
import type { AnalysisJob } from "./types";

export default function App() {
  const [job, setJob] = useState<AnalysisJob | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const playerRef = useRef<SegmentPlayerHandle>(null);

  useEffect(() => {
    if (!job || job.state === "completed" || job.state === "failed") return;
    const timer = window.setTimeout(async () => {
      try {
        setJob(await getJob(job.id));
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : "Could not check progress.");
      }
    }, 900);
    return () => window.clearTimeout(timer);
  }, [job]);

  const analyze = async (file: File) => {
    setUploading(true);
    setError(null);
    setActiveIndex(0);
    try {
      setJob(await uploadMedia(file));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  const reset = async () => {
    if (job) await removeJob(job.id).catch(() => undefined);
    setJob(null);
    setError(null);
    setActiveIndex(0);
  };

  const selectSegment = (index: number) => {
    setActiveIndex(index);
    playerRef.current?.seekToSegment(index);
  };

  const complete = job?.state === "completed" && job.media && job.segments && job.media_url;
  const busy = uploading || job?.state === "queued" || job?.state === "processing";

  return (
    <main>
      <header className="site-header">
        <a className="brand" href="/" aria-label="Audio Segment Navigator home">
          <span className="brand-mark" aria-hidden="true">AS</span>
          <span>Audio Segment Navigator</span>
        </a>
        {job && (
          <button className="text-button" type="button" onClick={reset}>
            Analyze another file
          </button>
        )}
      </header>

      {!complete && (
        <div className="intro-layout">
          <section className="hero">
            <span className="eyebrow">Long recording. Short path.</span>
            <h1>Move through every song, instantly.</h1>
            <p>
              Add a full concert, compilation, or video. We’ll map its song boundaries so you
              can jump straight to the part you want.
            </p>
          </section>
          <MediaUploader
            busy={Boolean(busy)}
            progress={uploading ? 0.08 : (job?.progress ?? 0)}
            onSelect={analyze}
          />
          {(error || job?.error) && (
            <div className="error-message" role="alert">
              <strong>Couldn’t analyze this file.</strong>
              <span>{error ?? job?.error}</span>
            </div>
          )}
        </div>
      )}

      {complete && (
        <div className="results-layout">
          <div className="result-summary">
            <div>
              <span className="eyebrow">Analysis complete</span>
              <h1>{job.media!.filename}</h1>
            </div>
            <span className="track-count">{job.segments!.length} tracks found</span>
          </div>
          <SegmentPlayer
            ref={playerRef}
            media={job.media!}
            source={job.media_url!}
            segments={job.segments!}
            activeIndex={activeIndex}
            onActiveChange={setActiveIndex}
          />
          <SegmentList
            segments={job.segments!}
            activeIndex={activeIndex}
            onSelect={selectSegment}
          />
        </div>
      )}
    </main>
  );
}
