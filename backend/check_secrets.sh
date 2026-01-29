#!/bin/bash
# check_secrets.sh
# Simple secret scanner for pre-commit or CI hooks
# Rejects commits with hardcoded Google keys or API key assignments

echo "🔒 Scanning for secrets..."

# 1. Check for Hardcoded Google Keys (AIza...)
# Uses find + grep to avoid BSD/GNU grep version issues with exclude-dir
echo "   Searching for 'AIza' patterns..."
if find . -type f \
    -not -path '*/.git/*' \
    -not -path '*/.venv/*' \
    -not -path '*/venv/*' \
    -not -path '*/node_modules/*' \
    -not -path '*/dist/*' \
    -not -path '*/build/*' \
    -not -path '*/__pycache__/*' \
    -not -name 'check_secrets.sh' \
    -not -name '.env*' \
    -not -name '*.docx' \
    -not -name '*.json' \
    -not -name 'GEMINI_SETUP.md' \
    -print0 | xargs -0 grep "AIza"; then
    echo "❌ CRITICAL: Found potential hardcoded Google API Key (starts with AIza)."
    exit 1
fi

# 2. Check for Hardcoded assignments to GEMINI_API_KEY
echo "   Searching for unsafe assignments..."
if find . -type f \
    -not -path '*/.git/*' \
    -not -path '*/.venv/*' \
    -not -path '*/venv/*' \
    -not -path '*/node_modules/*' \
    -not -path '*/dist/*' \
    -not -path '*/build/*' \
    -not -path '*/__pycache__/*' \
    -not -name 'check_secrets.sh' \
    -not -name '.env*' \
    -not -name 'GEMINI_SETUP.md' \
    -print0 | xargs -0 grep "GEMINI_API_KEY=[\"']AIza"; then
    echo "❌ CRITICAL: Found hardcoded GEMINI_API_KEY assignment."
    exit 1
fi

# 3. Check for specific dangerous files not in gitignore check
# (Just a double check, gitignore prevents commit but this checks if they exist in source tree to warn user)
if [ -f "reallapikeys.docx" ]; then
    echo "⚠️  WARNING: 'reallapikeys.docx' exists in directory. Ensure it is NOT added to git."
fi

echo "✅ Secret Scan Passed. No obvious hardcoded keys found."
exit 0
