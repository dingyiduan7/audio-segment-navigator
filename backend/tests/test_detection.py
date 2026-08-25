import numpy as np

from app.detection import Boundary, build_segments, detect_boundaries


def _tone(frequency: float, seconds: float, sample_rate: int) -> np.ndarray:
    time = np.arange(int(seconds * sample_rate), dtype=np.float32) / sample_rate
    return (0.25 * np.sin(2 * np.pi * frequency * time)).astype(np.float32)


def test_detects_silence_between_concatenated_tracks() -> None:
    sample_rate = 4000
    samples = np.concatenate(
        [
            _tone(220, 30, sample_rate),
            np.zeros(int(1.5 * sample_rate), dtype=np.float32),
            _tone(660, 30, sample_rate),
        ]
    )

    boundaries = detect_boundaries(
        samples,
        sample_rate,
        minimum_segment_seconds=10,
    )

    assert len(boundaries) == 1
    assert abs(boundaries[0].time - 30.75) < 1.5


def test_short_media_stays_as_one_segment() -> None:
    sample_rate = 1000
    samples = _tone(440, 15, sample_rate)

    boundaries = detect_boundaries(samples, sample_rate, minimum_segment_seconds=10)

    assert boundaries == []
    segments = build_segments(15, boundaries)
    assert len(segments) == 1
    assert segments[0].label == "Track 1"


def test_adapts_minimum_duration_for_short_multi_track_fixture() -> None:
    sample_rate = 4000
    samples = np.concatenate(
        [
            _tone(220, 6, sample_rate),
            np.zeros(sample_rate, dtype=np.float32),
            _tone(440, 4.8, sample_rate),
            np.zeros(sample_rate, dtype=np.float32),
            _tone(660, 4.8, sample_rate),
        ]
    )

    boundaries = detect_boundaries(samples, sample_rate)
    segments = build_segments(len(samples) / sample_rate, boundaries)

    assert len(segments) == 3
    assert abs(segments[0].end - 6.5) < 0.75
    assert abs(segments[1].end - 12.3) < 0.75


def test_detects_dense_hard_cut_clip_compilation() -> None:
    sample_rate = 2000
    frequencies = [110, 180, 260, 340, 430, 520, 610, 700, 790, 880]
    samples = np.concatenate(
        [_tone(frequency, 10, sample_rate) for frequency in frequencies]
    )

    boundaries = detect_boundaries(samples, sample_rate)

    assert len(boundaries) == len(frequencies) - 1
    assert all(boundary.source == "clip-change" for boundary in boundaries)
    assert [round(boundary.time) for boundary in boundaries] == list(range(10, 100, 10))


def test_build_segments_preserves_order_and_confidence() -> None:
    segments = build_segments(
        100,
        [Boundary(25, 0.9, "silence"), Boundary(70, 0.6, "acoustic-change")],
    )

    assert [(segment.start, segment.end) for segment in segments] == [
        (0, 25),
        (25, 70),
        (70, 100),
    ]
    assert segments[1].confidence == 0.9
    assert segments[2].confidence == 0.6
