
import sys
import os
import pytest
from pydantic import ValidationError

# Ensure backend is in path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.graph.contracts import ConflictMetrics

def test_valid_anchored_metric():
    print("\n--- Testing Valid Anchored Metric ---")
    try:
        m = ConflictMetrics(
            velocity=0.5,
            intensity_score=25.0,
            anchor_id="B1",
            band="B",
            hotspots=["Paris"],
            trend="stable"
        )
        print("✅ Success: Created valid anchored metric.")
        assert m.delta_required is True
    except Exception as e:
        print(f"❌ Failed to create valid metric: {e}")
        sys.exit(1)

def test_invalid_unanchored_metric():
    print("\n--- Testing Invalid Unanchored Metric (Should Fail) ---")
    try:
        ConflictMetrics(
            velocity=0.5,
            intensity_score=50.0,
            # Missing anchor_id and band
            hotspots=["London"],
            trend="stable"
        )
        print("❌ FAILED: Schema accepted unanchored metric!")
        sys.exit(1)
    except ValidationError as e:
        print("✅ Success: Schema rejected unanchored metric.")
        print(f"   Error: {e.errors()[0]['msg']}")

def test_missing_score_with_reason():
    print("\n--- Testing Missing Score with Reason ---")
    try:
        m = ConflictMetrics(
            velocity=0.1,
            intensity_score=None,
            unknown_reason="Insufficient data",
            hotspots=[],
            trend="stable"
        )
        print("✅ Success: Created valid metric with missing score.")
    except Exception as e:
        print(f"❌ Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_valid_anchored_metric()
    test_invalid_unanchored_metric()
    test_missing_score_with_reason()
