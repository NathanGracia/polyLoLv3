# PolymarketLolBot v2.0 - Testing Checklist

## 🧪 Pre-Launch Testing Guide

This document outlines all tests that should be performed before considering v2.0 production-ready.

## ✅ Test 1: Database Creation & Persistence

**Objective:** Verify database is created and bets persist between sessions.

### Steps:
1. Delete `bets.db` if it exists
2. Run `python gui_modern.py`
3. Verify `bets.db` file is created in project folder
4. Connect to Polymarket (wait for "ONLINE" status)
5. Go to Markets tab
6. Place a test bet (small amount, e.g., $1)
7. Verify bet appears in Activity Log
8. Close the application completely
9. Reopen `python gui_modern.py`
10. Navigate to "ACTIVE BETS" tab
11. Verify the bet you placed is still there

### Expected Results:
- ✅ `bets.db` file created on first run
- ✅ Bet saved to database
- ✅ Bet persists after restart
- ✅ All bet details are correct (market, outcome, price, amount)

### Pass Criteria:
All expected results achieved.

---

## ✅ Test 2: Status Tracking (Pending → Active)

**Objective:** Verify bets automatically update from pending to active when filled.

### Steps:
1. Open the application
2. Place a test bet on an active market
3. Note the initial status (should be "⏳ PENDING")
4. Navigate to "ACTIVE BETS" tab
5. Wait up to 60 seconds (2 polling cycles)
6. Observe status change

### Expected Results:
- ✅ Initial status is "⏳ PENDING" (cyan)
- ✅ Status changes to "● ACTIVE" (green) within 60s
- ✅ Toast notification appears: "✓ Bet filled: [outcome]"
- ✅ Activity Log shows: "Bet filled: [market]..."
- ✅ Active Bets tab updates automatically

### Pass Criteria:
Status updates automatically without manual refresh, notification appears.

---

## ✅ Test 3: Settlement & P&L Calculation

**Objective:** Verify bets settle correctly and P&L is calculated accurately.

### Prerequisites:
- Have an active bet on a market that's about to resolve
- OR manually test with a resolved market (check Polymarket.com)

### Steps:
1. Have an active bet in the system
2. Wait for the market to resolve (or use a recently resolved market)
3. Wait up to 60 seconds for monitoring to detect settlement
4. Navigate to "HISTORY" tab
5. Find the settled bet
6. Verify P&L calculation

### Expected Results:
- ✅ Status changes to "✓ SETTLED" (gray)
- ✅ Toast notification: "Bet settled: +$X.XX" or "Bet settled: -$X.XX"
- ✅ P&L is displayed in History tab
- ✅ ROI percentage is shown
- ✅ P&L calculation is correct:
  - For WIN: P&L = (size - cost) where cost = price × size
  - For LOSS: P&L = -cost

### Manual Verification:
Calculate expected P&L manually and compare with displayed value.

**Example:**
- Buy 10 shares @ $0.55 = Cost $5.50
- If WIN (settled_price = 1.0): Payout = $10.00, P&L = +$4.50 (81.8%)
- If LOSE (settled_price = 0.0): Payout = $0.00, P&L = -$5.50 (-100%)

### Pass Criteria:
P&L matches manual calculation within $0.01.

---

## ✅ Test 4: Active Bets Tab Functionality

**Objective:** Test all features of the Active Bets tab.

### Steps:
1. Have 2-3 active bets in different states (pending, active)
2. Navigate to "ACTIVE BETS" tab
3. Verify all bets are displayed
4. Check status color coding
5. Click "↻ REFRESH" button
6. Wait 30 seconds for auto-refresh
7. Verify count label updates

### Expected Results:
- ✅ All pending/active bets are shown
- ✅ Correct count displayed: "ACTIVE BETS (X)"
- ✅ Status colors correct:
  - Pending = cyan
  - Active = green
- ✅ Manual refresh works
- ✅ Auto-refresh occurs every 30s
- ✅ All bet details are accurate

### Pass Criteria:
Tab displays accurate real-time data, refreshes work correctly.

---

## ✅ Test 5: History Tab with Filters

**Objective:** Test filtering, searching, and exporting in History tab.

### Prerequisites:
Have at least 5 bets in various states (pending, active, settled).

