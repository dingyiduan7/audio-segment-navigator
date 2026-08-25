import { formatTime } from "../format";
import type { Segment } from "../types";

interface SegmentListProps {
  segments: Segment[];
  activeIndex: number;
  onSelect: (index: number) => void;
}

export function SegmentList({ segments, activeIndex, onSelect }: SegmentListProps) {
  return (
    <section className="segment-section" aria-labelledby="segment-heading">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Detected timeline</span>
          <h2 id="segment-heading">{segments.length} song{segments.length === 1 ? "" : "s"}</h2>
        </div>
        <span className="hint">Select a song to jump</span>
      </div>
      <ol className="segment-list">
        {segments.map((segment, index) => (
          <li key={segment.id}>
            <button
              className={`segment-row ${index === activeIndex ? "is-active" : ""}`}
              type="button"
              onClick={() => onSelect(index)}
              aria-current={index === activeIndex ? "true" : undefined}
            >
              <span className="track-number">{String(index + 1).padStart(2, "0")}</span>
              <span className="track-copy">
                <strong>{segment.label}</strong>
                <small>
                  {formatTime(segment.start)} — {formatTime(segment.end)}
                </small>
              </span>
              <span className="track-duration">{formatTime(segment.duration)}</span>
              <span className="confidence" title="Boundary confidence">
                {Math.round(segment.confidence * 100)}%
              </span>
            </button>
          </li>
        ))}
      </ol>
    </section>
  );
}
