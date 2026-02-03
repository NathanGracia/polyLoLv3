"""
Database module for PolymarketLolBot bet tracking.
Provides thread-safe SQLite operations for storing and retrieving bets.
"""

import sqlite3
import threading
from typing import List, Dict, Optional
from datetime import datetime
import csv


class BetDatabase:
    """Thread-safe SQLite database for bet tracking."""

    def __init__(self, db_path="bets.db"):
        """
        Initialize database connection and create tables if needed.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_database()

    def _init_database(self):
        """Create tables and indexes if they don't exist."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Create bets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bets (
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
                )
            """)

            # Create indexes for fast queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status ON bets(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_placed_at ON bets(placed_at DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_order_id ON bets(order_id)
            """)

            conn.commit()
            conn.close()

    def insert_bet(self, bet_data: Dict) -> int:
        """
        Insert a new bet into the database.

        Args:
            bet_data: Dictionary with bet fields (order_id, token_id, etc.)

        Returns:
            bet_id of inserted bet
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO bets (
                    order_id, token_id, market_id, market_question,
                    outcome, side, price, size, amount_spent, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                bet_data.get('order_id'),
                bet_data.get('token_id'),
                bet_data.get('market_id'),
                bet_data.get('market_question'),
                bet_data.get('outcome'),
                bet_data.get('side', 'BUY'),
                bet_data.get('price'),
                bet_data.get('size'),
                bet_data.get('amount_spent'),
                bet_data.get('status', 'pending')
            ))

            bet_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return bet_id

    def update_bet_status(self, bet_id: int, new_status: str, **kwargs):
        """
        Update bet status and optionally other fields.

        Args:
            bet_id: ID of bet to update
            new_status: New status value
            **kwargs: Optional fields to update (settled_at, settled_price, pnl, roi)
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Build dynamic update query
            update_fields = ['status = ?']
            values = [new_status]

            if 'settled_at' in kwargs:
                update_fields.append('settled_at = ?')
                values.append(kwargs['settled_at'])
            if 'settled_price' in kwargs:
                update_fields.append('settled_price = ?')
                values.append(kwargs['settled_price'])
            if 'pnl' in kwargs:
                update_fields.append('pnl = ?')
                values.append(kwargs['pnl'])
            if 'roi' in kwargs:
                update_fields.append('roi = ?')
                values.append(kwargs['roi'])

            values.append(bet_id)

            query = f"UPDATE bets SET {', '.join(update_fields)} WHERE bet_id = ?"
            cursor.execute(query, values)

            conn.commit()
            conn.close()

    def get_active_bets(self) -> List[Dict]:
        """
        Get all bets with status 'pending' or 'active'.

        Returns:
            List of bet dictionaries
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM bets
                WHERE status IN ('pending', 'active')
                AND status != 'deleted'
                ORDER BY placed_at DESC
            """)

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

    def get_bet_history(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Get bet history with optional filters.

        Args:
            filters: Dictionary with optional keys:
                - status: Filter by status ('all', 'pending', 'active', 'settled', 'cancelled')
                - period_days: Number of days to look back (7, 30, None for all)
                - search: Text to search in market_question

        Returns:
            List of bet dictionaries
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = "SELECT * FROM bets WHERE status != 'deleted'"
            params = []

            if filters:
                # Status filter
                if filters.get('status') and filters['status'] != 'all':
                    query += " AND status = ?"
                    params.append(filters['status'])

                # Period filter
                if filters.get('period_days'):
                    query += " AND placed_at >= datetime('now', '-' || ? || ' days')"
                    params.append(filters['period_days'])

                # Search filter
                if filters.get('search'):
                    query += " AND market_question LIKE ?"
                    params.append(f"%{filters['search']}%")

            query += " ORDER BY placed_at DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

    def get_bet_by_id(self, bet_id: int) -> Optional[Dict]:
        """
        Get a single bet by its ID.

        Args:
            bet_id: ID of bet to retrieve

        Returns:
            Bet dictionary or None if not found
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM bets WHERE bet_id = ?", (bet_id,))
            row = cursor.fetchone()
            conn.close()

            return dict(row) if row else None

    def get_bet_by_order_id(self, order_id: str) -> Optional[Dict]:
        """
        Get a single bet by its order ID.

        Args:
            order_id: Polymarket order ID

        Returns:
            Bet dictionary or None if not found
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM bets WHERE order_id = ?", (order_id,))
            row = cursor.fetchone()
            conn.close()

            return dict(row) if row else None

    def export_to_csv(self, filename: str, filters: Optional[Dict] = None):
        """
        Export bets to CSV file.

        Args:
            filename: Path to CSV file to create
            filters: Optional filters (same as get_bet_history)
        """
        bets = self.get_bet_history(filters)

        if not bets:
            return

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'bet_id', 'order_id', 'market_question', 'outcome', 'side',
                'price', 'amount_spent', 'status', 'placed_at', 'settled_at',
                'pnl', 'roi'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for bet in bets:
                # Only write relevant fields
                row = {k: bet.get(k) for k in fieldnames}
                writer.writerow(row)

    def get_stats(self) -> Dict:
        """
        Get overall statistics.

        Returns:
            Dictionary with stats (total_bets, active_bets, settled_bets, total_pnl, win_rate)
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Total bets
            cursor.execute("SELECT COUNT(*) as count FROM bets")
            total_bets = cursor.fetchone()['count']

            # Active bets
            cursor.execute("SELECT COUNT(*) as count FROM bets WHERE status IN ('pending', 'active')")
            active_bets = cursor.fetchone()['count']

            # Settled bets
            cursor.execute("SELECT COUNT(*) as count FROM bets WHERE status = 'settled'")
            settled_bets = cursor.fetchone()['count']

            # Total P&L
            cursor.execute("SELECT SUM(pnl) as total FROM bets WHERE status = 'settled'")
            total_pnl = cursor.fetchone()['total'] or 0.0

            # Win rate (bets with positive P&L / total settled)
            cursor.execute("SELECT COUNT(*) as count FROM bets WHERE status = 'settled' AND pnl > 0")
            wins = cursor.fetchone()['count']
            win_rate = (wins / settled_bets * 100) if settled_bets > 0 else 0.0

            conn.close()

            return {
                'total_bets': total_bets,
                'active_bets': active_bets,
                'settled_bets': settled_bets,
                'total_pnl': total_pnl,
                'win_rate': win_rate
            }
