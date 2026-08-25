import { forwardRef, useImperativeHandle, useRef } from "react";

import { formatTime } from "../format";
import type { MediaInfo, Segment } from "../types";

export interface SegmentPlayerHandle {
  seekToSegment: (index: number) => void;
}

interface SegmentPlayerProps {
  media: MediaInfo;
  source: string;
  segments: Segment[];
  activeIndex: number;
  onActiveChange: (index: number) => void;
}

export const SegmentPlayer = forwardRef<SegmentPlayerHandle, SegmentPlayerProps>(
  function SegmentPlayer({ media, source, segments, activeIndex, onActiveChange }, ref) {
    const playerRef = useRef<HTMLMediaElement>(null);

    const seekToSegment = (index: number) => {
      const player = playerRef.current;
      const segment = segments[index];
      if (!player || !segment) return;
      player.currentTime = segment.start;
      onActiveChange(index);
      void player.play().catch(() => undefined);
    };

    useImperativeHandle(ref, () => ({ seekToSegment }));

    const updateActiveSegment = () => {
      const currentTime = playerRef.current?.currentTime ?? 0;
      const index = segments.findIndex(
        (segment, candidate) =>
          currentTime >= segment.start &&
          (currentTime < segment.end || candidate === segments.length - 1),
      );
      if (index >= 0 && index !== activeIndex) onActiveChange(index);
    };

    const sharedProps = {
      ref: (element: HTMLMediaElement | null) => {
        playerRef.current = element;
      },
      src: source,
      controls: true,
      preload: "metadata" as const,
      onTimeUpdate: updateActiveSegment,
      onSeeked: updateActiveSegment,
    };
    const active = segments[activeIndex];

    return (
      <section
        className="player-card"
        aria-label="Media player"
        onKeyDown={(event) => {
          if (event.altKey && event.key === "ArrowLeft" && activeIndex > 0) {
            seekToSegment(activeIndex - 1);
          }
          if (event.altKey && event.key === "ArrowRight" && activeIndex < segments.length - 1) {
            seekToSegment(activeIndex + 1);
          }
        }}
      >
        <div className={`media-frame ${media.has_video ? "has-video" : ""}`}>
          {media.has_video ? <video {...sharedProps} /> : <audio {...sharedProps} />}
        </div>
        <div className="now-playing">
          <div>
            <span className="eyebrow">Now playing</span>
            <h2>{active?.label ?? "Track"}</h2>
            <p>{active ? `${formatTime(active.start)} — ${formatTime(active.end)}` : ""}</p>
          </div>
          <div className="transport">
            <button
              type="button"
              onClick={() => seekToSegment(activeIndex - 1)}
              disabled={activeIndex <= 0}
              aria-label="Previous song"
              title="Previous song (Alt + Left)"
            >
              <span aria-hidden="true">←</span> Previous
            </button>
            <button
              type="button"
              onClick={() => seekToSegment(activeIndex + 1)}
              disabled={activeIndex >= segments.length - 1}
              aria-label="Next song"
              title="Next song (Alt + Right)"
            >
              Next <span aria-hidden="true">→</span>
            </button>
          </div>
        </div>
      </section>
    );
  },
);
