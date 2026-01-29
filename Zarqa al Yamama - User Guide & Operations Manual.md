# Zarqa al Yamama - User Guide & Operations Manual

**Version:** 1.0.0  
**Creator:** Qusai Al-Duaij  
**Last Updated:** 2025-02-17

---

## 1. Introduction

Welcome to **Zarqa al Yamama**, your personal Foresight Intelligence Agent. This guide provides everything you need to install, operate, and understand the system.

### What is Zarqa al Yamama?

Zarqa al Yamama is a sophisticated AI system designed to predict geopolitical and economic scenarios. It works by combining two types of information:

1.  **Hard Data:** Statistical information like stock prices, economic indicators, and market trends.
2.  **Soft Signals:** Linguistic information from news articles, global events, and public sentiment.

By fusing these signals, the system generates probabilistic forecasts, helping you make more informed decisions.

### Who is this Guide For?

This guide is for end-users of the Zarqa al Yamama system. Whether you are an analyst, a decision-maker, or simply curious about future trends, this manual will walk you through every step of using the application.

---

## 2. Getting Started

### System Requirements

To run Zarqa al Yamama, you will need a computer with **Docker** installed. Docker is a platform that makes it easy to run applications in isolated environments called containers.

| Component | Requirement |
| :--- | :--- |
| **Operating System** | Windows 10/11, macOS, or Linux |
| **Software** | Docker Desktop (or Docker Engine on Linux) |
| **Internet** | An active internet connection is required |

