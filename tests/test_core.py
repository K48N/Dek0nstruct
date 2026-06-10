"""Core tests for Dek0nstruct (no AI, no external media required)."""
import pytest
from core.segment import Segment
from core.undo_manager import UndoManager, AddSegmentCommand, RemoveSegmentCommand


# ── Segment ──────────────────────────────────────────────────────────────────

def test_segment_basic():
    s = Segment(start=0.0, end=10.0, label="A")
    assert s.duration == pytest.approx(10.0)


def test_segment_overlap():
    a = Segment(0, 10)
    b = Segment(5, 15)
    c = Segment(10, 20)
    assert a.overlaps_with(b)
    assert not a.overlaps_with(c)


def test_segment_serialisation():
    s = Segment(start=1.5, end=9.5, label="Test", color="#ff0000",
                export_video=True, export_audio=False)
    d = s.to_dict()
    s2 = Segment.from_dict(d)
    assert s2.start == s.start
    assert s2.end == s.end
    assert s2.label == s.label
    assert s2.export_audio is False


def test_segment_invalid():
    with pytest.raises(ValueError):
        Segment(start=5.0, end=3.0)


# ── UndoManager ───────────────────────────────────────────────────────────────

def test_undo_add_remove():
    segments = []
    mgr = UndoManager()
    seg = Segment(0, 5, "X")

    mgr.execute(AddSegmentCommand(segments, seg))
    assert len(segments) == 1

    assert mgr.can_undo()
    mgr.undo()
    assert len(segments) == 0

    assert mgr.can_redo()
    mgr.redo()
    assert len(segments) == 1


def test_undo_remove():
    segments = []
    mgr = UndoManager()
    seg = Segment(0, 5, "Y")

    mgr.execute(AddSegmentCommand(segments, seg))
    mgr.execute(RemoveSegmentCommand(segments, seg))
    assert len(segments) == 0

    mgr.undo()
    assert len(segments) == 1

    mgr.undo()
    assert len(segments) == 0
