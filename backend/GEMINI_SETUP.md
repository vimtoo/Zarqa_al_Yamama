# Google Gemini API Setup Guide

This guide explains how to securely configure the Google Gemini Developer API for Zarqa al Yamama.

> **SECURITY WARNING:** Never hardcode your API key in `config.py` or commit it to Git. Always use environment variables.

## 1. Get your API Key
Obtain your API key from Google AI Studio: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

## 2. Set Environment Variables

### macOS / Linux (Bash/Zsh)
Add these lines to your `~/.zshrc` or `~/.bashrc`, or run them in your current terminal session:

```bash
export GEMINI_ENABLED=true
export GEMINI_DRY_RUN=false # Set to true to mock network calls
export GEMINI_API_KEY="AIzaSy..." # Replace with your actual key
```

To reload your shell config:
```bash
source ~/.zshrc
```

### Windows (PowerShell)
Run these commands in your PowerShell session:

```powershell
$env:GEMINI_ENABLED="true"
$env:GEMINI_API_KEY="AIzaSy..." # Replace with your actual key
```

To make it persistent (User level):
```powershell
[System.Environment]::SetEnvironmentVariable("GEMINI_ENABLED", "true", "User")
[System.Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "AIzaSy...", "User")
```

## 3. Verify Setup
Run the smoke test to confirm the application can see the key:

```bash
python3 backend/verify_gemini.py
```

## Troubleshooting
*   **Startup Error:** "GEMINI_ENABLED is True, but GEMINI_API_KEY is not set."
    *   *Fix:* You enabled the feature flag but forgot to export the key.
*   **Logs say:** "Gemini API key not configured"
    *   *Fix:* Check if `GEMINI_ENABLED` is actually true.