> **Note:** If you do not have Docker, please download it from the official [Docker website](https://www.docker.com/products/docker-desktop) before proceeding.

### One-Click Installation

We have created simple one-click installation scripts to get you up and running in minutes.

#### For Linux and macOS Users:

1.  Open a **Terminal**.
2.  Navigate to the `zarqa-al-yamama` project directory.
3.  Make the script executable: `chmod +x install.sh`
4.  Run the installer: `./install.sh`

#### For Windows Users:

1.  Open **PowerShell** (right-click and "Run as Administrator").
2.  Navigate to the `zarqa-al-yamama` project directory.
3.  Allow script execution: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
4.  Run the installer: `.\install.ps1`

### The Installation Process

The script will automate the following steps:

1.  **Prerequisite Check:** Verifies that Docker is installed and running.
2.  **API Key Configuration:** Prompts you to enter your API keys. You can press `Enter` to skip any key you don't have.
3.  **Docker Setup:** Builds and starts all the necessary services.
4.  **Health Check:** Verifies that all components are running correctly.
5.  **Sample Forecast:** Runs a test forecast to ensure the system is fully operational.

Upon completion, it will display the URLs to access the application and other useful information.

---

## 3. Using the Dashboard

### Accessing the Web Interface

Once the installation is complete, you can access the Zarqa al Yamama dashboard by opening the following URL in your web browser:

> **http://localhost:3000**

### Dashboard Overview

The dashboard is designed for simplicity and ease of use.

![Dashboard Overview](https://i.imgur.com/placeholder.png) <!-- Placeholder for a real image -->

| Section | Description |
| :--- | :--- |
| **1. Scenario Selection** | A dropdown menu to choose the scenario you want to forecast (e.g., "Middle East Oil Price Stability"). |
| **2. Generate Forecast** | The main button to start the analysis. This will trigger the AI agents to gather and process data. |
| **3. Results Display** | This area will populate with the forecast results once the analysis is complete. |

### How to Generate a Forecast

1.  **Select a Scenario:** Choose the topic you are interested in from the dropdown menu.
2.  **Click Generate:** Press the "Generate Forecast" button.
3.  **Wait for Analysis:** The process typically takes **30-90 seconds**. The button will be disabled during this time.
4.  **View Results:** The results will appear on the dashboard automatically.

### Interpreting the Results

Once a forecast is complete, the results are displayed in several sections:

#### Executive Summary
A concise, three-line summary of the most critical findings, including the predicted outcome, confidence level, and key factors to watch.

#### Forecast Metrics
A set of cards showing the key numbers:

-   **Current Value:** The latest known value of the metric being forecast.
-   **30-Day Forecast:** The predicted value of the metric in 30 days.
-   **Confidence:** The system's confidence in its own forecast, expressed as a percentage.
-   **Processing Time:** How long the analysis took to complete.

#### Strategic Recommendation
An actionable recommendation based on the forecast. This is not financial advice but rather a strategic insight based on the available data.

#### Weak Signals
These are early warning indicators or subtle trends that may not be widely noticed but could have a significant impact in the future. They are critical for proactive decision-making.

#### Metadata
This section provides transparency into the forecast process, showing which AI agents were involved, the unique ID of the request, and the validation status.

---

## 4. System Operations

Zarqa al Yamama runs on Docker, which makes managing the system straightforward.

### Starting and Stopping the System

-   **To Start:** Open a terminal in the project directory and run `docker-compose up -d`.
-   **To Stop:** Open a terminal in the project directory and run `docker-compose down`.

### Viewing System Logs

To see what the system is doing in real-time, you can view the logs:

```bash
# View logs for all services
docker-compose logs -f

# View logs for a specific service (e.g., the backend)
docker-compose logs -f backend
```

### Checking Service Status

To see the status of all running services, use the following command:

```bash
docker-compose ps
```

This will show you which services are running and if they are healthy.

---

## 5. Troubleshooting

| Problem | Solution |
| :--- | :--- |
| **Installation script fails** | Ensure you are running PowerShell as an Administrator (Windows) or have made the script executable (`chmod +x install.sh`) on Linux/macOS. |
| **"Port is already allocated" error** | Another application is using a required port (e.g., 3000, 8000). Close the other application or change the port in the `docker-compose.yml` file. |
| **Dashboard is not loading** | 1. Run `docker-compose ps` to ensure the `frontend` and `backend` services are running. <br> 2. Check the logs with `docker-compose logs -f frontend`. <br> 3. Try restarting the services: `docker-compose restart`. |
| **Forecast generation fails** | 1. Check the backend logs: `docker-compose logs -f backend`. <br> 2. Ensure your API keys in the `.env` file are correct. <br> 3. Make sure you have a stable internet connection. |

---

## 6. Frequently Asked Questions (FAQ)

**Q: How long does a forecast take to generate?**
A: A typical forecast takes between 30 and 90 seconds, depending on the complexity of the scenario and the speed of the external data sources.

**Q: Where does the data come from?**
A: The system integrates over 15 public and commercial data sources, including GDELT, NewsAPI, Polygon.io (for market data), and various economic databases. All sources are validated for credibility.

**Q: How accurate are the forecasts?**
A: Forecast accuracy varies by scenario but is continuously benchmarked. The system provides a **confidence score** with every prediction to indicate its own assessment of reliability. It is designed to provide probabilistic guidance, not deterministic certainty.

**Q: Can I add my own scenarios?**
A: The current version includes a pre-defined set of scenarios. Custom scenario building is a feature planned for a future release.

---

## 7. Glossary

| Term | Definition |
| :--- | :--- |
| **Temporal Analyst** | The AI agent responsible for analyzing time-series data (e.g., stock prices). |
| **Context Interpreter** | The AI agent that analyzes news and text to understand sentiment and narratives. |
| **The Quantifier** | The middleware agent that mathematically combines the outputs of the other agents. |
| **The Critic** | The AI agent that validates data sources and checks for bias. |
| **The Governor** | The AI agent that ensures all forecasts adhere to ethical guidelines. |
| **Sentiment Score** | A metric from -1 (very negative) to +1 (very positive) that quantifies the tone of news and events. |
| **Weak Signal** | An early, often subtle, indicator of a potential future trend or disruption. |

---

## 8. Support & Contact

For support, questions, or to report an issue, please contact the development team led by **Qusai Al-Duaij** through the official project channels.

Thank you for using Zarqa al Yamama!
