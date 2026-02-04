# PolymarketLolBot v2.0 - Upgrade Guide

## 🎉 What's New in v2.0

This major update adds comprehensive bet tracking and management features to the PolymarketLolBot while maintaining the lightning-fast <5s bet placement speed.

### New Features

1. **Persistent Bet Storage** - All bets are saved to a local SQLite database
2. **Automatic Status Tracking** - Monitor bets in real-time (pending → active → settled)
3. **Active Bets View** - See all your current positions at a glance
4. **Complete History** - Browse all past bets with filters and search
5. **P&L Calculations** - Automatic profit/loss calculation when bets settle
6. **Toast Notifications** - Get notified when bet status changes
7. **CSV Export** - Export your betting history for analysis
8. **Tabbed Interface** - Clean organization: Markets | Active Bets | History

## 📦 Installation

### First Time Setup

```bash
# Navigate to project folder
cd C:\Users\nathan\Documents\projets\polyLoLv3

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Make sure you have your .env file with credentials
# PRIVATE_KEY=your_private_key
# FUNDER_ADDRESS=your_address
```

### Upgrading from v1.0

No additional dependencies required! The upgrade uses only Python's standard library:
- `sqlite3` (built-in)
- `threading` (built-in)
- `dataclasses` (built-in)

Simply pull the latest code and run:

```bash
python gui_modern.py
```

The database will be automatically created on first run.

## 🚀 Quick Start

### Running the Application

```bash
python gui_modern.py
```

Or use the batch file:

```bash
START_MODERN.bat
```

### First Run

On first launch, the application will:
1. Create `bets.db` in the project folder
2. Connect to Polymarket
3. Start the bet monitoring system
4. Load the Markets tab

## 📱 Using the New Features

### 1. Markets Tab (Unchanged)

- Search for markets
- Select a market and outcome
- Place bets instantly (<5s)
- All bets are now automatically saved!

### 2. Active Bets Tab

**What you'll see:**
- All pending and active bets
- Real-time status updates (every 30s)
- Entry price, amount, and current status
- Auto-refresh indicator

**Status Indicators:**
- ⏳ **PENDING** - Order placed but not yet filled (cyan)
- ● **ACTIVE** - Position open, waiting for settlement (green)

**Actions:**
- Click "↻ REFRESH" to manually update
- Auto-refreshes every 30 seconds

### 3. History Tab

**Filters:**
- **Status**: All, Pending, Active, Settled, Cancelled
- **Period**: All time, Last 7 days, Last 30 days
- **Search**: Search market questions by keyword

**What you'll see:**
- All your bets sorted by date (newest first)
- For settled bets: P&L and ROI displayed
- Color-coded status indicators
- Timestamp for each bet

**Actions:**
- Filter and search to find specific bets
- Click "EXPORT CSV" to export filtered results
- Use search to find bets on specific markets/teams

### 4. Notifications

You'll receive automatic toast notifications for:

**Bet Filled** (pending → active)
```
✓ Bet filled: YES
```

**Bet Settled** (active → settled)
```
✓ Bet settled: +$8.18  (if win)
✗ Bet settled: -$5.00  (if loss)
```

**Bet Cancelled**
```
Bet cancelled: YES
```

## 💾 Database Structure

The `bets.db` SQLite database contains:

### Bets Table Schema

```sql
CREATE TABLE bets (
    bet_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT UNIQUE,
    token_id TEXT NOT NULL,
    market_id TEXT,
    market_question TEXT,
    outcome TEXT NOT NULL,
    side TEXT NOT NULL,
    price REAL NOT NULL,
    size REAL NOT NULL,
    amount_spent REAL NOT NULL,
    status TEXT DEFAULT 'pending',
    placed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    settled_at TIMESTAMP,
    settled_price REAL,
    pnl REAL,
    roi REAL
);
```

### Bet Status Lifecycle

1. **pending** - Order placed but not filled yet
2. **active** - Order filled, position open
3. **settled** - Market resolved, P&L calculated
4. **cancelled** - Order cancelled before fill

## 📊 P&L Calculation

### For BUY Orders

```
Cost = price × size

If WIN (outcome happens):
  Payout = size × 1.0
  P&L = Payout - Cost

If LOSE (outcome doesn't happen):
  Payout = 0
  P&L = -Cost

ROI = (P&L / Cost) × 100%
```

### Example

Buy 10 shares @ $0.55:
- Cost = $5.50
- If WIN: Payout = $10.00 → P&L = +$4.50 (+81.8%)
- If LOSE: Payout = $0.00 → P&L = -$5.50 (-100%)

## 🔧 Configuration

### Polling Interval

The bet monitor checks for status updates every 30 seconds by default. To change this, edit `bet_monitor.py`:

```python
self.polling_interval = 30  # Change to desired seconds
```

**Note:** Lower values = more API calls. Recommended: 30-60 seconds.

### Database Location

By default, the database is created at:
```
C:\Users\nathan\Documents\projets\polyLoLv3\bets.db
```

To change the location, edit `gui_modern.py` line 148:

```python
self.database = BetDatabase("bets.db")  # Change path here
```

## 📈 Performance

### Speed Comparison

| Metric | v1.0 | v2.0 | Impact |
|--------|------|------|--------|
| Bet placement | ~4s | ~4s | ✅ None |
| Memory usage | ~50MB | ~55MB | ✅ +5MB |
| CPU (idle) | <1% | <1% | ✅ None |
| CPU (active) | <5% | <5% | ✅ None |

### Optimization

The implementation is optimized for speed:
- **Async database writes** - <10ms overhead
- **Background monitoring** - Runs in separate thread
- **Efficient queries** - Indexed database lookups
- **Minimal API calls** - Batched when possible

