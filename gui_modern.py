"""
🎮 POLYMARKET BOT - MODERN NEON UI
Interface futuriste flat design sans popups
"""

import sys
import json
import tkinter as tk
from tkinter import ttk, font
import threading
import requests
from datetime import datetime
from bot import PolymarketLolBot

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')


class NeonButton(tk.Canvas):
    """Bouton néon custom."""
    def __init__(self, parent, text, command, bg="#0a0a0a", fg="#00ffff",
                 hover_fg="#ff00ff", width=200, height=50, **kwargs):
        super().__init__(parent, width=width, height=height, bg=bg,
                        highlightthickness=0, **kwargs)

        self.bg = bg
        self.fg = fg
        self.hover_fg = hover_fg
        self.text = text
        self.command = command
        self.width = width
        self.height = height
        self.is_hovered = False
        self.is_disabled = False

        self.draw()
        self.bind("<Button-1>", self._click)
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)

    def draw(self):
        self.delete("all")

        color = "#333333" if self.is_disabled else (self.hover_fg if self.is_hovered else self.fg)

        # Border glow
        self.create_rectangle(2, 2, self.width-2, self.height-2,
                            outline=color, width=2)

        # Text
        text_color = "#666666" if self.is_disabled else color
        self.create_text(self.width/2, self.height/2, text=self.text,
                        fill=text_color, font=("Arial", 12, "bold"))

    def _click(self, event):
        if not self.is_disabled and self.command:
            self.command()

    def _enter(self, event):
        if not self.is_disabled:
            self.is_hovered = True
            self.draw()

    def _leave(self, event):
        self.is_hovered = False
        self.draw()

    def disable(self):
        self.is_disabled = True
        self.draw()

    def enable(self):
        self.is_disabled = False
        self.draw()


class ToastNotification(tk.Toplevel):
    """Toast notification au lieu de popup."""
    def __init__(self, parent, message, type="info"):
        super().__init__(parent)

        self.overrideredirect(True)
        self.attributes('-topmost', True)

        # Colors
        colors = {
            "info": "#00ffff",
            "success": "#00ff88",
            "error": "#ff0066",
            "warning": "#ffaa00"
        }

        color = colors.get(type, "#00ffff")

        self.configure(bg="#0a0a0a")

        frame = tk.Frame(self, bg="#0a0a0a", highlightbackground=color,
                        highlightthickness=2)
        frame.pack(padx=2, pady=2)

        label = tk.Label(frame, text=message, bg="#0a0a0a", fg=color,
                        font=("Arial", 10, "bold"), padx=20, pady=10)
        label.pack()

        # Position
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        self.geometry(f"+{screen_width-320}+{screen_height-100}")

        # Auto dismiss
        self.after(3000, self.destroy)


class ModernPolymarketGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("POLYMARKET BOT")
        self.root.geometry("1400x800")

        # Colors
        self.bg = "#0a0a0a"
        self.bg_secondary = "#1a1a1a"
        self.neon_cyan = "#00ffff"
        self.neon_magenta = "#ff00ff"
        self.neon_green = "#00ff88"
        self.neon_red = "#ff0066"
        self.text_gray = "#888888"

        self.root.configure(bg=self.bg)

        # State
        self.bot = None
        self.markets = []
        self.selected_market = None
        self.selected_outcome_idx = None
        self.is_refreshing = False
        self.auto_confirm = tk.BooleanVar(value=False)

        # Fonts
        self.font_title = font.Font(family="Arial", size=24, weight="bold")
        self.font_subtitle = font.Font(family="Arial", size=12)
        self.font_body = font.Font(family="Arial", size=10)
        self.font_small = font.Font(family="Arial", size=9)

        self.create_ui()
        self.init_bot()

    def create_ui(self):
        """Créer l'interface moderne."""

        # Header
        header = tk.Frame(self.root, bg=self.bg, height=80)
        header.pack(fill=tk.X, padx=20, pady=10)
        header.pack_propagate(False)

        title = tk.Label(header, text="POLYMARKET", bg=self.bg,
                        fg=self.neon_cyan, font=self.font_title)
        title.pack(side=tk.LEFT, pady=20)

        subtitle = tk.Label(header, text="LIGHTNING FAST BETTING", bg=self.bg,
                           fg=self.text_gray, font=self.font_subtitle)
        subtitle.pack(side=tk.LEFT, padx=20, pady=20)

        self.status_dot = tk.Canvas(header, width=12, height=12, bg=self.bg,
                                   highlightthickness=0)
        self.status_dot.pack(side=tk.RIGHT, padx=10, pady=30)
        self.status_dot.create_oval(2, 2, 10, 10, fill=self.text_gray, outline="")

        self.status_label = tk.Label(header, text="CONNECTING", bg=self.bg,
                                    fg=self.text_gray, font=self.font_small)
        self.status_label.pack(side=tk.RIGHT, pady=30)

        # Divider
        div1 = tk.Frame(self.root, bg=self.neon_cyan, height=1)
        div1.pack(fill=tk.X, padx=20)

        # Main container
        main = tk.Frame(self.root, bg=self.bg)
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Left: Markets
        left = tk.Frame(main, bg=self.bg)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        markets_header = tk.Frame(left, bg=self.bg)
        markets_header.pack(fill=tk.X, pady=(0, 10))

        markets_label = tk.Label(markets_header, text="MARKETS", bg=self.bg,
                                fg=self.neon_magenta, font=("Arial", 14, "bold"))
        markets_label.pack(side=tk.LEFT)

        self.market_count = tk.Label(markets_header, text="0", bg=self.bg,
                                    fg=self.text_gray, font=self.font_small)
        self.market_count.pack(side=tk.LEFT, padx=10)

        # Search
        search_frame = tk.Frame(left, bg=self.bg_secondary, height=40)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        search_frame.pack_propagate(False)

        self.search_var = tk.StringVar(value="League of Legends")
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                    bg=self.bg_secondary, fg="white",
                                    font=self.font_body, relief=tk.FLAT,
                                    insertbackground=self.neon_cyan)
        self.search_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.search_entry.bind("<Return>", lambda e: self.search_markets())

        search_btn = tk.Label(search_frame, text="SEARCH", bg=self.bg_secondary,
                            fg=self.neon_cyan, font=("Arial", 9, "bold"),
                            cursor="hand2")
        search_btn.pack(side=tk.RIGHT, padx=10)
        search_btn.bind("<Button-1>", lambda e: self.search_markets())

        refresh_btn = tk.Label(search_frame, text="↻", bg=self.bg_secondary,
                             fg=self.neon_magenta, font=("Arial", 16),
                             cursor="hand2")
        refresh_btn.pack(side=tk.RIGHT, padx=5)
        refresh_btn.bind("<Button-1>", lambda e: self.search_markets())

        # Markets list
        list_container = tk.Frame(left, bg=self.bg_secondary)
        list_container.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_container, bg=self.bg_secondary,
                                troughcolor=self.bg, activebackground=self.neon_cyan)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.markets_canvas = tk.Canvas(list_container, bg=self.bg_secondary,
                                       highlightthickness=0, yscrollcommand=scrollbar.set)
        self.markets_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.markets_canvas.yview)

        self.markets_frame = tk.Frame(self.markets_canvas, bg=self.bg_secondary)
        self.markets_canvas.create_window((0, 0), window=self.markets_frame, anchor="nw")

        self.markets_frame.bind("<Configure>",
                               lambda e: self.markets_canvas.configure(scrollregion=self.markets_canvas.bbox("all")))

        # Divider vertical
        div2 = tk.Frame(main, bg=self.neon_cyan, width=1)
        div2.pack(side=tk.LEFT, fill=tk.Y, padx=20)

        # Right: Bet panel
        right = tk.Frame(main, bg=self.bg, width=450)
        right.pack(side=tk.RIGHT, fill=tk.Y)
        right.pack_propagate(False)

        bet_header = tk.Label(right, text="PLACE BET", bg=self.bg,
                            fg=self.neon_green, font=("Arial", 14, "bold"))
        bet_header.pack(pady=(0, 20))

        # Market title
        self.market_title_label = tk.Label(right, text="SELECT A MARKET", bg=self.bg,
                                          fg=self.text_gray, font=self.font_body,
                                          wraplength=400, justify=tk.LEFT)
        self.market_title_label.pack(pady=(0, 20))

        # Outcomes
        outcomes_label = tk.Label(right, text="OUTCOMES", bg=self.bg,
                                fg=self.text_gray, font=("Arial", 10, "bold"))
        outcomes_label.pack(pady=(0, 10), anchor=tk.W)

        self.outcomes_frame = tk.Frame(right, bg=self.bg)
        self.outcomes_frame.pack(fill=tk.X, pady=(0, 20))

        # Amount
        amount_label = tk.Label(right, text="AMOUNT", bg=self.bg,
                              fg=self.text_gray, font=("Arial", 10, "bold"))
        amount_label.pack(pady=(0, 10), anchor=tk.W)

        amount_container = tk.Frame(right, bg=self.bg_secondary, height=60)
        amount_container.pack(fill=tk.X, pady=(0, 10))
        amount_container.pack_propagate(False)

        dollar = tk.Label(amount_container, text="$", bg=self.bg_secondary,
                         fg=self.neon_cyan, font=("Arial", 20, "bold"))
        dollar.pack(side=tk.LEFT, padx=10)

        self.amount_var = tk.StringVar(value="1.0")
        self.amount_entry = tk.Entry(amount_container, textvariable=self.amount_var,
                                    bg=self.bg_secondary, fg="white",
                                    font=("Arial", 20), relief=tk.FLAT,
                                    insertbackground=self.neon_cyan,
                                    justify=tk.CENTER)
        self.amount_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=10)

        # Quick amounts
        quick_frame = tk.Frame(right, bg=self.bg)
        quick_frame.pack(fill=tk.X, pady=(0, 20))

        for amount in [1, 5, 10, 25, 50, 100]:
            btn = tk.Label(quick_frame, text=f"{amount}", bg=self.bg_secondary,
                          fg=self.neon_cyan, font=("Arial", 9),
                          cursor="hand2", width=6, height=2)
            btn.pack(side=tk.LEFT, padx=2)
            btn.bind("<Button-1>", lambda e, a=amount: self.set_amount(a))

        # Auto confirm toggle
        auto_frame = tk.Frame(right, bg=self.bg)
        auto_frame.pack(fill=tk.X, pady=(0, 20))

        auto_check = tk.Checkbutton(auto_frame, text="AUTO CONFIRM (NO POPUP)",
                                   variable=self.auto_confirm, bg=self.bg,
                                   fg=self.neon_magenta, selectcolor=self.bg,
                                   activebackground=self.bg,
                                   activeforeground=self.neon_magenta,
                                   font=("Arial", 9, "bold"))
        auto_check.pack(anchor=tk.W)

        # Bet button
        self.bet_btn = NeonButton(right, text="BET NOW", command=self.place_bet,
                                 bg=self.bg, fg=self.neon_green,
                                 hover_fg=self.neon_cyan,
                                 width=440, height=80)
        self.bet_btn.pack(pady=(0, 20))
        self.bet_btn.disable()

        # Log
        log_label = tk.Label(right, text="ACTIVITY LOG", bg=self.bg,
                           fg=self.text_gray, font=("Arial", 10, "bold"))
        log_label.pack(pady=(0, 10), anchor=tk.W)

        log_container = tk.Frame(right, bg=self.bg_secondary)
        log_container.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(log_container, bg=self.bg_secondary, fg=self.text_gray,
                               font=("Courier", 8), relief=tk.FLAT, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.config(state=tk.DISABLED)

        # Log colors
        self.log_text.tag_config("cyan", foreground=self.neon_cyan)
        self.log_text.tag_config("green", foreground=self.neon_green)
        self.log_text.tag_config("red", foreground=self.neon_red)
        self.log_text.tag_config("magenta", foreground=self.neon_magenta)

    def log(self, message, color="gray"):
        """Log avec couleur."""
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")

        tag = color if color != "gray" else None
        self.log_text.insert(tk.END, f"[{timestamp}] ", "gray")
        self.log_text.insert(tk.END, f"{message}\n", tag)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def toast(self, message, type="info"):
        """Afficher un toast."""
        ToastNotification(self.root, message, type)

    def update_status(self, status, color):
        """Mettre à jour le status."""
        self.status_label.config(text=status, fg=color)
        self.status_dot.delete("all")
        self.status_dot.create_oval(2, 2, 10, 10, fill=color, outline="")

    def init_bot(self):
        """Initialiser le bot."""
        def _init():
            try:
                self.log("Connecting to Polymarket...", "cyan")
                self.bot = PolymarketLolBot()
                self.log("Connected successfully", "green")
                self.root.after(0, lambda: self.update_status("ONLINE", self.neon_green))
                self.root.after(0, self.search_markets)
            except Exception as e:
                self.log(f"Connection failed: {e}", "red")
                self.root.after(0, lambda: self.update_status("OFFLINE", self.neon_red))

        threading.Thread(target=_init, daemon=True).start()

    def search_markets(self):
        """Rechercher des marchés."""
        if self.is_refreshing:
            return

        query = self.search_var.get()

        def _search():
            try:
                self.is_refreshing = True
                self.log(f"Searching: {query}", "cyan")

                resp = requests.get("https://gamma-api.polymarket.com/markets?limit=300&closed=false", timeout=10)
                all_markets = resp.json()

                keywords = query.lower().split()
                filtered = []

                for market in all_markets:
                    question = market.get("question", "").lower()
                    description = market.get("description", "").lower()

                    for keyword in keywords:
                        if keyword in question or keyword in description:
                            filtered.append(market)
                            break

                self.markets = filtered
                self.root.after(0, self.display_markets)
                self.log(f"Found {len(filtered)} markets", "green")

            except Exception as e:
                self.log(f"Search failed: {e}", "red")
            finally:
                self.is_refreshing = False

        threading.Thread(target=_search, daemon=True).start()

    def display_markets(self):
        """Afficher les marchés."""
        for widget in self.markets_frame.winfo_children():
            widget.destroy()

        self.market_count.config(text=str(len(self.markets)))

        for i, market in enumerate(self.markets):
            question = market.get("question", "N/A")

            market_card = tk.Frame(self.markets_frame, bg=self.bg,
                                  highlightthickness=1, highlightbackground=self.bg_secondary)
            market_card.pack(fill=tk.X, pady=5, padx=5)

            text = tk.Label(market_card, text=question, bg=self.bg, fg="white",
                           font=self.font_small, wraplength=550, justify=tk.LEFT,
                           cursor="hand2", padx=10, pady=10)
            text.pack(fill=tk.X)

            # Bind click
            for widget in [market_card, text]:
                widget.bind("<Button-1>", lambda e, m=market: self.select_market(m))
                widget.bind("<Enter>", lambda e, w=market_card: w.config(highlightbackground=self.neon_cyan))
                widget.bind("<Leave>", lambda e, w=market_card: w.config(highlightbackground=self.bg_secondary))

    def select_market(self, market):
        """Sélectionner un marché."""
        self.selected_market = market
        self.selected_outcome_idx = None

        question = market.get("question", "N/A")
        self.market_title_label.config(text=question, fg="white")

        # Clear outcomes
        for widget in self.outcomes_frame.winfo_children():
            widget.destroy()

        # Parse outcomes
        outcomes = json.loads(market.get("outcomes", "[]"))
        prices = json.loads(market.get("outcomePrices", "[]"))

        for i, (outcome, price) in enumerate(zip(outcomes, prices)):
            card = tk.Frame(self.outcomes_frame, bg=self.bg_secondary,
                           cursor="hand2", highlightthickness=1,
                           highlightbackground=self.bg_secondary)
            card.pack(fill=tk.X, pady=3)

            outcome_label = tk.Label(card, text=outcome, bg=self.bg_secondary,
                                   fg="white", font=self.font_body, anchor=tk.W)
            outcome_label.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.X, expand=True)

            price_label = tk.Label(card, text=f"${float(price):.4f}",
                                  bg=self.bg_secondary, fg=self.neon_cyan,
                                  font=("Arial", 10, "bold"))
            price_label.pack(side=tk.RIGHT, padx=10, pady=10)

            # Bind click
            for widget in [card, outcome_label, price_label]:
                widget.bind("<Button-1>", lambda e, idx=i, c=card: self.select_outcome(idx, c))

        self.bet_btn.enable()
        self.log(f"Selected: {question[:50]}...", "magenta")

    def select_outcome(self, idx, card):
        """Sélectionner un outcome."""
        # Reset all
        for widget in self.outcomes_frame.winfo_children():
            widget.config(highlightbackground=self.bg_secondary)

        # Highlight selected
        card.config(highlightbackground=self.neon_cyan)
        self.selected_outcome_idx = idx

        outcomes = json.loads(self.selected_market.get("outcomes", "[]"))
        self.log(f"Selected: {outcomes[idx]}", "cyan")

    def set_amount(self, amount):
        """Définir le montant."""
        self.amount_var.set(str(float(amount)))

    def place_bet(self):
        """Placer le pari."""
        if not self.selected_market or self.selected_outcome_idx is None:
            self.toast("Select market and outcome", "error")
            return

        try:
            amount = float(self.amount_var.get())
            if amount < 1.0:
                self.toast("Minimum: $1", "warning")
                return
        except:
            self.toast("Invalid amount", "error")
            return

        # Parse data
        outcomes = json.loads(self.selected_market.get("outcomes", "[]"))
        prices = json.loads(self.selected_market.get("outcomePrices", "[]"))
        tokens = json.loads(self.selected_market.get("clobTokenIds", "[]"))

        outcome = outcomes[self.selected_outcome_idx]
        price = float(prices[self.selected_outcome_idx])
        token_id = tokens[self.selected_outcome_idx]

        # Confirmation si pas auto
        if not self.auto_confirm.get():
            confirm_win = tk.Toplevel(self.root)
            confirm_win.title("Confirm")
            confirm_win.geometry("400x250")
            confirm_win.configure(bg=self.bg)
            confirm_win.attributes('-topmost', True)

            tk.Label(confirm_win, text="CONFIRM BET", bg=self.bg, fg=self.neon_cyan,
                    font=("Arial", 14, "bold")).pack(pady=20)

            tk.Label(confirm_win, text=f"Outcome: {outcome}", bg=self.bg, fg="white",
                    font=self.font_body).pack(pady=5)
            tk.Label(confirm_win, text=f"Price: ${price:.4f}", bg=self.bg, fg="white",
                    font=self.font_body).pack(pady=5)
            tk.Label(confirm_win, text=f"Amount: ${amount:.2f}", bg=self.bg, fg=self.neon_green,
                    font=("Arial", 12, "bold")).pack(pady=5)

            btn_frame = tk.Frame(confirm_win, bg=self.bg)
            btn_frame.pack(pady=20)

            def confirm():
                confirm_win.destroy()
                self._execute_bet(token_id, price, amount, outcome)

            NeonButton(btn_frame, "CONFIRM", confirm, fg=self.neon_green,
                      width=150, height=40).pack(side=tk.LEFT, padx=5)
            NeonButton(btn_frame, "CANCEL", confirm_win.destroy, fg=self.neon_red,
                      width=150, height=40).pack(side=tk.LEFT, padx=5)
        else:
            self._execute_bet(token_id, price, amount, outcome)

    def _execute_bet(self, token_id, price, amount, outcome):
        """Exécuter le pari."""
        self.bet_btn.disable()
        self.log(f"Placing bet: {outcome} ${amount:.2f}", "cyan")

        def _bet():
            try:
                result = self.bot.place_bet(
                    token_id=token_id,
                    side="BUY",
                    price=price + 0.01,
                    total_amount=amount,
                    confirm=False
                )

                if result and result.get('success'):
                    order_id = result.get('orderID', 'N/A')[:16]
                    self.root.after(0, lambda: self.log(f"✓ BET PLACED: {order_id}...", "green"))
                    self.root.after(0, lambda: self.toast(f"Bet placed! {order_id}...", "success"))
                else:
                    self.root.after(0, lambda: self.log("✗ Bet failed", "red"))
                    self.root.after(0, lambda: self.toast("Bet failed", "error"))

            except Exception as e:
                self.root.after(0, lambda: self.log(f"✗ Error: {e}", "red"))
                self.root.after(0, lambda: self.toast(f"Error: {e}", "error"))
            finally:
                self.root.after(0, self.bet_btn.enable)

        threading.Thread(target=_bet, daemon=True).start()


def main():
    root = tk.Tk()
    app = ModernPolymarketGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
