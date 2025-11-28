# 🤖 Multi-Brain Competition Minecraft Bot

**Multiple AI personalities compete for control!**

---

## 🚀 Quick Start

```bash
python bot.py
```

---

## 📁 Project Structure

```
minecraft_bot/
├── bot.py              ⭐ Main controller
│
├── brains/             🧠 Competing personalities
│   ├── brain_manager.py    Voting system
│   ├── aggressive.py       🔥 Fight-focused
│   ├── cautious.py         🛡️ Survival-focused
│   ├── health.py           ❤️ HP-obsessed
│   └── strategic.py        🧠 Smart planner
│
├── core/               📡 Enhanced systems
│   ├── perception.py       Complete environmental awareness
│   ├── action_manager.py   ⚡ Real-time execution (Pathfinder, PvP)
│   └── ai_brain.py         API support (optional)
│
├── settings.json       Configuration
└── logs/               Generated logs
```

---

## 🧠 How Brain Competition Works

### **The System**

```
1. Enhanced Perception gathers ALL data:
   - Health, food, position
   - Weather, time, biome, dimension
   - Nearby: entities, blocks, players
   - Inventory, armor, progression

2. All brains VOTE (0-100 score):
   🔥 AggressiveBrain: 45
   🛡️ CautiousBrain: 85  
   ❤️ HealthBrain: 95  ← WINNER!
   🧠 StrategicBrain: 60

3. Winner's decision is executed by ActionManager!
```

### **Brain Personalities**

#### 🔥 **AggressiveBrain**
- Loves combat and fighting
- Votes higher when: Strong HP, has weapons, enemies nearby
- Decision: Attack everything!

#### 🛡️ **CautiousBrain**  
- Survival first, avoids danger
- Votes higher when: Low HP, threats nearby, nighttime
- Decision: Flee to safety!

#### ❤️ **HealthBrain**
- Paranoid about hit points
- Votes higher when: ANY damage taken, low food
- Decision: Eat and heal!

#### 🧠 **Strategic Brain**
- Smart long-term planning
- Votes higher when: Good resources, progression opportunities
- Decision: Optimal next step!

---

## ⚡ Action Execution

The **ActionManager** (`core/action_manager.py`) translates brain decisions into real-time actions:

- **Combat**: Uses `mineflayer-pvp` for advanced fighting (strafing, crits).
- **Movement**: Uses `mineflayer-pathfinder` to navigate terrain and parkour.
- **Mining**: Smart block finding and breaking.
- **Fleeing**: Intelligent retreat from danger.

---

## 🎮 Example Scenario

```
[SITUATION]
Health: 8/20
Food: 5/20
Zombie 6 blocks away
Time: Night

[PERCEPTION]
{
  health: 8,
  food: 5,
  nearby_entities: [
    {type: 'zombie', distance: 6, hostile: true}
  ],
  time_of_day: 'Night'
}

[BRAIN VOTES]
🔥 AggressiveBrain: 30 (too weak to fight)
🛡️ CautiousBrain: 90 (danger + low HP!)
❤️ HealthBrain: 95 (CRITICAL HP!) ← WINNER
🧠 StrategicBrain: 45  

[DECISION] HealthBrain wins!
Action: EAT
Reason: Must eat! Food at 5/20

[EXECUTION]
ActionManager: Finding food... Eating bread.
```

---

## ⚙️ Configuration

`settings.json`:
```json
{
  "bot": {
    "default_server": "my_server",
    "ai_decision_interval": 3
  },
  "servers": {
    "my_server": {
      "host": "your-server.com",
      "port": 25565,
      "version": "1.21",
      "username": "MultiBot"
    }
  }
}
```

---

## ✨ Features

✅ **4 Competing Personalities** - Fight for control  
✅ **Complete Perception** - Weather, biome, threats, resources  
✅ **Real-Time Execution** - Pathfinder & PvP integration  
✅ **Democratic Voting** - Best brain wins each decision  
✅ **Logged Competition** - See votes and winner  
✅ **Modular** - Easy to add new brain personalities  
✅ **Self-Contained** - No external APIs needed  

---

**Most intelligent multi-brain bot!** 🧠⚡