### Steps:

#### 5.1 - Status Filter
1. Navigate to "HISTORY" tab
2. Set Status filter to "all"
3. Verify all bets shown
4. Set Status filter to "settled"
5. Verify only settled bets shown
6. Try other statuses (pending, active, cancelled)

#### 5.2 - Period Filter
1. Set Period filter to "7 days"
2. Verify only bets from last 7 days shown
3. Set Period filter to "30 days"
4. Verify bets from last 30 days shown
5. Set back to "all"

#### 5.3 - Search
1. Enter a keyword from a market question (e.g., "T1")
2. Press Enter or click 🔍
3. Verify only matching bets shown
4. Clear search
5. Verify all bets return

#### 5.4 - Combined Filters
1. Set Status = "settled" AND Period = "7 days"
2. Verify only settled bets from last 7 days shown

### Expected Results:
- ✅ All filters work independently
- ✅ Filters can be combined
- ✅ Search is case-insensitive
- ✅ Count updates with filters
- ✅ Results update immediately

### Pass Criteria:
All filter combinations produce correct results.

---

## ✅ Test 6: CSV Export

**Objective:** Verify CSV export functionality.

### Steps:
1. Navigate to "HISTORY" tab
2. Apply some filters (optional)
3. Click "EXPORT CSV" button
4. Choose a save location
5. Save the file
6. Open the CSV in Excel or text editor
7. Verify data integrity

### Expected Results:
- ✅ File dialog appears
- ✅ CSV file is created
- ✅ File contains headers
- ✅ All filtered bets are exported
- ✅ Data format is correct
- ✅ Special characters handled (quotes, commas)
- ✅ Success toast notification appears

### Expected CSV Format:
```csv
bet_id,order_id,market_question,outcome,side,price,amount_spent,status,placed_at,settled_at,pnl,roi
1,0x7a8f...,T1 vs G2 - Who wins?,YES,BUY,0.55,10.00,settled,2025-01-28 14:32,2025-01-28 18:45,8.18,81.8
```

### Pass Criteria:
CSV exports successfully with valid data.

---

## ✅ Test 7: Notifications System

**Objective:** Test all notification types.

### Test 7.1 - Bet Placed (Existing Feature)
1. Place a bet
2. Verify toast: "Bet placed! [order_id]..."

### Test 7.2 - Bet Filled
1. Wait for pending bet to fill
2. Verify toast: "✓ Bet filled: [outcome]"
3. Verify Activity Log entry

### Test 7.3 - Bet Settled (Win)
1. Have a bet on a winning outcome settle
2. Verify toast: "Bet settled: +$X.XX" (green)
3. Verify Activity Log entry (green)

### Test 7.4 - Bet Settled (Loss)
1. Have a bet on a losing outcome settle
2. Verify toast: "Bet settled: -$X.XX" (red)
3. Verify Activity Log entry (red)

### Expected Results:
- ✅ All notification types appear
- ✅ Correct colors used
- ✅ Toasts auto-dismiss after 3s
- ✅ Activity Log persists notifications

### Pass Criteria:
All 4 notification types work correctly.

---

## ✅ Test 8: Performance (Critical!)

**Objective:** Ensure v2.0 maintains <5s bet placement speed.

### Steps:
1. Prepare to place a bet
2. Start timer when clicking "BET NOW"
3. Stop timer when bet confirmed (toast appears)
4. Record time
5. Repeat 5 times
6. Calculate average

### Expected Results:
- ✅ Average bet placement time: <5 seconds
- ✅ GUI remains responsive during bet placement
- ✅ No freezing or lag
- ✅ Database write doesn't slow placement

### Target Benchmark:
- Excellent: <4s
- Good: 4-5s
- Acceptable: 5-6s
- **Fail: >6s**

### Pass Criteria:
Average placement time ≤5 seconds.

---

## ✅ Test 9: Memory & CPU Usage

**Objective:** Verify no resource leaks or excessive usage.

### Steps:
1. Open Task Manager (Windows) or Activity Monitor (Mac)
2. Launch the application
3. Record initial memory usage
4. Place 10 bets
5. Navigate between tabs multiple times
6. Let application run for 30 minutes
7. Record final memory usage and CPU usage

