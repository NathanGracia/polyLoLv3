# Testing Guide - Position Display & SELL Functionality

## Quick Start

### 1. Run Position Test Script
```bash
python test_positions.py
```

This will verify:
- Bot initialization
- Position fetching from API
- Position calculation accuracy
- Market filtering

**Expected Output:**
- List of your current positions (if any)
- Position details: size, entry price, current price, P&L
- "No open positions" if you haven't placed orders yet

---

### 2. Launch GUI
```bash
python gui_modern.py
```

---

## Manual Testing Checklist

### A. Position Display Tests

#### Test 1: Empty State
**Steps:**
1. Launch GUI
2. Search for markets
3. Select a market where you have NO positions

**Expected:**
- "No positions in this market" message appears in positions section

#### Test 2: Position Display
**Steps:**
1. Select a market where you HAVE positions
2. Wait for positions to load

**Expected:**
- Position cards appear with:
  - Direction indicator (🟢 LONG or 🔴 SHORT)
  - Outcome name
  - Size and entry price
  - Current price (updated from API)
  - P&L in green (profit) or red (loss)
  - ROI percentage

#### Test 3: Manual Refresh
**Steps:**
1. Select market with positions
2. Click "↻ REFRESH" button next to "YOUR POSITIONS"

**Expected:**
- Positions reload from API
- Updated prices reflect

#### Test 4: Auto Refresh
**Steps:**
1. Select Market A
2. Note positions shown
3. Select Market B
4. Select Market A again

**Expected:**
- Positions refresh automatically each time market is selected

---

### B. BUY/SELL Button Tests

#### Test 5: Button States
**Steps:**
1. Launch GUI (no market selected)

**Expected:**
- Both BUY and SELL buttons are DISABLED (grayed out)

**Steps:**
2. Select a market

**Expected:**
- Both BUY and SELL buttons are ENABLED

#### Test 6: BUY Order
**Steps:**
1. Select market and outcome
2. Enter amount: $5
3. Click BUY button
4. Confirm in dialog

**Expected:**
- Confirmation dialog shows:
  - "CONFIRM BUY" in green
  - Outcome name
  - Side: BUY
  - Price
  - Amount: $5.00
- After confirm:
  - Toast: "BUY placed! [order_id]..."
  - Log entry: "✓ BUY PLACED: [order_id]..."
  - Positions refresh automatically

#### Test 7: SELL Order
**Steps:**
1. Select market and outcome
2. Enter amount: $3
3. Click SELL button
4. Confirm in dialog

**Expected:**
- Confirmation dialog shows:
  - "CONFIRM SELL" in red
  - Outcome name
  - Side: SELL
  - Price
  - Amount: $3.00
- After confirm:
  - Toast: "SELL placed! [order_id]..."
  - Log entry: "✓ SELL PLACED: [order_id]..."
  - Positions refresh automatically

#### Test 8: Auto-Confirm
**Steps:**
1. Enable "AUTO CONFIRM (NO POPUP)" checkbox
2. Click BUY or SELL button

**Expected:**
- NO confirmation dialog
- Order executes immediately
- Toast notification appears

---

### C. Quick Sell Tests

#### Test 9: Quick Sell Buttons Visibility
**Steps:**
1. View position cards

**Expected:**
- LONG positions (🟢): Show "SELL 25%", "SELL 50%", "SELL ALL" buttons
- SHORT positions (🔴): NO quick sell buttons (correct behavior)

#### Test 10: Quick Sell 25%
**Steps:**
1. Note current position size (e.g., 100 shares)
2. Click "SELL 25%" button
3. Check confirmation (if auto-confirm disabled)

**Expected:**
- Sells 25% of position (25 shares)
- Toast notification
- Positions refresh
- New position size: 75 shares

#### Test 11: Quick Sell 50%
**Steps:**
1. Note current position size
2. Click "SELL 50%"