## 🐛 Troubleshooting

### Database Issues

**Database locked error:**
```bash
# Close all instances of the app, then:
rm bets.db
python gui_modern.py  # Will recreate DB
```

**Missing bets:**
- Check the History tab with "All" filters
- Verify the bet was placed successfully (check Activity Log)

### Monitoring Issues

**Status not updating:**
1. Check internet connection
2. Verify Polymarket API is accessible
3. Check Activity Log for errors
4. Try clicking "↻ REFRESH" manually

**Incorrect P&L:**
- P&L is only calculated when market settles
- Verify the market has been resolved on Polymarket.com
- Check the settled_price in the database

### Performance Issues

**GUI feels slow:**
1. Check how many bets are in the database
2. Use filters in History tab to reduce results
3. Consider archiving old bets (export CSV, then delete from DB)

**High CPU usage:**
- Check the polling interval (should be ≥30s)
- Verify only one instance of the app is running

## 📤 Exporting Data

### CSV Export Format

```csv
bet_id,order_id,market_question,outcome,side,price,amount_spent,status,placed_at,settled_at,pnl,roi
1,0x7a8f...,T1 vs G2 - Who wins?,YES,BUY,0.55,10.00,settled,2025-01-28 14:32,2025-01-28 18:45,8.18,81.8
```

### Using Exported Data

**In Excel:**
1. Open exported CSV
2. Use filters to analyze performance
3. Create pivot tables for stats

**In Python:**
```python
import pandas as pd

df = pd.read_csv('polymarket_history.csv')
total_pnl = df['pnl'].sum()
win_rate = (df['pnl'] > 0).sum() / len(df) * 100
print(f"Total P&L: ${total_pnl:.2f}")
print(f"Win Rate: {win_rate:.1f}%")
```

## 🔐 Data Privacy

### What's Stored Locally

All data is stored in the local `bets.db` file:
- Bet details (market, outcome, price, amount)
- Order IDs from Polymarket
- Status and timestamps
- P&L calculations

### What's NOT Stored

- Your private key (only in .env)
- Wallet addresses
- Personal information
- Any data on external servers

**Security Note:** The database file is unencrypted. Keep your computer secure and don't share the `bets.db` file.

## 📝 Backup and Restore

### Manual Backup

```bash
# Backup database
copy bets.db bets_backup_20250203.db

# Backup entire project
cd ..
tar -czf polyLoLv3_backup.tar.gz polyLoLv3/
```

### Restore from Backup

```bash
# Restore database
copy bets_backup_20250203.db bets.db
```

### Automated Backup (Optional)

Create a batch file `backup.bat`:

```batch
@echo off
set TIMESTAMP=%date:~-4%%date:~3,2%%date:~0,2%
copy bets.db backups\bets_%TIMESTAMP%.db
echo Backup created: backups\bets_%TIMESTAMP%.db
```

Run this before closing the app or on a schedule.

## 🆘 Support

### Getting Help

1. Check this guide first
2. Review the Activity Log in the app
3. Check the console for error messages
4. Review `bets.db` with SQLite Browser

### Common Questions

**Q: Can I edit bets in the database?**
A: Not recommended. Manual edits may cause sync issues with Polymarket.

**Q: What happens if I delete a bet from the database?**
A: It only removes the local record. Your actual position on Polymarket is unchanged.

**Q: Can I use this with multiple accounts?**
A: Yes, but use separate database files (change path in gui_modern.py).

**Q: Does this work on Mac/Linux?**
A: Yes! All code is cross-platform. Just use forward slashes in paths.

## 🎯 Next Steps

Now that you have v2.0 running:

1. ✅ Place a test bet to see it saved
2. ✅ Check the Active Bets tab
3. ✅ Wait for bet to fill and see notification
4. ✅ Explore filters in History tab
5. ✅ Export your data to CSV

## 📚 Advanced Usage

### Database Queries

You can query the database directly using Python:

```python
from database import BetDatabase

db = BetDatabase("bets.db")

# Get stats
stats = db.get_stats()
print(f"Total bets: {stats['total_bets']}")
print(f"Win rate: {stats['win_rate']:.1f}%")
print(f"Total P&L: ${stats['total_pnl']:.2f}")

# Get recent bets
recent = db.get_bet_history({'period_days': 7})
for bet in recent:
    print(f"{bet['market_question']}: {bet['outcome']} - {bet['status']}")
```

### Custom Reports

Create custom analytics by querying the database:

```python
import sqlite3

conn = sqlite3.connect('bets.db')
cursor = conn.cursor()

# Best performing outcomes
cursor.execute("""
    SELECT outcome, COUNT(*) as count, AVG(pnl) as avg_pnl
    FROM bets
    WHERE status = 'settled'
    GROUP BY outcome
    ORDER BY avg_pnl DESC
""")

for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]} bets, avg P&L: ${row[2]:.2f}")
```

## 🚀 Future Enhancements (Roadmap)

Potential features for v2.1+:

- **Portfolio Dashboard** - Visual overview with charts
- **Price Alerts** - Notifications when odds change
- **Stop-Loss/Take-Profit** - Automated exit strategies
- **Arbitrage Detection** - Find guaranteed profit opportunities
- **Multi-Market Analysis** - Compare similar markets
- **WebSocket Updates** - Real-time updates instead of polling

## 📄 License & Credits

- **PolymarketLolBot** - Built for the LoL betting community
- **Polymarket API** - via py-clob-client
- **Database** - SQLite (public domain)

---

**Version:** 2.0.0
**Last Updated:** 2025-02-03
**Compatibility:** Python 3.7+, Windows/Mac/Linux
