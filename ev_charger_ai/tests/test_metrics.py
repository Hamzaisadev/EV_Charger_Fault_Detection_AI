"""Unit tests for competition scoring in core.metrics.

Verifies:
  - Perfect detection scores 100.
  - On-time detection boundary (fault + LATE_GRACE_S vs fault + LATE_GRACE_S + 0.1).
  - Earliness scaling and LEAD_CAP clipping at 120s.
  - False alarm rate lowering score by 30/N.
  - Head-to-head tie sharing within TIE_S.
  - Missed detections and family-level statistics breakdown.
  - Edge cases (empty datasets, sessions with no alerts).
"""
import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.metrics import (  # noqa: E402
    score_detectors,
    LEAD_CAP,
    LATE_GRACE_S,
    TIE_S,
)


def test_perfect_detector_scores_100():
    records = [
        # Faulty sessions with lead >= 120s
        {
            "label": {"faults": [(200.0, "iso", "isolation drop")]},
            "alerts": {"Perfect": {"t": 50.0}},  # lead = 150s >= 120s cap
        },
        {
            "label": {"faults": [(300.0, "slac", "attenuation")]},
            "alerts": {"Perfect": {"t": 180.0}},  # lead = 120s cap
        },
        # Clean sessions with no alerts
        {
            "label": {"faults": []},
            "alerts": {},
        },
        {
            "label": {"faults": []},
            "alerts": {"Perfect": None},
        },
    ]

    res = score_detectors(records, ["Perfect"])
    assert res["n_faulty"] == 2
    assert res["n_clean"] == 2

    d = res["detectors"]["Perfect"]
    assert d["recall"] == 1.0
    assert d["far"] == 0.0
    assert d["earliness"] == 1.0
    assert d["score"] == 100.0
    assert d["tp"] == 2
    assert d["fp"] == 0
    assert d["miss"] == 0
    assert d["late"] == 0
    assert d["wins"] == 2.0


def test_late_grace_boundary():
    # Fault at t = 100.0
    # On-time boundary is t <= 100.0 + LATE_GRACE_S (110.0s)
    # Late boundary is t > 110.0s
    records = [
        {
            "label": {"faults": [(100.0, "iso", "reason")]},
            "alerts": {
                "OnTimeBoundary": {"t": 100.0 + LATE_GRACE_S},
                "LateBoundary": {"t": 100.0 + LATE_GRACE_S + 0.1},
            },
        }
    ]

    res = score_detectors(records, ["OnTimeBoundary", "LateBoundary"])
    ontime = res["detectors"]["OnTimeBoundary"]
    late = res["detectors"]["LateBoundary"]

    assert ontime["tp"] == 1
    assert ontime["late"] == 0
    assert ontime["recall"] == 1.0
    assert ontime["earliness"] == 0.0  # lead = max(0, 100 - 110) = 0

    assert late["tp"] == 0
    assert late["late"] == 1
    assert late["recall"] == 0.0
    assert late["earliness"] == 0.0


def test_false_alarm_rate_lowers_score_by_30_over_n():
    n_clean = 5
    records = [
        # 1 faulty session with perfect score
        {
            "label": {"faults": [(200.0, "iso", "reason")]},
            "alerts": {"Detector": {"t": 50.0}},
        },
    ]
    # Add N clean sessions, with 1 false alarm on the first clean session
    for i in range(n_clean):
        records.append({
            "label": {"faults": []},
            "alerts": {"Detector": {"t": 10.0}} if i == 0 else {},
        })

    res = score_detectors(records, ["Detector"])
    assert res["n_faulty"] == 1
    assert res["n_clean"] == n_clean

    d = res["detectors"]["Detector"]
    assert d["tp"] == 1
    assert d["fp"] == 1
    assert d["far"] == 1.0 / n_clean

    expected_score = 50.0 * 1.0 + 30.0 * (1.0 - (1.0 / n_clean)) + 20.0 * 1.0
    assert round(d["score"], 4) == round(expected_score, 4)


def test_head_to_head_tie_shares_win():
    # Both detectors alert within TIE_S (0.1s) of the earliest alert
    records = [
        {
            "label": {"faults": [(100.0, "iso", "reason")]},
            "alerts": {
                "DetA": {"t": 60.0},
                "DetB": {"t": 60.0 + TIE_S * 0.8},  # within tie window
                "DetC": {"t": 60.0 + TIE_S + 0.05},  # outside tie window
            },
        }
    ]

    res = score_detectors(records, ["DetA", "DetB", "DetC"])
    assert res["detectors"]["DetA"]["wins"] == 0.5
    assert res["detectors"]["DetB"]["wins"] == 0.5
    assert res["detectors"]["DetC"]["wins"] == 0.0


def test_earliness_scaling_and_lead_cap():
    records = [
        {
            "label": {"faults": [(100.0, "iso", "reason")]},
            "alerts": {
                "HalfLead": {"t": 40.0},  # lead = 60s -> 60/120 = 0.5
                "CappedLead": {"t": -50.0},  # lead = 150s -> min(150, 120)/120 = 1.0
            },
        }
    ]

    res = score_detectors(records, ["HalfLead", "CappedLead"])
    assert res["detectors"]["HalfLead"]["earliness"] == 0.5
    assert res["detectors"]["HalfLead"]["median_lead_s"] == 60.0
    assert res["detectors"]["CappedLead"]["earliness"] == 1.0
    assert res["detectors"]["CappedLead"]["median_lead_s"] == 150.0


def test_miss_detection():
    records = [
        {
            "label": {"faults": [(100.0, "iso", "reason")]},
            "alerts": {
                "Active": {"t": 90.0},
                "Silent": None,
            },
        }
    ]

    res = score_detectors(records, ["Active", "Silent"])
    assert res["detectors"]["Active"]["tp"] == 1
    assert res["detectors"]["Silent"]["miss"] == 1
    assert res["detectors"]["Silent"]["tp"] == 0
    assert res["detectors"]["Silent"]["recall"] == 0.0


def test_by_family_breakdown():
    records = [
        {
            "label": {"faults": [(100.0, "iso", "isolation")]},
            "alerts": {"Det": {"t": 90.0}},
        },
        {
            "label": {"faults": [(200.0, "slac", "attenuation")]},
            "alerts": {"Det": {"t": 250.0}},  # late
        },
    ]

    res = score_detectors(records, ["Det"])
    by_fam = res["detectors"]["Det"]["by_family"]

    assert "iso" in by_fam and by_fam["iso"]["tp"] == 1 and by_fam["iso"]["n"] == 1
    assert by_fam["iso"]["recall"] == 1.0
    assert "slac" in by_fam and by_fam["slac"]["tp"] == 0 and by_fam["slac"]["n"] == 1
    assert by_fam["slac"]["recall"] == 0.0


def test_empty_records():
    res = score_detectors([], ["Det"])
    assert res["n_faulty"] == 0
    assert res["n_clean"] == 0
    d = res["detectors"]["Det"]
    assert d["recall"] == 0.0
    assert d["far"] == 0.0
    assert d["earliness"] == 0.0
    # score = 50 * 0 + 30 * (1 - 0) + 20 * 0 = 30.0
    assert d["score"] == 30.0


def main():
    test_functions = [
        v for k, v in sorted(globals().items())
        if k.startswith("test_") and callable(v)
    ]
    print(f"Running {len(test_functions)} metric test suites...")
    for test in test_functions:
        test()
        print(f"  [PASS] {test.__name__}")
    print("\nAll unit tests passed successfully!")


if __name__ == "__main__":
    main()