**Expected:**
- Sells 50% of position
- Positions refresh

#### Test 12: Quick Sell ALL
**Steps:**
1. Click "SELL ALL" on a position
2. Wait for execution

**Expected:**
- Sells entire position
- Position card disappears after refresh
- "No positions" message if it was the only one

#### Test 13: Minimum Amount Validation
**Steps:**
1. Have a very small position (e.g., 2 shares @ $0.10 = $0.20)
2. Try to sell it

**Expected:**
- Toast error: "Sell amount too small (min $1)"
- No order placed

---

### D. Database & Deletion Tests

#### Test 14: BUY Order in Database
**Steps:**
1. Place a BUY order
2. Go to "ACTIVE BETS" tab
3. Find the bet

**Expected:**
- Bet appears in active bets
- Side: BUY
- Status: pending or active

#### Test 15: SELL Order in Database
**Steps:**
1. Place a SELL order
2. Check "ACTIVE BETS" tab

**Expected:**
- Bet appears with Side: SELL

#### Test 16: Manual Deletion
**Steps:**
1. Go to "ACTIVE BETS" tab
2. Click "✗ DELETE" on a bet
3. Confirm in dialog

**Expected:**
- Confirmation dialog appears:
  - "DELETE BET?"
  - "This will remove the bet from your database."
  - "CANCEL" and "DELETE" buttons
- After confirm:
  - Bet removed from active bets
  - Toast: "Bet deleted"
  - Log: "Bet #{id} deleted from database"

#### Test 17: Deleted Bets Stay Hidden
**Steps:**
1. Delete a bet from active bets
2. Go to "HISTORY" tab
3. Search/filter for the deleted bet

**Expected:**
- Deleted bet does NOT appear in history
- Deleted bet does NOT appear in active bets

---

### E. Error Handling Tests

#### Test 18: Network Error
**Steps:**
1. Disconnect internet
2. Select a market
3. Wait for position refresh

**Expected:**
- Empty positions state (graceful failure)
- Log message: "Error fetching positions: ..."
- No crash

#### Test 19: Invalid Amount
**Steps:**
1. Enter amount: "abc"
2. Click BUY

**Expected:**
- Toast: "Invalid amount"
- No order placed

#### Test 20: Minimum Amount
**Steps:**
1. Enter amount: 0.50
2. Click BUY

**Expected:**
- Toast: "Minimum: $1"
- No order placed

#### Test 21: Order Failure
**Steps:**
1. Try to place order with invalid token_id (if possible)

**Expected:**
- Toast: "BUY failed: [error message]"
- Log: "✗ BUY failed: ..."
- Buttons re-enabled

---

### F. Integration Tests

#### Test 22: End-to-End BUY Flow
**Steps:**
1. Search "League of Legends"
2. Select market
3. Select outcome
4. Enter $10
5. Click BUY
6. Confirm
7. Wait for execution

**Expected:**
- Order ID appears in toast
- Active bets tab shows new bet
- Positions section updates with new/updated position
- Log shows success message

#### Test 23: End-to-End SELL Flow
**Steps:**
1. Have an existing LONG position
2. Select that market
3. Select same outcome
4. Enter $5
5. Click SELL
6. Confirm

**Expected:**
- Sell order executes
- Position size decreases
- P&L updates
- Active bets shows SELL order

#### Test 24: Full Position Close
**Steps:**
1. Have a LONG position of 20 shares
2. Use quick sell ALL

**Expected:**
- All 20 shares sold
- Position disappears from positions section
- "No positions" message if last position

---

## Performance Tests

### Test 25: Rapid Clicks
**Steps:**
1. Click BUY button 5 times rapidly

**Expected:**
- Buttons disable after first click
- Only one order executes
- Buttons re-enable after completion

### Test 26: Multiple Markets
**Steps:**
1. Click Market A
2. Immediately click Market B
3. Check positions

**Expected:**
- Only Market B's positions shown
- No race conditions
- No duplicate position cards

