import { fireEvent, render, screen } from "@testing-library/react";
import { beforeAll, describe, expect, it, vi } from "vitest";

import type { MediaInfo, Segment } from "../types";
import { SegmentPlayer } from "./SegmentPlayer";

const media: MediaInfo = {
  filename: "mix.mp3",
  content_type: "audio/mpeg",
  duration: 120,
  has_video: false,
};
const segments: Segment[] = [
  { id: 0, label: "Track 1", start: 0, end: 60, duration: 60, confidence: 1 },
  { id: 1, label: "Track 2", start: 60, end: 120, duration: 60, confidence: 0.9 },
];

beforeAll(() => {
  Object.defineProperty(HTMLMediaElement.prototype, "play", {
    configurable: true,
    value: vi.fn().mockResolvedValue(undefined),
  });
});

describe("SegmentPlayer", () => {
  it("moves to the next song and disables previous at the start", () => {
    const onActiveChange = vi.fn();
    render(
      <SegmentPlayer
        media={media}
        source="/media"
        segments={segments}
        activeIndex={0}
        onActiveChange={onActiveChange}
      />,
    );

    expect(screen.getByRole("button", { name: "Previous song" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Next song" }));

    expect(onActiveChange).toHaveBeenCalledWith(1);
  });

  it("disables next on the final song", () => {
    render(
      <SegmentPlayer
        media={media}
        source="/media"
        segments={segments}
        activeIndex={1}
        onActiveChange={() => undefined}
      />,
    );

    expect(screen.getByRole("button", { name: "Next song" })).toBeDisabled();
  });
});
