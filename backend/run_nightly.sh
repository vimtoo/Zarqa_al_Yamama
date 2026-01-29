#!/bin/bash
# Nightly Epistemic Regression Hook
# Runs the Golden Set calibration suite.

echo "Starting Nightly Calibration Harness..."
cd backend || exit 1

# Ensure dependencies
# pip install -r requirements.txt (Assumed installed in CI env)

# Run Verification
python3 verify_regression.py
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Epistemic Integrity Verified."
    exit 0
else
    echo "❌ REGRESSION DETECTED. Blocking Deployment."
    exit 1
fi
