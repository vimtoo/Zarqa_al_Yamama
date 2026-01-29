# Zarqa al Yamama - Quick Start Guide

**Welcome! This guide will get you from zero to your first forecast in 5 minutes.**

---

### **Step 1: Run the One-Click Installer**

This is the only step you need to get the system running. The installer handles everything.

**On Linux or macOS:**

1.  Open a **Terminal**.
2.  Navigate to the `zarqa-al-yamama` folder.
3.  Run the command: `./install.sh`

**On Windows:**

1.  Open **PowerShell** as an Administrator.
2.  Navigate to the `zarqa-al-yamama` folder.
3.  Run the command: `.\install.ps1`

> The installer will ask for your API keys. You can press **Enter** to skip any you don't have. The system will still run with limited functionality.

---

### **Step 2: Access the Dashboard**

Once the installer finishes, it will display a list of URLs. Open the **Frontend Dashboard** link in your web browser:

> **http://localhost:3000**

---

### **Step 3: Generate Your First Forecast**

Now you are ready to see Zarqa al Yamama in action.

1.  **Select a Scenario:** From the dropdown menu on the dashboard, choose a topic you're interested in, like `Middle East Oil Price Stability`.

2.  **Click Generate:** Press the **"Generate Forecast"** button.

3.  **View the Results:** In about 30-90 seconds, the dashboard will update with your forecast, including an executive summary, key metrics, and a strategic recommendation.

**That's it! You have successfully generated your first AI-powered forecast.**

---

### **What's Next?**

-   **Explore Other Scenarios:** Try generating forecasts for the other available scenarios.
-   **Review the User Guide:** For a more detailed explanation of all the features, open the `USER_GUIDE.md` file.
-   **Manage the System:** Use the commands below to manage your Zarqa al Yamama instance.

### **Essential Commands**

Run these from a terminal in the `zarqa-al-yamama` folder.

| Action | Command |
| :--- | :--- |
| **Stop the System** | `docker-compose down` |
| **Start the System Again** | `docker-compose up -d` |
| **View System Logs** | `docker-compose logs -f` |
| **Check Service Status** | `docker-compose ps` |

---

**Enjoy using Zarqa al Yamama!**
