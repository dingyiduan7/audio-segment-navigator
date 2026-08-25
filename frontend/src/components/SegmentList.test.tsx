import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { Segment } from "../types";
import { SegmentList } from "./SegmentList";

const segments: Segment[] = [
  { id: 0, label: "Track 1", start: 0, end: 60, duration: 60, confidence: 1 },
  { id: 1, label: "Track 2", start: 60, end: 135, duration: 75, confidence: 0.92 },
];

describe("SegmentList", () => {
  it("shows all segments and selects one", () => {
    const onSelect = vi.fn();
    render(<SegmentList segments={segments} activeIndex={0} onSelect={onSelect} />);

    expect(screen.getByText("2 songs")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Track 2/ }));

    expect(onSelect).toHaveBeenCalledWith(1);
  });

  it("marks the current segment", () => {
    render(<SegmentList segments={segments} activeIndex={1} onSelect={() => undefined} />);

    expect(screen.getByRole("button", { name: /Track 2/ })).toHaveAttribute(
      "aria-current",
      "true",
    );
  });
});
