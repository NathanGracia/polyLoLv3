# ⚡ PolyLoL - Ultra Fast Polymarket Trading Bot

**Version:** 3.0 Ultra Simple
**Status:** ✅ Stable & Production Ready

---

## 🎯 Overview

Ultra-fast trading bot for **Polymarket** prediction markets, optimized for esports (especially League of Legends).

- **Speed:** ~4 seconds, 2 clicks
- **Design:** Minimalist neon cyberpunk
- **Features:** Real-time price chart (5 min), configurable buffers, instant execution

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Copy `.env.example` to `.env` and add your Polymarket credentials:

```bash
PRIVATE_KEY=0xYOUR_PRIVATE_KEY
FUNDER_ADDRESS=0xYOUR_WALLET_ADDRESS
SIGNATURE_TYPE=1
CHAIN_ID=137
```

### 3. Launch

**Windows:** Double-click `START_MODERN.bat`
**Linux/Mac:** `python3 gui_modern.py`

---

## 📊 Key Features

✅ **Real-time price chart** (5 minutes live history)
✅ **Configurable price buffer** (default 0.5% - you control it)
✅ **Auto amount buffer** (1% fixed for $1 minimum safety)
✅ **Direct URL loading** (paste any Polymarket market URL)
✅ **Instant search** (filter markets in real-time)
✅ **Mouse wheel scroll** (smooth list navigation)
✅ **Clean activity log** (no spam, only your actions)

---

## 🎨 Interface Layout

```
┌─────────────────────────────────────────────────┐
│  POLYMARKET - LIGHTNING FAST    🟢 ONLINE       │
├──────────┬──────────────────────────────────────┤
│ MARKETS  │  PLACE BET                           │
│ Search   │  Selected Market                     │
│ URL      │  Outcomes                            │
│ List     │  Amount | Price Buffer %             │
│          │  [BUY YES] [BUY NO]                  │
│          │  📊 PRICE CHART (5 MIN)              │
├──────────┴──────────────────────────────────────┤
│  ACTIVITY LOG                                   │
└─────────────────────────────────────────────────┘
```

---

## ⚙️ Configuration

### Price Buffer %

Controls how aggressively you buy above market price:

- **0%** = Exact market price (may not fill instantly)
- **0.5%** = Recommended (balance speed/cost)
- **1-2%** = Very aggressive (instant fills)

### Amount Buffer

**Fixed at 1%** to ensure orders stay above Polymarket's $1 minimum.

Example: You enter $1.00 → Bot sends $1.01

---

## 📝 Activity Log Example

```
[13:45:03] Selected: LoL: T1 vs GenG (BO5)
[13:45:05] 💰 BUY T1 Win: $1.00 → $1.01 (+1%) | Price: $0.45 → $0.4522 (+0.5%)
[13:45:06] ✓ BUY SUCCESS: 0x8312f596ec
```

Clean, minimal, no spam.

---

## 🔒 Security

- ✅ Private keys stored **locally** in `.env` (gitignored)
- ✅ Orders signed **locally** (keys never sent to API)
- ✅ 100% open source, fully auditable
- ✅ No telemetry, tracking, or analytics

**Never commit `.env` to git!**

---

## 📦 Project Structure

```
polyLoLv3/
├── bot.py               # Core trading logic & API
├── gui_modern.py        # Main UI (Tkinter + Matplotlib)
├── bets.db             # Local SQLite DB (auto-created)
├── requirements.txt    # Python dependencies
├── START_MODERN.bat    # Windows launcher
├── .env               # Your API keys (gitignored)
├── .env.example       # Template
├── claude.md          # AI assistant instructions
├── README.md          # This file
└── LICENSE            # MIT License
```

---

## 🐛 Troubleshooting

**"invalid amount... min size: $1"**
→ Increase your bet amount or reduce price buffer %

**Connection failed**
→ Check `.env` credentials and internet connection

**Prices not updating**
→ Market may be closed. Try selecting another market.

---

## 🎮 Optimized for Esports

Built for League of Legends markets but works with **any Polymarket event**.

---

## 📄 License

MIT License - See [LICENSE](LICENSE)

---

**Trade fast. Trade smart. ⚡**