### Test 27: Concurrent Operations
**Steps:**
1. Place BUY order
2. While order executing, click quick SELL on different position

**Expected:**
- Both operations complete
- No crashes
- Buttons handle state correctly

---

## Visual Checks

### Colors
- ✅ BUY button: Green/Cyan
- ✅ SELL button: Red/Magenta
- ✅ Profit P&L: Green
- ✅ Loss P&L: Red
- ✅ LONG indicator: 🟢 Green
- ✅ SHORT indicator: 🔴 Red
- ✅ Delete button: Red

### Layout
- ✅ Positions section between outcomes and amount
- ✅ BUY/SELL buttons side-by-side
- ✅ Position cards compact and readable
- ✅ Quick sell buttons aligned horizontally
- ✅ Delete button aligned to right in bet cards

### Text
- ✅ Outcome names display correctly
- ✅ Prices formatted to 4 decimals ($0.5432)
- ✅ Amounts formatted to 2 decimals ($10.00)
- ✅ P&L shows +/- sign ($+5.20 or $-3.40)
- ✅ ROI shows percentage (+12.5% or -8.2%)

---

## Regression Tests

### Test 28: Existing Features Still Work
**Steps:**
1. Test search markets
2. Test market selection
3. Test outcome selection
4. Test quick amount buttons (1, 5, 10, 25, 50, 100)
5. Test activity log
6. Test active bets tab
7. Test history tab with filters
8. Test CSV export

**Expected:**
- All existing features work unchanged
- No regressions

---

## Edge Cases

### Test 29: Zero Positions
**Steps:**
1. Select market with no open orders

**Expected:**
- "No positions in this market"
- No errors

### Test 30: Large Position
**Steps:**
1. Have position with 1000+ shares

**Expected:**
- Numbers display correctly
- No overflow
- Quick sell calculates correctly

### Test 31: Multiple Positions Same Market
**Steps:**
1. Have 2+ positions in same market (different outcomes)

**Expected:**
- All positions show in separate cards
- Each has own quick sell buttons
- P&L calculated independently

### Test 32: Negative P&L
**Steps:**
1. Have losing position (current_price < entry_price)

**Expected:**
- P&L shows in red
- Negative sign displays
- ROI negative

### Test 33: Very Small Position
**Steps:**
1. Position: 1.5 shares @ $0.80

**Expected:**
- Displays correctly
- Quick sell validates minimum amount

---

## Cleanup After Testing

### Test 34: Delete Test Bets
**Steps:**
1. Go to Active Bets tab
2. Delete all test bets using "✗ DELETE" button

**Expected:**
- All test bets removed from view
- Database cleaned up

---

## Known Issues to Watch For

1. **ClobClient Methods:**
   - If `get_orders()` not available in SDK, fallback to API should work
   - Check console for API errors

2. **Position Calculation:**
   - Complex scenarios (multiple buys/sells) should aggregate correctly
   - Check that net_size = buys - sells

3. **Price Updates:**
   - Current prices should update from live API
   - If API fails, falls back to entry price

4. **Threading:**
   - UI should never freeze
   - All API calls in background threads
   - Toast/log updates should appear promptly

---

## Success Criteria

All tests should PASS with:
- ✅ No crashes
- ✅ No UI freezes
- ✅ Correct calculations
- ✅ Clear error messages
- ✅ Smooth user experience

---

## Bug Reporting Template

If you find a bug:

```
**Bug:** [Short description]

**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected:** [What should happen]

**Actual:** [What actually happened]

**Error Messages:** [Any errors in console/log]

**Screenshot:** [If applicable]
```

---

## Contact

For issues or questions about this implementation, refer to:
- `POSITION_SELL_IMPLEMENTATION.md` - Full technical documentation
- `IMPLEMENTATION_SUMMARY.md` - Migration guide
- GitHub Issues (if applicable)
