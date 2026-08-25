from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .models import Segment


@dataclass(frozen=True)
class Boundary:
    time: float
    confidence: float
    source: str


def _robust_score(values: np.ndarray) -> np.ndarray:
    median = float(np.median(values))
    spread = float(np.median(np.abs(values - median))) * 1.4826
    if spread < 1e-8:
        return np.zeros_like(values)
    return (values - median) / spread


def _frame_features(
    samples: np.ndarray, sample_rate: int, frame_seconds: float = 1.0, hop_seconds: float = 0.5
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    frame_size = max(256, int(frame_seconds * sample_rate))
    hop_size = max(128, int(hop_seconds * sample_rate))
    if len(samples) < frame_size:
        samples = np.pad(samples, (0, frame_size - len(samples)))

    count = 1 + (len(samples) - frame_size) // hop_size
    window = np.hanning(frame_size).astype(np.float32)
    rms = np.empty(count, dtype=np.float32)
    spectra: list[np.ndarray] = []

    for index in range(count):
        frame = samples[index * hop_size : index * hop_size + frame_size]
        rms[index] = np.sqrt(np.mean(frame * frame) + 1e-12)
        spectrum = np.abs(np.fft.rfft(frame * window))
        spectrum /= float(spectrum.sum()) + 1e-12
        spectra.append(spectrum.astype(np.float32))

    spectrum_matrix = np.stack(spectra)
    flux = np.zeros(count, dtype=np.float32)
    if count > 1:
        flux[1:] = np.sqrt(np.mean(np.diff(spectrum_matrix, axis=0) ** 2, axis=1))
    times = np.arange(count, dtype=np.float32) * (hop_size / sample_rate) + frame_seconds / 2
    return times, rms, flux


def _clip_change_candidates(
    samples: np.ndarray,
    sample_rate: int,
    duration: float,
    minimum_spacing: float = 8.0,
) -> list[Boundary]:
    """Find hard audio changes in compilations made from short clips."""
    frame_seconds = 1.0
    hop_seconds = 0.5
    frame_size = int(frame_seconds * sample_rate)
    hop_size = int(hop_seconds * sample_rate)
    if len(samples) < frame_size * 4:
        return []

    count = 1 + (len(samples) - frame_size) // hop_size
    window = np.hanning(frame_size).astype(np.float32)
    band_edges = np.unique(np.geomspace(1, frame_size // 2 + 1, 33).astype(int))
    features = np.empty((count, len(band_edges)), dtype=np.float32)

    for index in range(count):
        frame = samples[index * hop_size : index * hop_size + frame_size]
        spectrum = np.abs(np.fft.rfft(frame * window)) ** 2
        for band, (start, end) in enumerate(zip(band_edges[:-1], band_edges[1:])):
            features[index, band] = np.log1p(float(np.mean(spectrum[start:end])))
        features[index, -1] = np.log(np.sqrt(np.mean(frame * frame)) + 1e-6)

    median = np.median(features, axis=0)
    spread = np.median(np.abs(features - median), axis=0) * 1.4826 + 1e-4
    features = np.clip((features - median) / spread, -8, 8)

    context_frames = 4
    scores = np.zeros(count, dtype=np.float32)
    for index in range(context_frames, count - context_frames):
        before = features[index - context_frames : index].mean(axis=0)
        after = features[index : index + context_frames].mean(axis=0)
        scores[index] = np.sqrt(np.mean((before - after) ** 2))

    local_peaks: list[tuple[float, float]] = []
    for index in range(2, count - 2):
        score = float(scores[index])
        if score >= 0.88 and score == float(scores[index - 2 : index + 3].max()):
            local_peaks.append((score, index * hop_seconds))

    selected: list[tuple[float, float]] = []
    for score, time in sorted(local_peaks, reverse=True):
        if time < minimum_spacing or duration - time < minimum_spacing:
            continue
        if any(abs(time - chosen_time) < minimum_spacing for _, chosen_time in selected):
            continue
        selected.append((score, time))

    selected.sort(key=lambda item: item[1])
    if len(selected) < max(8, int(duration / 45)):
        return []

    intervals = np.diff([time for _, time in selected])
    if len(intervals) and float(np.median(intervals)) > 25:
        return []

    return [
        Boundary(
            time=time,
            confidence=min(0.94, 0.58 + score * 0.16),
            source="clip-change",
        )
        for score, time in selected
    ]


def detect_boundaries(
    samples: np.ndarray,
    sample_rate: int,
    duration: float | None = None,
    minimum_segment_seconds: float = 20.0,
) -> list[Boundary]:
    """Find conservative song transitions from silence and spectral novelty."""
    if samples.ndim != 1 or sample_rate <= 0:
        raise ValueError("samples must be mono audio with a positive sample rate")
    duration = duration or len(samples) / sample_rate
    effective_minimum = min(
        minimum_segment_seconds,
        max(2.0, duration / 6),
    )
    if duration < effective_minimum * 2:
        return []

    frame_seconds = 0.5 if duration < 60 else 1.0
    hop_seconds = frame_seconds / 2
    times, rms, flux = _frame_features(
        samples,
        sample_rate,
        frame_seconds=frame_seconds,
        hop_seconds=hop_seconds,
    )
    peak_rms = float(np.percentile(rms, 95))
    noise_floor = float(np.percentile(rms, 1))
    silence_limit = min(
        max(noise_floor * 1.8, peak_rms * 0.012, 1e-5),
        peak_rms * 0.15,
    )
    silent = rms <= silence_limit
    candidates: list[Boundary] = []

    start: int | None = None
    for index in range(len(silent) + 1):
        is_silent = index < len(silent) and bool(silent[index])
        if is_silent and start is None:
            start = index
        elif not is_silent and start is not None:
            run_seconds = (index - start) * hop_seconds
            if run_seconds >= max(0.25, frame_seconds / 2):
                midpoint = float((times[start] + times[index - 1]) / 2)
                depth = 1 - float(np.mean(rms[start:index])) / (silence_limit + 1e-12)
                candidates.append(Boundary(midpoint, min(0.99, 0.78 + max(0, depth) * 0.2), "silence"))
            start = None

    clip_candidates = _clip_change_candidates(samples, sample_rate, duration)
    if clip_candidates:
        candidates.extend(clip_candidates)
        effective_minimum = 8.0

    if duration >= 60 and not clip_candidates:
        novelty = _robust_score(flux) + np.maximum(
            0,
            _robust_score(np.abs(np.diff(rms, prepend=rms[0]))),
        ) * 0.4
        flux_floor = max(
            1e-5,
            float(np.percentile(flux, 75)) * 4,
            float(np.max(flux)) * 0.08,
        )
        for index in range(2, len(novelty) - 2):
            local = novelty[index - 2 : index + 3]
            if (
                novelty[index] >= 4.0
                and novelty[index] == local.max()
                and flux[index] >= flux_floor
            ):
                confidence = min(0.85, 0.45 + float(novelty[index]) * 0.04)
                candidates.append(Boundary(float(times[index]), confidence, "acoustic-change"))

    candidates.sort(key=lambda item: (-item.confidence, item.time))
    selected: list[Boundary] = []
    for candidate in candidates:
        if candidate.time < effective_minimum or duration - candidate.time < effective_minimum:
            continue
        if any(abs(candidate.time - item.time) < effective_minimum for item in selected):
            continue
        selected.append(candidate)
    return sorted(selected, key=lambda item: item.time)


def build_segments(duration: float, boundaries: list[Boundary]) -> list[Segment]:
    points = [0.0, *(item.time for item in boundaries), duration]
    segments: list[Segment] = []
    for index, (start, end) in enumerate(zip(points, points[1:])):
        confidence = boundaries[index - 1].confidence if index else 1.0
        segments.append(
            Segment(
                id=index,
                label=f"Track {index + 1}",
                start=round(start, 3),
                end=round(end, 3),
                duration=round(end - start, 3),
                confidence=round(confidence, 2),
            )
        )
    return segments