### Expected Results:
- ✅ Initial memory: ~50-60 MB
- ✅ After 30 min: <100 MB (no major leak)
- ✅ CPU usage (idle): <1%
- ✅ CPU usage (active): <5%
- ✅ No memory leaks over time

### Pass Criteria:
Resource usage stays within acceptable bounds.

---

## ✅ Test 10: Error Handling

**Objective:** Verify graceful handling of errors.

### Test 10.1 - No Internet
1. Disconnect from internet
2. Try to place a bet
3. Verify error message in Activity Log
4. Verify toast notification shows error

### Test 10.2 - Invalid Market
1. Try to select a closed market
2. Attempt to place bet
3. Verify appropriate error handling

### Test 10.3 - Database Corruption (Manual)
1. While app is closed, corrupt `bets.db` (delete some bytes)
2. Try to open app
3. Verify app handles corruption gracefully

### Test 10.4 - API Rate Limiting
1. Place many bets rapidly
2. Verify API errors are caught and logged
3. Verify app doesn't crash

### Expected Results:
- ✅ No crashes on any error
- ✅ Errors logged to Activity Log
- ✅ User-friendly error messages
- ✅ App recovers gracefully

### Pass Criteria:
No crashes, all errors handled gracefully.

---

## ✅ Test 11: Multi-Session Behavior

**Objective:** Test behavior with multiple instances.

### Steps:
1. Open two instances of the application
2. Place a bet in Instance 1
3. Switch to Instance 2
4. Refresh Active Bets tab
5. Verify bet appears

### Expected Results:
- ✅ Both instances can read from database
- ✅ No database locking issues
- ✅ Data syncs via manual refresh

### Known Limitations:
- Auto-refresh only in the instance that placed the bet
- Other instances need manual refresh

### Pass Criteria:
Both instances work without conflicts.

---

## ✅ Test 12: Edge Cases

### Test 12.1 - Empty Database
1. Delete `bets.db`
2. Open app
3. Navigate to Active Bets tab
4. Verify message: "No active bets"
5. Navigate to History tab
6. Verify message: "No bets found"

### Test 12.2 - Very Long Market Names
1. Find a market with a very long question (>100 chars)
2. Place a bet
3. Verify truncation in UI works
4. Verify full text stored in database

### Test 12.3 - Special Characters
1. Find a market with special characters (quotes, apostrophes)
2. Place a bet
3. Verify correct display in all tabs
4. Export to CSV
5. Verify correct escaping in CSV

### Test 12.4 - Many Bets (Scalability)
1. Have 50+ bets in database
2. Navigate to History tab
3. Verify smooth scrolling
4. Apply filters
5. Verify performance is acceptable

### Expected Results:
- ✅ All edge cases handled gracefully
- ✅ No crashes or data corruption
- ✅ UI scales to many bets

### Pass Criteria:
All edge cases pass without issues.

---

## 📊 Final Acceptance Criteria

### Must Pass (Blockers)
- [ ] Test 1: Persistence
- [ ] Test 2: Status Tracking
- [ ] Test 3: P&L Calculation
- [ ] Test 8: Performance (<5s)
- [ ] Test 10: Error Handling

### Should Pass (High Priority)
- [ ] Test 4: Active Bets Tab
- [ ] Test 5: History Filters
- [ ] Test 6: CSV Export
- [ ] Test 7: Notifications

### Nice to Pass (Medium Priority)
- [ ] Test 9: Resource Usage
- [ ] Test 11: Multi-Session
- [ ] Test 12: Edge Cases

## 🎯 Overall Status

**Pass Criteria:**
- All "Must Pass" tests: 100% pass rate
- All "Should Pass" tests: ≥75% pass rate
- All "Nice to Pass" tests: ≥50% pass rate

**Status:**
- [ ] ✅ Ready for Production
- [ ] ⚠️ Ready with Known Issues
- [ ] ❌ Not Ready

## 📝 Test Results Log

Use this template to record test results:

```
Test #: [Number]
Date: [YYYY-MM-DD]
Tester: [Name]
Result: [PASS/FAIL]
Notes: [Any observations]
Issues Found: [List any bugs]
```

---

**Testing Version:** v2.0.0
**Last Updated:** 2025-02-03
