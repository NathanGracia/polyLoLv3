"""
Background monitoring system for tracking bet status changes.
Polls Polymarket API to update bet status and calculate P&L.
"""

import threading
import time
from datetime import datetime
from typing import Optional, Callable, Dict
from models import Bet


class BetMonitor:
    """
    Monitors active bets and updates their status in real-time.
    Runs in a background thread to avoid blocking the GUI.
    """

    def __init__(self, bot, database, event_callback: Optional[Callable] = None):
        """
        Initialize bet monitor.

        Args:
            bot: PolymarketLolBot instance (for API access)
            database: BetDatabase instance
            event_callback: Optional callback for status change events
        """
        self.bot = bot
        self.db = database
        self.callback = event_callback
        self.polling_interval = 30  # seconds
        self.running = False
        self.thread = None

    def start(self):
        """Start the monitoring thread."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the monitoring thread gracefully."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)

    def _monitor_loop(self):
        """Main monitoring loop that runs in background thread."""
        while self.running:
            try:
                self._check_all_active_bets()
            except Exception as e:
                print(f"[BetMonitor] Error in monitoring loop: {e}")

            # Sleep with interrupt checking
            for _ in range(self.polling_interval):
                if not self.running:
                    break
                time.sleep(1)

    def _check_all_active_bets(self):
        """Check status of all active bets and update if changed."""
        active_bets = self.db.get_active_bets()

        for bet_data in active_bets:
            try:
                bet = Bet.from_db_row(bet_data)
                new_status = self._check_bet_status(bet)

                if new_status and new_status != bet.status:
                    self._handle_status_change(bet, new_status)
            except Exception as e:
                print(f"[BetMonitor] Error checking bet {bet_data.get('bet_id')}: {e}")

    def _check_bet_status(self, bet: Bet) -> Optional[str]:
        """
        Check current status of a bet via Polymarket API.

        Args:
            bet: Bet instance to check

        Returns:
            New status string or None if couldn't determine
        """
        try:
            # Try to get order status from Polymarket
            if not bet.order_id:
                return None

            # Use bot's client to check order
            if not hasattr(self.bot, 'client') or not self.bot.client:
                return None

            # Get order details
            try:
                order = self.bot.client.get_order(bet.order_id)

                if not order:
                    return None

                # Map Polymarket order status to our status
                api_status = order.get('status', '').lower()

                if api_status == 'matched' or api_status == 'filled':
                    # Check if market is resolved
                    if bet.market_id:
                        settled_price = self._check_market_resolution(bet.market_id)
                        if settled_price is not None:
                            return 'settled'
                    return 'active'

                elif api_status == 'open' or api_status == 'pending':
                    return 'pending'

                elif api_status == 'cancelled' or api_status == 'canceled':
                    return 'cancelled'

            except Exception as e:
                # If we can't get order details, check market resolution
                if bet.market_id and bet.status == 'active':
                    settled_price = self._check_market_resolution(bet.market_id)
                    if settled_price is not None:
                        return 'settled'

        except Exception as e:
            print(f"[BetMonitor] Error checking status: {e}")

        return None

    def _check_market_resolution(self, market_id: str) -> Optional[float]:
        """
        Check if a market is resolved and get the settled price.

        Args:
            market_id: Polymarket market/condition ID

        Returns:
            Settled price (1.0 for YES, 0.0 for NO) or None if not resolved
        """
        try:
            if not hasattr(self.bot, 'client') or not self.bot.client:
                return None

            # Get market details
            market = self.bot.client.get_market(market_id)

            if not market:
                return None

            # Check if market is closed and resolved
            if market.get('closed') and market.get('resolvedOutcome'):
                outcome = market.get('resolvedOutcome')
                # Convert outcome to price: YES=1.0, NO=0.0
                return 1.0 if outcome == 'YES' else 0.0

        except Exception as e:
            print(f"[BetMonitor] Error checking market resolution: {e}")

        return None

    def _handle_status_change(self, bet: Bet, new_status: str):
        """
        Handle a status change for a bet.

        Args:
            bet: Bet instance
            new_status: New status string
        """
        update_kwargs = {}

        # If settling, calculate P&L
        if new_status == 'settled' and bet.market_id:
            settled_price = self._check_market_resolution(bet.market_id)
            if settled_price is not None:
                pnl, roi = bet.calculate_pnl(settled_price)
                update_kwargs['settled_at'] = datetime.now().isoformat()
                update_kwargs['settled_price'] = settled_price
                update_kwargs['pnl'] = pnl
                update_kwargs['roi'] = roi

                # Update bet object for callback
                bet.settled_at = datetime.now()
                bet.settled_price = settled_price
                bet.pnl = pnl
                bet.roi = roi

        # Update database
        self.db.update_bet_status(bet.bet_id, new_status, **update_kwargs)

        # Update bet object
        bet.status = new_status

        # Notify callback
        if self.callback:
            try:
                self.callback({
                    'type': 'status_change',
                    'bet': bet.to_dict(),
                    'new_status': new_status
                })
            except Exception as e:
                print(f"[BetMonitor] Error in callback: {e}")

    def force_check(self):
        """Force an immediate check of all active bets (useful for testing)."""
        if self.running:
            threading.Thread(target=self._check_all_active_bets, daemon=True).start()
