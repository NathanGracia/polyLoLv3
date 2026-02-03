"""
🎮 POLYMARKET BOT - MODERN NEON UI
Interface futuriste flat design sans popups
"""

import sys
import json
import tkinter as tk
from tkinter import ttk, font, filedialog
import threading
import requests
from datetime import datetime
from collections import deque
from bot import PolymarketLolBot
from database import BetDatabase
from bet_monitor import BetMonitor

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates

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
        self.is_refreshing_positions = False
        self.current_positions = []
        self.auto_confirm = tk.BooleanVar(value=False)

        # Price tracking for chart
        self.price_history = deque(maxlen=100)  # Store last 100 price points
        self.price_timestamps = deque(maxlen=100)
        self.chart_updater_running = False
        self.chart_canvas = None
        self.chart_figure = None
        self.chart_ax = None

        # Fonts
        self.font_title = font.Font(family="Arial", size=24, weight="bold")
        self.font_subtitle = font.Font(family="Arial", size=12)
        self.font_body = font.Font(family="Arial", size=10)
        self.font_small = font.Font(family="Arial", size=9)

        # Database and monitoring
        self.database = BetDatabase("bets.db")
        self.bet_monitor = None

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

        # Notebook (Tabbed Interface)
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background=self.bg, borderwidth=0, tabmargins=0)
        style.configure('TNotebook.Tab', background=self.bg_secondary,
                       foreground=self.text_gray, padding=[20, 10],
                       font=("Arial", 10, "bold"))
        style.map('TNotebook.Tab',
                 background=[('selected', self.bg)],
                 foreground=[('selected', self.neon_cyan)])

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Tab 1: Markets (existing content)
        main = tk.Frame(self.notebook, bg=self.bg)
        self.notebook.add(main, text="MARKETS")

        # Left: Markets (reduced width)
        left = tk.Frame(main, bg=self.bg, width=400)
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)

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
        div2.pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Right: Bet panel (wider to accommodate more content)
        right = tk.Frame(main, bg=self.bg)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)

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

        # Positions section
        positions_header = tk.Frame(right, bg=self.bg)
        positions_header.pack(fill=tk.X, pady=(0, 10))

        positions_label = tk.Label(positions_header, text="YOUR POSITIONS", bg=self.bg,
                                  fg=self.text_gray, font=("Arial", 10, "bold"))
        positions_label.pack(side=tk.LEFT)

        refresh_positions_btn = tk.Label(positions_header, text="↻ REFRESH", bg=self.bg,
                                        fg=self.neon_cyan, font=("Arial", 9),
                                        cursor="hand2")
        refresh_positions_btn.pack(side=tk.RIGHT)
        refresh_positions_btn.bind("<Button-1>", lambda e: self.refresh_positions())

        self.positions_frame = tk.Frame(right, bg=self.bg)
        self.positions_frame.pack(fill=tk.X, pady=(0, 20))

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

        # Buy and Sell buttons
        button_frame = tk.Frame(right, bg=self.bg)
        button_frame.pack(pady=(0, 20))

        self.buy_btn = NeonButton(button_frame, text="BUY",
                                 command=lambda: self.place_bet("BUY"),
                                 bg=self.bg, fg=self.neon_green,
                                 hover_fg=self.neon_cyan,
                                 width=210, height=80)
        self.buy_btn.pack(side=tk.LEFT, padx=5)
        self.buy_btn.disable()

        self.sell_btn = NeonButton(button_frame, text="SELL",
                                  command=lambda: self.place_bet("SELL"),
                                  bg=self.bg, fg=self.neon_red,
                                  hover_fg=self.neon_magenta,
                                  width=210, height=80)
        self.sell_btn.pack(side=tk.LEFT, padx=5)
        self.sell_btn.disable()

        # Active Bets for this market
        active_bets_label = tk.Label(right, text="ACTIVE BETS (THIS MARKET)", bg=self.bg,
                                    fg=self.neon_magenta, font=("Arial", 10, "bold"))
        active_bets_label.pack(pady=(20, 10), anchor=tk.W)

        active_bets_container = tk.Frame(right, bg=self.bg_secondary, height=150)
        active_bets_container.pack(fill=tk.X, pady=(0, 10))
        active_bets_container.pack_propagate(False)

        # Scrollable active bets
        active_scroll = tk.Scrollbar(active_bets_container, bg=self.bg_secondary)
        active_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.market_active_canvas = tk.Canvas(active_bets_container, bg=self.bg_secondary,
                                              highlightthickness=0, yscrollcommand=active_scroll.set)
        self.market_active_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        active_scroll.config(command=self.market_active_canvas.yview)

        self.market_active_frame = tk.Frame(self.market_active_canvas, bg=self.bg_secondary)
        self.market_active_canvas.create_window((0, 0), window=self.market_active_frame, anchor="nw")
        self.market_active_frame.bind("<Configure>",
                                     lambda e: self.market_active_canvas.configure(
                                         scrollregion=self.market_active_canvas.bbox("all")))

        # Price Chart
        chart_label = tk.Label(right, text="PRICE CHART (LIVE)", bg=self.bg,
                             fg=self.neon_cyan, font=("Arial", 10, "bold"))
        chart_label.pack(pady=(10, 10), anchor=tk.W)

        chart_container = tk.Frame(right, bg=self.bg_secondary, height=200)
        chart_container.pack(fill=tk.X, pady=(0, 10))
        chart_container.pack_propagate(False)

        # Create matplotlib chart
        self.chart_figure = Figure(figsize=(8, 2), facecolor='#0a0a0a')
        self.chart_ax = self.chart_figure.add_subplot(111)
        self.chart_ax.set_facecolor('#1a1a1a')
        self.chart_ax.tick_params(colors='#888888', labelsize=8)
        self.chart_ax.spines['bottom'].set_color('#00ffff')
        self.chart_ax.spines['top'].set_color('#1a1a1a')
        self.chart_ax.spines['right'].set_color('#1a1a1a')
        self.chart_ax.spines['left'].set_color('#00ffff')
        self.chart_ax.set_xlabel('Time', color='#888888', fontsize=8)
        self.chart_ax.set_ylabel('Price ($)', color='#888888', fontsize=8)
        self.chart_figure.tight_layout(pad=0.5)

        self.chart_canvas = FigureCanvasTkAgg(self.chart_figure, chart_container)
        self.chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Keep log_text for compatibility but make it invisible
        self.log_text = tk.Text(right, height=1)
        self.log_text.pack_forget()  # Hide it
        self.log_text.config(state=tk.DISABLED)
        # Log colors
        self.log_text.tag_config("cyan", foreground=self.neon_cyan)
        self.log_text.tag_config("green", foreground=self.neon_green)
        self.log_text.tag_config("red", foreground=self.neon_red)
        self.log_text.tag_config("magenta", foreground=self.neon_magenta)

        # Tab 2: Active Bets
        self.active_bets_tab = tk.Frame(self.notebook, bg=self.bg)
        self.notebook.add(self.active_bets_tab, text="ACTIVE BETS")
        self.create_active_bets_tab()

        # Tab 3: History
        self.history_tab = tk.Frame(self.notebook, bg=self.bg)
        self.notebook.add(self.history_tab, text="HISTORY")
        self.create_history_tab()

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
                self.bot.set_database(self.database)
                self.log("Connected successfully", "green")
                self.root.after(0, lambda: self.update_status("ONLINE", self.neon_green))

                # Start bet monitoring
                self.bet_monitor = BetMonitor(self.bot, self.database, self.handle_bet_event)
                self.bet_monitor.start()
                self.log("Bet monitoring started", "cyan")

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
        # Stop previous chart updater
        self.stop_chart_updater()

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

        self.buy_btn.enable()
        self.sell_btn.enable()
        self.log(f"Selected: {question[:50]}...", "magenta")

        # Refresh positions for this market
        self.refresh_positions()

        # Refresh active bets for this market
        self.refresh_market_active_bets()

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

        # Start chart updater for this outcome
        self.stop_chart_updater()
        self.start_chart_updater()

    def set_amount(self, amount):
        """Définir le montant."""
        self.amount_var.set(str(float(amount)))

    def place_bet(self, side="BUY"):
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
            confirm_win.geometry("400x280")
            confirm_win.configure(bg=self.bg)
            confirm_win.attributes('-topmost', True)

            side_color = self.neon_green if side == "BUY" else self.neon_red
            tk.Label(confirm_win, text=f"CONFIRM {side}", bg=self.bg, fg=side_color,
                    font=("Arial", 14, "bold")).pack(pady=20)

            tk.Label(confirm_win, text=f"Outcome: {outcome}", bg=self.bg, fg="white",
                    font=self.font_body).pack(pady=5)
            tk.Label(confirm_win, text=f"Side: {side}", bg=self.bg, fg=side_color,
                    font=self.font_body).pack(pady=5)
            tk.Label(confirm_win, text=f"Price: ${price:.4f}", bg=self.bg, fg="white",
                    font=self.font_body).pack(pady=5)
            tk.Label(confirm_win, text=f"Amount: ${amount:.2f}", bg=self.bg, fg=self.neon_green,
                    font=("Arial", 12, "bold")).pack(pady=5)

            btn_frame = tk.Frame(confirm_win, bg=self.bg)
            btn_frame.pack(pady=20)

            def confirm():
                confirm_win.destroy()
                self._execute_bet(token_id, price, amount, outcome, side)

            NeonButton(btn_frame, "CONFIRM", confirm, fg=self.neon_green,
                      width=150, height=40).pack(side=tk.LEFT, padx=5)
            NeonButton(btn_frame, "CANCEL", confirm_win.destroy, fg=self.neon_red,
                      width=150, height=40).pack(side=tk.LEFT, padx=5)
        else:
            self._execute_bet(token_id, price, amount, outcome, side)

    def _execute_bet(self, token_id, price, amount, outcome, side="BUY"):
        """Exécuter le pari."""
        self.buy_btn.disable()
        self.sell_btn.disable()
        self.log(f"Placing {side}: {outcome} ${amount:.2f}", "cyan")

        def _bet():
            try:
                # Set context for database insert
                if self.bot:
                    self.bot.set_current_market(self.selected_market)
                    self.bot.set_current_outcome(outcome)

                # Adjust price based on side
                adjusted_price = price + 0.01 if side == "BUY" else price - 0.01
                adjusted_price = max(0.01, min(0.99, adjusted_price))

                # Add 3% buffer to avoid "amount too small" errors due to rounding/slippage
                safe_amount = amount * 1.03

                result = self.bot.place_bet(
                    token_id=token_id,
                    side=side,
                    price=adjusted_price,
                    total_amount=safe_amount,
                    confirm=False
                )

                if result and result.get('success'):
                    order_id = result.get('orderID', 'N/A')[:16]
                    self.root.after(0, lambda: self.log(f"✓ {side} PLACED: {order_id}...", "green"))
                    self.root.after(0, lambda: self.toast(f"{side} placed! {order_id}...", "success"))
                    # Refresh positions and active bets after successful bet
                    self.root.after(0, self.refresh_positions)
                    self.root.after(500, self.refresh_market_active_bets)  # Small delay for DB insert
                else:
                    # Log detailed error info
                    error_msg = "Unknown error"
                    if result:
                        error_msg = result.get('error', result.get('errorMsg', str(result)))
                    self.root.after(0, lambda: self.log(f"✗ {side} failed: {error_msg}", "red"))
                    self.root.after(0, lambda: self.toast(f"{side} failed: {error_msg}", "error"))

            except Exception as e:
                self.root.after(0, lambda: self.log(f"✗ Error: {e}", "red"))
                self.root.after(0, lambda: self.toast(f"Error: {e}", "error"))
            finally:
                self.root.after(0, self.buy_btn.enable)
                self.root.after(0, self.sell_btn.enable)

        threading.Thread(target=_bet, daemon=True).start()

    def refresh_positions(self):
        """Refresh positions for the selected market."""
        if not self.bot or not self.selected_market or self.is_refreshing_positions:
            return

        market_id = self.selected_market.get("condition_id")

        def _refresh():
            try:
                self.is_refreshing_positions = True
                positions = self.bot.get_user_positions(market_id=market_id)
                self.current_positions = positions
                self.root.after(0, lambda: self.display_positions(positions))
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Error fetching positions: {e}", "red"))
            finally:
                self.is_refreshing_positions = False

        threading.Thread(target=_refresh, daemon=True).start()

    def display_positions(self, positions):
        """Display positions in the positions frame."""
        # Clear existing positions
        for widget in self.positions_frame.winfo_children():
            widget.destroy()

        if not positions:
            # Empty state
            no_pos = tk.Label(self.positions_frame, text="No positions in this market",
                            bg=self.bg, fg=self.text_gray,
                            font=self.font_small, pady=10)
            no_pos.pack()
            return

        # Display each position
        for position in positions:
            self.create_position_card(position)

    def create_position_card(self, position):
        """Create a single position card with P&L and action buttons."""
        card = tk.Frame(self.positions_frame, bg=self.bg_secondary,
                       highlightthickness=1, highlightbackground=self.bg_secondary)
        card.pack(fill=tk.X, pady=3)

        content = tk.Frame(card, bg=self.bg_secondary)
        content.pack(fill=tk.X, padx=10, pady=8)

        # Outcome name and direction
        net_size = position.get('net_size', 0)
        direction = "LONG" if net_size > 0 else "SHORT"
        direction_color = self.neon_green if net_size > 0 else self.neon_red
        direction_icon = "🟢" if net_size > 0 else "🔴"

        outcome_text = f"{direction_icon} {position.get('outcome', 'Unknown')} ({direction})"
        outcome_label = tk.Label(content, text=outcome_text, bg=self.bg_secondary,
                                fg="white", font=("Arial", 10, "bold"), anchor=tk.W)
        outcome_label.pack(anchor=tk.W)

        # Position details
        details = tk.Frame(content, bg=self.bg_secondary)
        details.pack(fill=tk.X, pady=(3, 0))

        size_text = f"{abs(net_size):.2f} shares @ ${position.get('avg_entry_price', 0):.4f}"
        tk.Label(details, text=size_text, bg=self.bg_secondary, fg=self.text_gray,
                font=self.font_small).pack(side=tk.LEFT, padx=(0, 10))

        current_text = f"Current: ${position.get('current_price', 0):.4f}"
        tk.Label(details, text=current_text, bg=self.bg_secondary, fg=self.neon_cyan,
                font=self.font_small).pack(side=tk.LEFT, padx=(0, 10))

        # P&L
        pnl = position.get('unrealized_pnl', 0)
        roi = position.get('unrealized_roi', 0)
        pnl_color = self.neon_green if pnl > 0 else self.neon_red
        pnl_text = f"P&L: ${pnl:+.2f} ({roi:+.1f}%)"
        tk.Label(details, text=pnl_text, bg=self.bg_secondary, fg=pnl_color,
                font=("Arial", 9, "bold")).pack(side=tk.LEFT)

        # Quick sell buttons (only show for long positions)
        if net_size > 0:
            actions = tk.Frame(content, bg=self.bg_secondary)
            actions.pack(fill=tk.X, pady=(5, 0))

            for pct, label in [(0.25, "25%"), (0.5, "50%"), (1.0, "ALL")]:
                btn = tk.Label(actions, text=f"SELL {label}", bg=self.bg,
                             fg=self.neon_red, font=("Arial", 8, "bold"),
                             cursor="hand2", padx=8, pady=3)
                btn.pack(side=tk.LEFT, padx=2)
                btn.bind("<Button-1>", lambda e, t=position['token_id'], s=net_size*pct:
                        self.quick_sell(t, s))

    def quick_sell(self, token_id, size):
        """Quick sell action for positions."""
        if not self.bot:
            return

        # Get current price for this token
        current_price = self.bot.get_token_price(token_id)
        if current_price is None:
            self.toast("Cannot get current price", "error")
            return

        # Find the outcome name from positions
        outcome = "Position"
        for pos in self.current_positions:
            if pos['token_id'] == token_id:
                outcome = pos.get('outcome', 'Position')
                break

        # Calculate amount
        amount = size * current_price

        if amount < 1.0:
            self.toast("Sell amount too small (min $1)", "warning")
            return

        self.log(f"Quick sell: {size:.2f} shares of {outcome}", "cyan")

        # Disable buttons
        self.buy_btn.disable()
        self.sell_btn.disable()

        def _sell():
            try:
                # Adjust price for immediate execution
                adjusted_price = max(0.01, current_price - 0.01)

                # Add buffer only if close to minimum to avoid rounding errors
                # If amount < $2, add 5% buffer. Otherwise add 1% for safety.
                buffer = 1.05 if amount < 2.0 else 1.01
                safe_size = size * buffer

                result = self.bot.place_bet(
                    token_id=token_id,
                    side="SELL",
                    price=adjusted_price,
                    size=safe_size,
                    confirm=False
                )

                if result and result.get('success'):
                    order_id = result.get('orderID', 'N/A')[:16]
                    self.root.after(0, lambda: self.log(f"✓ SELL PLACED: {order_id}...", "green"))
                    self.root.after(0, lambda: self.toast(f"Sell placed! {order_id}...", "success"))
                    # Refresh positions
                    self.root.after(0, self.refresh_positions)
                else:
                    error_msg = "Unknown error"
                    if result:
                        error_msg = result.get('error', result.get('errorMsg', str(result)))
                    self.root.after(0, lambda: self.log(f"✗ Sell failed: {error_msg}", "red"))
                    self.root.after(0, lambda: self.toast(f"Sell failed: {error_msg}", "error"))

            except Exception as e:
                self.root.after(0, lambda: self.log(f"✗ Error: {e}", "red"))
                self.root.after(0, lambda: self.toast(f"Error: {e}", "error"))
            finally:
                self.root.after(0, self.buy_btn.enable)
                self.root.after(0, self.sell_btn.enable)

        threading.Thread(target=_sell, daemon=True).start()

    def refresh_market_active_bets(self):
        """Refresh active bets for the currently selected market."""
        if not self.selected_market:
            return

        market_id = self.selected_market.get("condition_id")

        try:
            # Get all active bets
            all_active = self.database.get_active_bets()

            # Filter by market_id
            market_bets = [bet for bet in all_active if bet.get('market_id') == market_id]

            # Clear existing
            for widget in self.market_active_frame.winfo_children():
                widget.destroy()

            if not market_bets:
                no_bets = tk.Label(self.market_active_frame, text="No active bets for this market",
                                  bg=self.bg_secondary, fg=self.text_gray,
                                  font=self.font_small, pady=20)
                no_bets.pack()
                return

            # Display each bet
            for bet in market_bets:
                self.create_compact_bet_card(self.market_active_frame, bet)

        except Exception as e:
            print(f"Error refreshing market active bets: {e}")

    def create_compact_bet_card(self, parent, bet):
        """Create a compact bet card for the market panel."""
        card = tk.Frame(parent, bg=self.bg, highlightthickness=1,
                       highlightbackground=self.bg_secondary)
        card.pack(fill=tk.X, pady=2, padx=5)

        content = tk.Frame(card, bg=self.bg)
        content.pack(fill=tk.X, padx=8, pady=6)

        # Outcome and side
        outcome = bet.get('outcome', 'N/A')
        side = bet.get('side', 'N/A')
        side_color = self.neon_green if side == 'BUY' else self.neon_red

        outcome_text = f"{side} {outcome}"
        tk.Label(content, text=outcome_text, bg=self.bg, fg=side_color,
                font=("Arial", 9, "bold"), anchor=tk.W).pack(side=tk.LEFT)

        # Amount
        amount = bet.get('amount_spent', 0)
        tk.Label(content, text=f"${amount:.2f}", bg=self.bg, fg=self.neon_cyan,
                font=("Arial", 9, "bold")).pack(side=tk.RIGHT, padx=5)

        # Status
        status = bet.get('status', 'unknown')
        status_icons = {'pending': '⏳', 'active': '●', 'settled': '✓', 'cancelled': '✗'}
        status_icon = status_icons.get(status, '?')
        tk.Label(content, text=status_icon, bg=self.bg, fg=self.text_gray,
                font=("Arial", 9)).pack(side=tk.RIGHT)

    def start_chart_updater(self):
        """Start updating the price chart in real-time."""
        if self.chart_updater_running:
            return

        self.chart_updater_running = True
        self.price_history.clear()
        self.price_timestamps.clear()

        def _update_chart():
            while self.chart_updater_running and self.selected_market:
                try:
                    # Get current price for selected outcome
                    if self.selected_outcome_idx is not None:
                        prices = json.loads(self.selected_market.get("outcomePrices", "[]"))
                        tokens = json.loads(self.selected_market.get("clobTokenIds", "[]"))

                        if self.selected_outcome_idx < len(tokens):
                            token_id = tokens[self.selected_outcome_idx]
                            current_price = self.bot.get_token_price(token_id)

                            if current_price is not None:
                                # Add to history
                                self.price_timestamps.append(datetime.now())
                                self.price_history.append(current_price)

                                # Update chart
                                self.root.after(0, self.update_chart_display)

                except Exception as e:
                    print(f"Chart update error: {e}")

                # Update every 5 seconds
                for _ in range(50):  # 5 seconds = 50 * 0.1s
                    if not self.chart_updater_running:
                        break
                    threading.Event().wait(0.1)

        threading.Thread(target=_update_chart, daemon=True).start()

    def stop_chart_updater(self):
        """Stop the chart updater."""
        self.chart_updater_running = False

    def update_chart_display(self):
        """Update the matplotlib chart with current price history."""
        if not self.price_history or not self.chart_ax:
            return

        try:
            self.chart_ax.clear()

            # Plot price history
            times = list(self.price_timestamps)
            prices = list(self.price_history)

            self.chart_ax.plot(times, prices, color='#00ffff', linewidth=2)
            self.chart_ax.fill_between(times, prices, alpha=0.2, color='#00ffff')

            # Styling
            self.chart_ax.set_facecolor('#1a1a1a')
            self.chart_ax.tick_params(colors='#888888', labelsize=7)
            self.chart_ax.spines['bottom'].set_color('#00ffff')
            self.chart_ax.spines['top'].set_color('#1a1a1a')
            self.chart_ax.spines['right'].set_color('#1a1a1a')
            self.chart_ax.spines['left'].set_color('#00ffff')

            # Format x-axis
            self.chart_ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            self.chart_figure.autofmt_xdate(rotation=45, ha='right')

            # Labels
            self.chart_ax.set_ylabel('Price ($)', color='#888888', fontsize=8)
            self.chart_ax.grid(True, alpha=0.1, color='#00ffff')

            self.chart_figure.tight_layout(pad=0.3)
            self.chart_canvas.draw()

        except Exception as e:
            print(f"Error updating chart display: {e}")

    def create_active_bets_tab(self):
        """Create Active Bets tab UI."""
        # Header
        header = tk.Frame(self.active_bets_tab, bg=self.bg)
        header.pack(fill=tk.X, pady=(20, 10))

        title = tk.Label(header, text="ACTIVE BETS", bg=self.bg,
                        fg=self.neon_green, font=("Arial", 14, "bold"))
        title.pack(side=tk.LEFT)

        self.active_count_label = tk.Label(header, text="(0)", bg=self.bg,
                                          fg=self.text_gray, font=self.font_small)
        self.active_count_label.pack(side=tk.LEFT, padx=10)

        refresh_btn = tk.Label(header, text="↻ REFRESH", bg=self.bg,
                              fg=self.neon_cyan, font=("Arial", 9, "bold"),
                              cursor="hand2")
        refresh_btn.pack(side=tk.RIGHT)
        refresh_btn.bind("<Button-1>", lambda e: self.refresh_active_bets())

        # Scrollable list
        list_container = tk.Frame(self.active_bets_tab, bg=self.bg_secondary)
        list_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        scrollbar = tk.Scrollbar(list_container, bg=self.bg_secondary,
                                troughcolor=self.bg, activebackground=self.neon_cyan)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.active_canvas = tk.Canvas(list_container, bg=self.bg_secondary,
                                       highlightthickness=0, yscrollcommand=scrollbar.set)
        self.active_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.active_canvas.yview)

        self.active_frame = tk.Frame(self.active_canvas, bg=self.bg_secondary)
        self.active_canvas.create_window((0, 0), window=self.active_frame, anchor="nw")

        self.active_frame.bind("<Configure>",
                              lambda e: self.active_canvas.configure(scrollregion=self.active_canvas.bbox("all")))

        # Auto-refresh every 30s
        self.refresh_active_bets()

    def refresh_active_bets(self):
        """Refresh active bets display."""
        try:
            active_bets = self.database.get_active_bets()

            # Clear existing
            for widget in self.active_frame.winfo_children():
                widget.destroy()

            self.active_count_label.config(text=f"({len(active_bets)})")

            if not active_bets:
                no_bets = tk.Label(self.active_frame, text="No active bets",
                                  bg=self.bg_secondary, fg=self.text_gray,
                                  font=self.font_body, pady=50)
                no_bets.pack()
                self.root.after(30000, self.refresh_active_bets)
                return

            for bet in active_bets:
                self.create_bet_card(self.active_frame, bet, show_pnl=False, show_delete=True)

            # Auto-refresh
            self.root.after(30000, self.refresh_active_bets)

        except Exception as e:
            print(f"Error refreshing active bets: {e}")

    def create_history_tab(self):
        """Create History tab UI."""
        # Header
        header = tk.Frame(self.history_tab, bg=self.bg)
        header.pack(fill=tk.X, pady=(20, 10))

        title = tk.Label(header, text="BET HISTORY", bg=self.bg,
                        fg=self.neon_magenta, font=("Arial", 14, "bold"))
        title.pack(side=tk.LEFT)

        self.history_count_label = tk.Label(header, text="(0)", bg=self.bg,
                                           fg=self.text_gray, font=self.font_small)
        self.history_count_label.pack(side=tk.LEFT, padx=10)

        # Filters
        filter_frame = tk.Frame(self.history_tab, bg=self.bg_secondary)
        filter_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        tk.Label(filter_frame, text="Status:", bg=self.bg_secondary,
                fg=self.text_gray, font=self.font_small).pack(side=tk.LEFT, padx=(10, 5))

        self.status_filter_var = tk.StringVar(value="all")
        status_menu = ttk.Combobox(filter_frame, textvariable=self.status_filter_var,
                                   values=["all", "pending", "active", "settled", "cancelled"],
                                   width=10, state="readonly")
        status_menu.pack(side=tk.LEFT, padx=5)
        status_menu.bind("<<ComboboxSelected>>", lambda e: self.refresh_history())

        tk.Label(filter_frame, text="Period:", bg=self.bg_secondary,
                fg=self.text_gray, font=self.font_small).pack(side=tk.LEFT, padx=(20, 5))

        self.period_filter_var = tk.StringVar(value="all")
        period_menu = ttk.Combobox(filter_frame, textvariable=self.period_filter_var,
                                   values=["all", "7 days", "30 days"],
                                   width=10, state="readonly")
        period_menu.pack(side=tk.LEFT, padx=5)
        period_menu.bind("<<ComboboxSelected>>", lambda e: self.refresh_history())

        # Search
        tk.Label(filter_frame, text="Search:", bg=self.bg_secondary,
                fg=self.text_gray, font=self.font_small).pack(side=tk.LEFT, padx=(20, 5))

        self.search_history_var = tk.StringVar()
        search_entry = tk.Entry(filter_frame, textvariable=self.search_history_var,
                               bg=self.bg, fg="white", font=self.font_small,
                               width=20, insertbackground=self.neon_cyan)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<Return>", lambda e: self.refresh_history())

        search_btn = tk.Label(filter_frame, text="🔍", bg=self.bg_secondary,
                             fg=self.neon_cyan, font=("Arial", 12),
                             cursor="hand2")
        search_btn.pack(side=tk.LEFT, padx=5)
        search_btn.bind("<Button-1>", lambda e: self.refresh_history())

        # Export button
        export_btn = NeonButton(filter_frame, text="EXPORT CSV",
                               command=self.export_history,
                               bg=self.bg_secondary, fg=self.neon_green,
                               width=120, height=30)
        export_btn.pack(side=tk.RIGHT, padx=10, pady=5)

        # Scrollable list
        list_container = tk.Frame(self.history_tab, bg=self.bg_secondary)
        list_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        scrollbar = tk.Scrollbar(list_container, bg=self.bg_secondary,
                                troughcolor=self.bg, activebackground=self.neon_cyan)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.history_canvas = tk.Canvas(list_container, bg=self.bg_secondary,
                                        highlightthickness=0, yscrollcommand=scrollbar.set)
        self.history_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.history_canvas.yview)

        self.history_frame = tk.Frame(self.history_canvas, bg=self.bg_secondary)
        self.history_canvas.create_window((0, 0), window=self.history_frame, anchor="nw")

        self.history_frame.bind("<Configure>",
                               lambda e: self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all")))

        # Initial load
        self.refresh_history()

    def refresh_history(self):
        """Refresh history display with current filters."""
        try:
            filters = {}

            # Status filter
            status = self.status_filter_var.get()
            if status != "all":
                filters['status'] = status

            # Period filter
            period = self.period_filter_var.get()
            if period == "7 days":
                filters['period_days'] = 7
            elif period == "30 days":
                filters['period_days'] = 30

            # Search filter
            search = self.search_history_var.get().strip()
            if search:
                filters['search'] = search

            bets = self.database.get_bet_history(filters)

            # Clear existing
            for widget in self.history_frame.winfo_children():
                widget.destroy()

            self.history_count_label.config(text=f"({len(bets)})")

            if not bets:
                no_bets = tk.Label(self.history_frame, text="No bets found",
                                  bg=self.bg_secondary, fg=self.text_gray,
                                  font=self.font_body, pady=50)
                no_bets.pack()
                return

            for bet in bets:
                self.create_bet_card(self.history_frame, bet, show_pnl=True)

        except Exception as e:
            print(f"Error refreshing history: {e}")

    def create_bet_card(self, parent, bet, show_pnl=False, show_delete=False):
        """Create a bet card UI element."""
        card = tk.Frame(parent, bg=self.bg, highlightthickness=1,
                       highlightbackground=self.bg_secondary)
        card.pack(fill=tk.X, pady=5, padx=10)

        content = tk.Frame(card, bg=self.bg)
        content.pack(fill=tk.X, padx=15, pady=15)

        # Market question
        question = bet.get('market_question', 'Unknown market')
        question_label = tk.Label(content, text=question[:80] + ("..." if len(question) > 80 else ""),
                                 bg=self.bg, fg="white", font=self.font_body,
                                 wraplength=900, justify=tk.LEFT)
        question_label.pack(anchor=tk.W)

        # Details row
        details = tk.Frame(content, bg=self.bg)
        details.pack(fill=tk.X, pady=(5, 0))

        outcome_text = f"Outcome: {bet.get('outcome', 'N/A')}"
        tk.Label(details, text=outcome_text, bg=self.bg, fg=self.text_gray,
                font=self.font_small).pack(side=tk.LEFT, padx=(0, 15))

        side_text = f"Side: {bet.get('side', 'N/A')}"
        tk.Label(details, text=side_text, bg=self.bg, fg=self.text_gray,
                font=self.font_small).pack(side=tk.LEFT, padx=(0, 15))

        price_text = f"Entry: ${bet.get('price', 0):.4f}"
        tk.Label(details, text=price_text, bg=self.bg, fg=self.neon_cyan,
                font=self.font_small).pack(side=tk.LEFT, padx=(0, 15))

        amount_text = f"Amount: ${bet.get('amount_spent', 0):.2f}"
        tk.Label(details, text=amount_text, bg=self.bg, fg=self.neon_green,
                font=self.font_small).pack(side=tk.LEFT, padx=(0, 15))

        # Status
        status = bet.get('status', 'unknown')
        status_colors = {
            'pending': self.neon_cyan,
            'active': self.neon_green,
            'settled': self.text_gray,
            'cancelled': self.neon_red
        }
        status_icons = {
            'pending': '⏳',
            'active': '●',
            'settled': '✓',
            'cancelled': '✗'
        }

        status_color = status_colors.get(status, self.text_gray)
        status_icon = status_icons.get(status, '?')
        status_text = f"{status_icon} {status.upper()}"

        tk.Label(details, text=status_text, bg=self.bg, fg=status_color,
                font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 15))

        # Delete button for active bets
        if show_delete:
            delete_btn = tk.Label(details, text="✗ DELETE", bg=self.bg,
                                fg=self.neon_red, font=("Arial", 8, "bold"),
                                cursor="hand2", padx=8, pady=2)
            delete_btn.pack(side=tk.RIGHT, padx=(15, 0))
            delete_btn.bind("<Button-1>", lambda e: self.delete_bet(bet['bet_id']))

        # P&L if settled and show_pnl
        if show_pnl and status == 'settled' and bet.get('pnl') is not None:
            pnl = bet.get('pnl', 0)
            pnl_text = f"P&L: ${pnl:+.2f}"
            pnl_color = self.neon_green if pnl > 0 else self.neon_red

            tk.Label(details, text=pnl_text, bg=self.bg, fg=pnl_color,
                    font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 15))

            if bet.get('roi') is not None:
                roi_text = f"({bet.get('roi'):+.1f}%)"
                tk.Label(details, text=roi_text, bg=self.bg, fg=pnl_color,
                        font=self.font_small).pack(side=tk.LEFT)

        # Timestamp
        placed_at = bet.get('placed_at', '')
        if placed_at:
            try:
                dt = datetime.fromisoformat(placed_at) if isinstance(placed_at, str) else placed_at
                time_str = dt.strftime("%Y-%m-%d %H:%M")
                tk.Label(details, text=f"Placed: {time_str}", bg=self.bg,
                        fg=self.text_gray, font=self.font_small).pack(side=tk.RIGHT)
            except:
                pass

    def delete_bet(self, bet_id):
        """Delete bet from database with confirmation."""
        # Create confirmation dialog
        confirm_win = tk.Toplevel(self.root)
        confirm_win.title("Delete Bet")
        confirm_win.geometry("400x200")
        confirm_win.configure(bg=self.bg)
        confirm_win.attributes('-topmost', True)

        tk.Label(confirm_win, text="DELETE BET?", bg=self.bg, fg=self.neon_red,
                font=("Arial", 14, "bold")).pack(pady=20)

        tk.Label(confirm_win, text="This will remove the bet from your database.",
                bg=self.bg, fg=self.text_gray,
                font=self.font_body).pack(pady=5)

        tk.Label(confirm_win, text="(Useful if you traded on the web interface)",
                bg=self.bg, fg=self.text_gray,
                font=self.font_small).pack(pady=5)

        btn_frame = tk.Frame(confirm_win, bg=self.bg)
        btn_frame.pack(pady=20)

        def confirm_delete():
            try:
                self.database.update_bet_status(bet_id, 'deleted')
                self.log(f"Bet #{bet_id} deleted from database", "cyan")
                self.toast("Bet deleted", "success")
                confirm_win.destroy()
                # Refresh active bets view
                self.refresh_active_bets()
            except Exception as e:
                self.log(f"Error deleting bet: {e}", "red")
                self.toast(f"Delete failed: {e}", "error")

        NeonButton(btn_frame, "DELETE", confirm_delete, fg=self.neon_red,
                  width=150, height=40).pack(side=tk.LEFT, padx=5)
        NeonButton(btn_frame, "CANCEL", confirm_win.destroy, fg=self.text_gray,
                  width=150, height=40).pack(side=tk.LEFT, padx=5)

    def export_history(self):
        """Export history to CSV."""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=f"polymarket_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )

            if filename:
                # Get current filters
                filters = {}
                status = self.status_filter_var.get()
                if status != "all":
                    filters['status'] = status

                period = self.period_filter_var.get()
                if period == "7 days":
                    filters['period_days'] = 7
                elif period == "30 days":
                    filters['period_days'] = 30

                search = self.search_history_var.get().strip()
                if search:
                    filters['search'] = search

                self.database.export_to_csv(filename, filters)
                self.toast(f"Exported to {filename}", "success")
                self.log(f"History exported to CSV", "green")

        except Exception as e:
            self.toast(f"Export failed: {e}", "error")
            self.log(f"Export failed: {e}", "red")

    def handle_bet_event(self, event):
        """Handle bet status change events from monitor."""
        try:
            bet = event['bet']
            new_status = event['new_status']

            if new_status == 'active':
                self.root.after(0, lambda: self.toast(f"✓ Bet filled: {bet.get('outcome', 'N/A')}", "success"))
                self.root.after(0, lambda: self.log(f"Bet filled: {bet.get('market_question', 'N/A')[:40]}...", "green"))

            elif new_status == 'settled':
                pnl = bet.get('pnl', 0)
                pnl_text = f"+${pnl:.2f}" if pnl > 0 else f"${pnl:.2f}"
                toast_type = "success" if pnl > 0 else "error"
                self.root.after(0, lambda: self.toast(f"Bet settled: {pnl_text}", toast_type))
                color = "green" if pnl > 0 else "red"
                self.root.after(0, lambda: self.log(f"Settled: {pnl_text} on {bet.get('market_question', 'N/A')[:30]}...", color))

            elif new_status == 'cancelled':
                self.root.after(0, lambda: self.toast(f"Bet cancelled: {bet.get('outcome', 'N/A')}", "warning"))
                self.root.after(0, lambda: self.log(f"Bet cancelled: {bet.get('outcome', 'N/A')}", "red"))

            # Refresh active bets tab and market active bets
            self.root.after(0, self.refresh_active_bets)
            self.root.after(0, self.refresh_market_active_bets)

        except Exception as e:
            print(f"Error handling bet event: {e}")


def main():
    root = tk.Tk()
    app = ModernPolymarketGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
