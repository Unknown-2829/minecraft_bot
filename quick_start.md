# 🚀 Quick Start Guide

Welcome to the **Autonomous Minecraft Bot**! This guide will help you get your bot up and running in minutes.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

1.  **Python 3.8+**: [Download Python](https://www.python.org/downloads/)
2.  **Node.js & npm**: [Download Node.js](https://nodejs.org/) (Required for Mineflayer)

## 🛠️ Installation

1.  **Clone the repository** (if you haven't already):
    ```bash
    git clone <repository-url>
    cd minecraft_bot
    ```

2.  **Install Python dependencies**:
    ```bash
    pip install javascript
    ```

3.  **Install Node.js dependencies**:
    ```bash
    npm install mineflayer mineflayer-pathfinder mineflayer-pvp
    ```

## ⚙️ Configuration

The bot uses `settings.json` for configuration. A default file will be created on the first run, or you can create one manually.

1.  **Edit `settings.json`**:
    ```json
    {
      "bot": {
        "default_server": "my_server",
        "ai_decision_interval": 3
      },
      "servers": {
        "my_server": {
          "host": "your-server-ip.com",
          "port": 25565,
          "version": "1.21",
          "username": "BotName",
          "auth": "offline" 
        }
      }
    }
    ```
    *Note: Set `"auth": "microsoft"` if you want to use a premium Minecraft account.*

## 🏃 Running the Bot

To start the bot, simply run:

```bash
python bot.py
```

The bot will:
1.  Connect to the server specified in `settings.json`.
2.  Initialize the **ActionManager** and **Brains**.
3.  Start the decision-making loop.

## 🧠 Understanding the Brains

Your bot is controlled by multiple competing "brains":

-   **🔥 AggressiveBrain**: Wants to fight.
-   **🛡️ CautiousBrain**: Wants to stay safe.
-   **❤️ HealthBrain**: Wants to heal and eat.
-   **🧠 StrategicBrain**: Wants to progress and gather resources.

They vote on actions, and the **ActionManager** executes the winner's choice!

## ❓ Troubleshooting

-   **"Error: Cannot find module 'mineflayer'"**: Run `npm install mineflayer` again.
-   **"Connection failed"**: Check your server IP and port in `settings.json`.
-   **Bot stands still**: Ensure `mineflayer-pathfinder` is installed (`npm install mineflayer-pathfinder`).

---
**Happy Botting!** 🤖
