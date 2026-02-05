"""
🎮 POLYMARKET BOT - ULTRA-SIMPLE FAST TRADING
2 clicks, <3 seconds, no tracking, no popups
"""

import sys
import json
import os
import tkinter as tk
from tkinter import font
import threading
import requests
from datetime import datetime, timedelta
from collections import deque
from bot import PolymarketLolBot
from dotenv import load_dotenv

# Matplotlib for price chart
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Load env and setup proxy for GUI requests
load_dotenv()
proxy_http = os.getenv("PROXY_HTTP", "").strip()
proxy_https = os.getenv("PROXY_HTTPS", "").strip()

GUI_PROXIES = None
if proxy_http or proxy_https:
    GUI_PROXIES = {}
    if proxy_http:
        GUI_PROXIES['http'] = proxy_http
    if proxy_https:
        GUI_PROXIES['https'] = proxy_https

# Create global session with proxy for GUI requests
GUI_SESSION = requests.Session()
if GUI_PROXIES:
    GUI_SESSION.proxies.update(GUI_PROXIES)


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

    def config(self, **kwargs):
        """Update button config."""
        if 'text' in kwargs:
            self.text = kwargs['text']
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


class UltraSimplePolymarketGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("POLYMARKET - ULTRA FAST")
        self.root.geometry("1400x750")

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
        self.selected_market_live_prices = []  # Store live prices for selected market
        self.is_refreshing = False
        self.price_refresh_active = False  # Control price refresh loop
        self.price_refresh_counter = 0  # Count refreshes

        # Price history for chart (5 minutes = 300 seconds, 1 point per 1 second = 300 points max)
        self.price_history = {
            'timestamps': deque(maxlen=300),
            'yes_prices': deque(maxlen=300),
            'no_prices': deque(maxlen=300)
        }

        # Fonts (REDUCED SIZES)
        self.font_title = font.Font(family="Arial", size=16, weight="bold")
        self.font_subtitle = font.Font(family="Arial", size=9)
        self.font_body = font.Font(family="Arial", size=8)
        self.font_small = font.Font(family="Arial", size=7)

        self.create_ui()
        self.init_bot()

    def create_ui(self):
        """Créer l'interface ultra-simple."""

        # Header (COMPACT)
        header = tk.Frame(self.root, bg=self.bg, height=40)
        header.pack(fill=tk.X, padx=15, pady=5)
        header.pack_propagate(False)

        title = tk.Label(header, text="POLYMARKET", bg=self.bg,
                        fg=self.neon_cyan, font=self.font_title)
        title.pack(side=tk.LEFT, pady=10)

        subtitle = tk.Label(header, text="LIGHTNING FAST BETTING", bg=self.bg,
                           fg=self.text_gray, font=self.font_subtitle)
        subtitle.pack(side=tk.LEFT, padx=15, pady=10)

        self.status_dot = tk.Canvas(header, width=8, height=8, bg=self.bg,
                                   highlightthickness=0)
        self.status_dot.pack(side=tk.RIGHT, padx=5, pady=15)
        self.status_dot.create_oval(1, 1, 7, 7, fill=self.text_gray, outline="")

        self.status_label = tk.Label(header, text="CONNECTING", bg=self.bg,
                                    fg=self.text_gray, font=self.font_small)
        self.status_label.pack(side=tk.RIGHT, pady=15)

        # Divider
        div1 = tk.Frame(self.root, bg=self.neon_cyan, height=1)
        div1.pack(fill=tk.X, padx=15)

        # Main container
        main = tk.Frame(self.root, bg=self.bg)
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # Left: Markets (reduced width to 280px)
        left = tk.Frame(main, bg=self.bg, width=280)
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)

        markets_header = tk.Frame(left, bg=self.bg)
        markets_header.pack(fill=tk.X, pady=(0, 5))

        markets_label = tk.Label(markets_header, text="MARKETS", bg=self.bg,
                                fg=self.neon_magenta, font=("Arial", 10, "bold"))
        markets_label.pack(side=tk.LEFT)

        self.market_count = tk.Label(markets_header, text="0", bg=self.bg,
                                    fg=self.text_gray, font=self.font_small)
        self.market_count.pack(side=tk.LEFT, padx=5)

        # Search hint
        hint_label = tk.Label(markets_header, text="(empty = all)", bg=self.bg,
                            fg=self.text_gray, font=("Arial", 6))
        hint_label.pack(side=tk.RIGHT)

        # Search
        search_frame = tk.Frame(left, bg=self.bg_secondary, height=28)
        search_frame.pack(fill=tk.X, pady=(0, 3))
        search_frame.pack_propagate(False)

        self.search_var = tk.StringVar(value="")
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                    bg=self.bg_secondary, fg="white",
                                    font=self.font_body, relief=tk.FLAT,
                                    insertbackground=self.neon_cyan)
        self.search_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=3)
        self.search_entry.bind("<Return>", lambda e: self.search_markets())

        search_btn = tk.Label(search_frame, text="SEARCH", bg=self.bg_secondary,
                            fg=self.neon_cyan, font=("Arial", 7, "bold"),
                            cursor="hand2")
        search_btn.pack(side=tk.RIGHT, padx=5)
        search_btn.bind("<Button-1>", lambda e: self.search_markets())

        # URL input (NEW)
        url_frame = tk.Frame(left, bg=self.bg_secondary, height=28)
        url_frame.pack(fill=tk.X, pady=(0, 5))
        url_frame.pack_propagate(False)

        self.url_var = tk.StringVar(value="")
        self.url_entry = tk.Entry(url_frame, textvariable=self.url_var,
                                  bg=self.bg_secondary, fg=self.neon_magenta,
                                  font=("Arial", 7), relief=tk.FLAT,
                                  insertbackground=self.neon_magenta)
        self.url_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=3)
        self.url_entry.bind("<Return>", lambda e: self.load_from_url())

        # Placeholder text for URL
        self.url_entry.insert(0, "Or paste Polymarket URL...")
        self.url_entry.bind("<FocusIn>", lambda e: self.url_entry.delete(0, tk.END) if self.url_entry.get() == "Or paste Polymarket URL..." else None)
        self.url_entry.config(fg=self.text_gray)
        self.url_entry.bind("<KeyPress>", lambda e: self.url_entry.config(fg=self.neon_magenta))

        url_btn = tk.Label(url_frame, text="LOAD", bg=self.bg_secondary,
                          fg=self.neon_magenta, font=("Arial", 7, "bold"),
                          cursor="hand2")
        url_btn.pack(side=tk.RIGHT, padx=5)
        url_btn.bind("<Button-1>", lambda e: self.load_from_url())

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

        # Mouse wheel scrolling
        def _on_mousewheel(event):
            self.markets_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        self.markets_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Divider vertical
        div2 = tk.Frame(main, bg=self.neon_cyan, width=1)
        div2.pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Right: Bet panel (COMPACT)
        right = tk.Frame(main, bg=self.bg)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        # Top section: Bet controls
        bet_controls = tk.Frame(right, bg=self.bg)
        bet_controls.pack(fill=tk.X)

        bet_header = tk.Label(bet_controls, text="PLACE BET", bg=self.bg,
                            fg=self.neon_green, font=("Arial", 10, "bold"))
        bet_header.pack(pady=(0, 5))

        # Market title
        self.market_title_label = tk.Label(bet_controls, text="SELECT A MARKET", bg=self.bg,
                                          fg=self.text_gray, font=self.font_body,
                                          wraplength=500, justify=tk.LEFT)
        self.market_title_label.pack(pady=(0, 8))

        # Outcomes display (just display, not clickable)
        outcomes_label = tk.Label(bet_controls, text="OUTCOMES", bg=self.bg,
                                fg=self.text_gray, font=("Arial", 8, "bold"))
        outcomes_label.pack(pady=(0, 3), anchor=tk.W)

        self.outcomes_frame = tk.Frame(bet_controls, bg=self.bg)
        self.outcomes_frame.pack(fill=tk.X, pady=(0, 8))

        # Amount and Buffer in one row
        config_row = tk.Frame(bet_controls, bg=self.bg)
        config_row.pack(fill=tk.X, pady=(0, 5))

        # Amount (left)
        amount_col = tk.Frame(config_row, bg=self.bg)
        amount_col.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        amount_label = tk.Label(amount_col, text="AMOUNT", bg=self.bg,
                              fg=self.text_gray, font=("Arial", 8, "bold"))
        amount_label.pack(pady=(0, 3), anchor=tk.W)

        amount_container = tk.Frame(amount_col, bg=self.bg_secondary, height=35)
        amount_container.pack(fill=tk.X)
        amount_container.pack_propagate(False)

        dollar = tk.Label(amount_container, text="$", bg=self.bg_secondary,
                         fg=self.neon_cyan, font=("Arial", 14, "bold"))
        dollar.pack(side=tk.LEFT, padx=5)

        self.amount_var = tk.StringVar(value="1.0")
        self.amount_entry = tk.Entry(amount_container, textvariable=self.amount_var,
                                    bg=self.bg_secondary, fg="white",
                                    font=("Arial", 14), relief=tk.FLAT,
                                    insertbackground=self.neon_cyan,
                                    justify=tk.CENTER)
        self.amount_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=3)

        # Buffer (right)
        buffer_col = tk.Frame(config_row, bg=self.bg)
        buffer_col.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        buffer_label = tk.Label(buffer_col, text="PRICE BUFFER %", bg=self.bg,
                              fg=self.text_gray, font=("Arial", 8, "bold"))
        buffer_label.pack(pady=(0, 3), anchor=tk.W)

        buffer_container = tk.Frame(buffer_col, bg=self.bg_secondary, height=35)
        buffer_container.pack(fill=tk.X)
        buffer_container.pack_propagate(False)

        percent = tk.Label(buffer_container, text="%", bg=self.bg_secondary,
                         fg=self.neon_magenta, font=("Arial", 12, "bold"))
        percent.pack(side=tk.LEFT, padx=5)

        self.buffer_var = tk.StringVar(value="0.5")
        self.buffer_entry = tk.Entry(buffer_container, textvariable=self.buffer_var,
                                    bg=self.bg_secondary, fg="white",
                                    font=("Arial", 12), relief=tk.FLAT,
                                    insertbackground=self.neon_magenta,
                                    justify=tk.CENTER)
        self.buffer_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=3)

        # Quick amounts
        quick_frame = tk.Frame(bet_controls, bg=self.bg)
        quick_frame.pack(fill=tk.X, pady=(0, 8))

        for amount in [1, 5, 10, 25, 50, 100]:
            btn = tk.Label(quick_frame, text=f"{amount}", bg=self.bg_secondary,
                          fg=self.neon_cyan, font=("Arial", 7),
                          cursor="hand2", width=5, height=1, padx=3, pady=2)
            btn.pack(side=tk.LEFT, padx=1)
            btn.bind("<Button-1>", lambda e, a=amount: self.set_amount(a))

        # 2 BUTTONS: BUY YES / BUY NO (SIDE BY SIDE)
        button_frame = tk.Frame(bet_controls, bg=self.bg)
        button_frame.pack(fill=tk.X, pady=(5, 10))

        self.buy_yes_btn = NeonButton(button_frame, text="BUY YES",
                                 command=lambda: self.fast_buy(0),
                                 bg=self.bg, fg=self.neon_green,
                                 hover_fg=self.neon_cyan,
                                 width=200, height=60)
        self.buy_yes_btn.pack(side=tk.LEFT, padx=(0, 5), expand=True)
        self.buy_yes_btn.disable()

        self.buy_no_btn = NeonButton(button_frame, text="BUY NO",
                                  command=lambda: self.fast_buy(1),
                                  bg=self.bg, fg=self.neon_red,
                                  hover_fg=self.neon_magenta,
                                  width=200, height=60)
        self.buy_no_btn.pack(side=tk.LEFT, padx=(5, 0), expand=True)
        self.buy_no_btn.disable()

        # PRICE CHART (NEW!)
        chart_frame = tk.Frame(right, bg=self.bg_secondary, highlightbackground=self.neon_cyan, highlightthickness=1)
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        chart_header = tk.Label(chart_frame, text="PRICE CHART (5 MIN)", bg=self.bg_secondary,
                               fg=self.neon_magenta, font=("Arial", 8, "bold"))
        chart_header.pack(pady=3)

        # Create matplotlib figure
        self.fig = Figure(figsize=(8, 3), facecolor='#0a0a0a')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#0a0a0a')
        self.ax.tick_params(colors='#888888', labelsize=7)
        self.ax.spines['bottom'].set_color('#888888')
        self.ax.spines['left'].set_color('#888888')
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.set_ylim(0, 1)
        self.ax.set_ylabel('Price', color='#888888', fontsize=8)
        self.ax.grid(True, alpha=0.2, color='#888888')

        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        # Activity log (COMPACT - at bottom of window)
        log_frame = tk.Frame(self.root, bg=self.bg_secondary, height=80)
        log_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=15, pady=(0, 5))
        log_frame.pack_propagate(False)

        log_label = tk.Label(log_frame, text="ACTIVITY LOG", bg=self.bg_secondary,
                           fg=self.text_gray, font=("Arial", 7, "bold"))
        log_label.pack(anchor=tk.W, padx=5, pady=2)

        log_scroll = tk.Scrollbar(log_frame, bg=self.bg_secondary)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text = tk.Text(log_frame, height=4, bg=self.bg_secondary,
                               fg="white", font=("Arial", 7),
                               relief=tk.FLAT, yscrollcommand=log_scroll.set,
                               state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 3))
        log_scroll.config(command=self.log_text.yview)

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

    def update_chart(self):
        """Update price chart with latest prices."""
        if not self.selected_market_live_prices or len(self.selected_market_live_prices) < 2:
            return

        # Add new data point
        now = datetime.now()
        yes_price = self.selected_market_live_prices[0]
        no_price = self.selected_market_live_prices[1]

        # Only add if prices are valid
        if yes_price is not None and no_price is not None:
            self.price_history['timestamps'].append(now)
            self.price_history['yes_prices'].append(yes_price)
            self.price_history['no_prices'].append(no_price)

            # Clear and redraw
            self.ax.clear()
            self.ax.set_facecolor('#0a0a0a')
            self.ax.set_ylim(0, 1)
            self.ax.set_ylabel('Price', color='#888888', fontsize=8)
            self.ax.grid(True, alpha=0.2, color='#888888')

            if len(self.price_history['timestamps']) > 1:
                # Plot lines
                times = list(self.price_history['timestamps'])
                yes_prices = list(self.price_history['yes_prices'])
                no_prices = list(self.price_history['no_prices'])

                self.ax.plot(times, yes_prices, color='#00ff88', linewidth=2, label='YES')
                self.ax.plot(times, no_prices, color='#ff0066', linewidth=2, label='NO')
                self.ax.legend(loc='upper left', fontsize=7, framealpha=0.3, facecolor='#0a0a0a', edgecolor='#888888')

            # Format x-axis
            self.ax.tick_params(colors='#888888', labelsize=6)
            self.ax.spines['bottom'].set_color('#888888')
            self.ax.spines['left'].set_color('#888888')
            self.ax.spines['top'].set_visible(False)
            self.ax.spines['right'].set_visible(False)

            # Rotate time labels
            self.fig.autofmt_xdate(rotation=45, ha='right')

            self.canvas.draw()

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

        query = self.search_var.get().strip()

        def _search():
            try:
                self.is_refreshing = True

                # If empty query, show all markets
                if not query:
                    self.log(f"Loading all markets...", "cyan")
                else:
                    self.log(f"Searching: {query}", "cyan")

                # Increased limit to 1000 to catch more markets
                resp = GUI_SESSION.get("https://gamma-api.polymarket.com/markets?limit=1000&closed=false", timeout=15)
                all_markets = resp.json()

                # If no query, show all
                if not query:
                    filtered = all_markets
                else:
                    # Better search: check question, description, AND tags
                    keywords = query.lower().split()
                    filtered = []

                    for market in all_markets:
                        question = market.get("question", "").lower()
                        description = market.get("description", "").lower()
                        tags = " ".join(market.get("tags", [])).lower()

                        # Combine all searchable text
                        searchable = f"{question} {description} {tags}"

                        # Check if ALL keywords are present (better than ANY)
                        # But also check if the full query is present as-is
                        full_query = query.lower()
                        if full_query in searchable or all(kw in searchable for kw in keywords):
                            filtered.append(market)

                self.markets = filtered
                self.root.after(0, self.display_markets)

                if query:
                    self.log(f"Found {len(filtered)} markets matching '{query}'", "green")
                else:
                    self.log(f"Loaded {len(filtered)} active markets", "green")

            except Exception as e:
                self.log(f"Search failed: {e}", "red")
            finally:
                self.is_refreshing = False

        threading.Thread(target=_search, daemon=True).start()

    def load_from_url(self):
        """Load market directly from Polymarket URL."""
        url = self.url_var.get().strip()

        # Remove placeholder text
        if url == "Or paste Polymarket URL...":
            self.toast("Enter a Polymarket URL first", "warning")
            return

        if not url:
            self.toast("Enter a Polymarket URL", "warning")
            return

        # Validate URL
        if "polymarket.com" not in url:
            self.toast("Invalid Polymarket URL", "error")
            return

        def _load():
            try:
                self.log(f"Loading from URL...", "cyan")

                # Extract slug from URL
                # Format: https://polymarket.com/event/slug or /market/slug
                import re
                slug_match = re.search(r'/(?:event|market)/([^/?#]+)', url)

                if not slug_match:
                    self.root.after(0, lambda: self.toast("Could not extract slug from URL", "error"))
                    self.root.after(0, lambda: self.log("URL format not recognized", "red"))
                    return

                slug = slug_match.group(1)
                self.root.after(0, lambda: self.log(f"Extracted slug: {slug}", "cyan"))

                # Try Gamma API with slug (works for both events and markets)
                api_url = f"https://gamma-api.polymarket.com/events?slug={slug}"
                self.root.after(0, lambda: self.log(f"Querying Gamma API...", "cyan"))

                resp = GUI_SESSION.get(api_url, timeout=15)

                if resp.status_code != 200:
                    self.root.after(0, lambda: self.toast(f"API returned {resp.status_code}", "error"))
                    return

                data = resp.json()

                # API returns a list of events
                if not data or not isinstance(data, list) or len(data) == 0:
                    self.root.after(0, lambda: self.toast("Event not found in API", "error"))
                    return

                event = data[0]
                markets = event.get('markets', [])

                if not markets:
                    self.root.after(0, lambda: self.toast("No markets in this event", "error"))
                    return

                # Add markets to the list and display
                self.markets = markets
                self.root.after(0, self.display_markets)
                self.root.after(0, lambda: self.toast(f"Loaded {len(markets)} market(s)!", "success"))
                self.root.after(0, lambda: self.log(f"Event: {event.get('title', 'N/A')[:60]}", "green"))

                # Auto-select first market if only one
                if len(markets) == 1:
                    self.root.after(100, lambda: self.select_market(markets[0]))

            except Exception as e:
                self.root.after(0, lambda: self.log(f"Error loading URL: {e}", "red"))
                self.root.after(0, lambda: self.toast(f"Error: {e}", "error"))
                import traceback
                traceback.print_exc()

        threading.Thread(target=_load, daemon=True).start()

    def format_volume(self, volume):
        """Format volume for display (e.g., $1.2M, $43.5K)."""
        if volume is None:
            return ""

        volume = float(volume)

        if volume >= 1_000_000:
            return f"${volume/1_000_000:.1f}M"
        elif volume >= 1_000:
            return f"${volume/1_000:.1f}K"
        else:
            return f"${volume:.0f}"

    def display_markets(self):
        """Afficher les marchés."""
        for widget in self.markets_frame.winfo_children():
            widget.destroy()

        # Sort by volume24hr (most active first)
        sorted_markets = sorted(
            self.markets,
            key=lambda m: float(m.get('volume24hr', 0) or 0),
            reverse=True
        )

        self.market_count.config(text=str(len(sorted_markets)))

        for i, market in enumerate(sorted_markets):
            question = market.get("question", "N/A")
            volume_24h = market.get("volume24hr", 0)

            market_card = tk.Frame(self.markets_frame, bg=self.bg,
                                  highlightthickness=1, highlightbackground=self.bg_secondary)
            market_card.pack(fill=tk.X, pady=2, padx=3)

            # Question text
            text = tk.Label(market_card, text=question, bg=self.bg, fg="white",
                           font=self.font_small, wraplength=250, justify=tk.LEFT,
                           cursor="hand2", anchor="w")
            text.pack(fill=tk.X, padx=5, pady=(5, 3))

            # Volume indicator
            vol_str = self.format_volume(volume_24h)
            if vol_str:
                # Color based on volume
                if volume_24h >= 10000:  # Hot market
                    vol_color = self.neon_green
                    prefix = "🔥 "
                elif volume_24h >= 1000:  # Active
                    vol_color = self.neon_cyan
                    prefix = "● "
                else:  # Low volume
                    vol_color = self.text_gray
                    prefix = "○ "

                vol_label = tk.Label(market_card, text=f"{prefix}{vol_str} 24h",
                                   bg=self.bg, fg=vol_color,
                                   font=("Arial", 6), anchor="w")
                vol_label.pack(fill=tk.X, padx=5, pady=(0, 3))

            # Bind click to entire card
            for widget in [market_card, text]:
                widget.bind("<Button-1>", lambda e, m=market: self.select_market(m))
                widget.bind("<Enter>", lambda e, w=market_card: w.config(highlightbackground=self.neon_cyan))
                widget.bind("<Leave>", lambda e, w=market_card: w.config(highlightbackground=self.bg_secondary))

    def select_market(self, market):
        """Sélectionner un marché et mettre à jour l'UI."""
        # Stop previous price refresh if any
        self.price_refresh_active = False
        self.price_refresh_counter = 0

        self.selected_market = market

        # Reset price history for new market
        self.price_history['timestamps'].clear()
        self.price_history['yes_prices'].clear()
        self.price_history['no_prices'].clear()

        question = market.get("question", "N/A")
        self.market_title_label.config(text=question, fg="white")

        # Clear outcomes
        for widget in self.outcomes_frame.winfo_children():
            widget.destroy()

        # Parse outcomes and token IDs
        outcomes = json.loads(market.get("outcomes", "[]"))
        tokens = json.loads(market.get("clobTokenIds", "[]"))

        # Show loading indicator
        loading = tk.Label(self.outcomes_frame, text="⏳ Fetching live prices...",
                          bg=self.bg, fg=self.neon_cyan, font=("Arial", 10))
        loading.pack(pady=10)

        self.log(f"Selected: {question[:60]}...", "magenta")
        print(f"\n=== MARKET SELECTED ===")
        print(f"Question: {question[:60]}")
        print(f"Tokens: {tokens[:2]}")

        # Disable buttons while loading
        self.buy_yes_btn.disable()
        self.buy_no_btn.disable()

        # Start continuous price refresh
        self.price_refresh_active = True
        self.refresh_prices_loop()

    def refresh_prices_loop(self):
        """Continuously refresh prices every 1 second."""
        if not self.price_refresh_active or not self.selected_market:
            return

        self.price_refresh_counter += 1
        print(f"\n[Refresh #{self.price_refresh_counter}] Fetching prices...")

        # Parse market data
        outcomes = json.loads(self.selected_market.get("outcomes", "[]"))
        tokens = json.loads(self.selected_market.get("clobTokenIds", "[]"))

        def _fetch():
            try:
                live_prices = []
                for i, token_id in enumerate(tokens[:2]):  # Only first 2 (YES/NO)
                    print(f"  → Fetching price for token {i} ({token_id[:20]}...)...")
                    price = self.bot.get_token_price(token_id) if self.bot else None
                    print(f"    Got: ${price:.4f}" if price else "    Got: None")
                    live_prices.append(price)

                # Update UI
                def _update_ui():
                    self.selected_market_live_prices = live_prices

                    # Update price chart
                    self.update_chart()

                    # Clear outcomes frame
                    for widget in self.outcomes_frame.winfo_children():
                        widget.destroy()

                    # Display outcomes with LIVE prices
                    for i, (outcome, price) in enumerate(zip(outcomes[:2], live_prices)):
                        if price is not None:
                            label_text = f"{outcome} - ${price:.4f} 🔴"
                            price_color = self.neon_cyan if i == 0 else self.neon_red
                        else:
                            label_text = f"{outcome} - Price N/A"
                            price_color = self.text_gray

                        tk.Label(self.outcomes_frame, text=label_text,
                                bg=self.bg, fg=price_color,
                                font=("Arial", 9, "bold")).pack(pady=3, anchor=tk.W)

                    # Update buttons with OUTCOME NAMES (not YES/NO)
                    if len(live_prices) >= 2 and all(p is not None for p in live_prices):
                        # Truncate long outcome names for buttons
                        outcome_0 = outcomes[0][:20] + "..." if len(outcomes[0]) > 20 else outcomes[0]
                        outcome_1 = outcomes[1][:20] + "..." if len(outcomes[1]) > 20 else outcomes[1]

                        self.buy_yes_btn.config(text=f"BUY {outcome_0}\n${live_prices[0]:.4f}")
                        self.buy_no_btn.config(text=f"BUY {outcome_1}\n${live_prices[1]:.4f}")
                        self.buy_yes_btn.enable()
                        self.buy_no_btn.enable()
                        print(f"[Refresh #{self.price_refresh_counter}] ✓ {outcomes[0]}: ${live_prices[0]:.4f} | {outcomes[1]}: ${live_prices[1]:.4f}")
                        # Don't log every refresh to avoid spam
                        # self.log(f"🔴 Live #{self.price_refresh_counter}: {outcomes[0]} | {outcomes[1]}", "green")

                self.root.after(0, _update_ui)

            except Exception as e:
                print(f"[Refresh #{self.price_refresh_counter}] ✗ Error: {e}")
                self.root.after(0, lambda: self.log(f"Price fetch error: {e}", "red"))

        threading.Thread(target=_fetch, daemon=True).start()

        # Schedule next refresh in 1 second
        if self.price_refresh_active:
            self.root.after(1000, self.refresh_prices_loop)

    def set_amount(self, amount):
        """Définir le montant."""
        self.amount_var.set(str(float(amount)))

    def fast_buy(self, outcome_idx):
        """Ultra-fast buy - no confirmation, minimal buffer."""
        if not self.selected_market:
            self.toast("Select a market first", "error")
            return

        try:
            amount = float(self.amount_var.get())
            if amount < 1.0:
                self.toast("Minimum: $1", "error")
                return
        except:
            self.toast("Invalid amount", "error")
            return

        # Get market data
        outcomes = json.loads(self.selected_market.get("outcomes", "[]"))
        tokens = json.loads(self.selected_market.get("clobTokenIds", "[]"))

        if outcome_idx >= len(outcomes) or outcome_idx >= len(tokens):
            self.toast("Invalid outcome", "error")
            return

        outcome = outcomes[outcome_idx]
        token_id = tokens[outcome_idx]

        # Use LIVE prices if available, otherwise fallback to API prices
        if self.selected_market_live_prices and outcome_idx < len(self.selected_market_live_prices):
            price = self.selected_market_live_prices[outcome_idx]
            if price is None:
                # Fallback to API price
                prices = json.loads(self.selected_market.get("outcomePrices", "[]"))
                price = float(prices[outcome_idx]) if outcome_idx < len(prices) else None
        else:
            # Fallback to API price
            prices = json.loads(self.selected_market.get("outcomePrices", "[]"))
            price = float(prices[outcome_idx]) if outcome_idx < len(prices) else None

        if price is None:
            self.toast("Could not get price", "error")
            return

        # Get PRICE buffer percentage (user configurable)
        try:
            price_buffer_pct = float(self.buffer_var.get())
        except:
            price_buffer_pct = 0.5  # Default to 0.5% if invalid

        # AMOUNT buffer is always 1% (hard-coded for safety - ensures we stay above $1 min)
        amount_buffer_pct = 1.0
        amount_multiplier = 1.01  # 1% buffer

        # Disable buttons during execution
        self.buy_yes_btn.disable()
        self.buy_no_btn.disable()

        # Execute in background thread
        def _buy():
            try:
                # Apply fixed 0.5% buffer to amount (safety)
                safe_amount = amount * amount_multiplier

                # Apply user-configurable buffer to price
                remaining_to_max = 0.99 - price
                price_buffer = min(price * (price_buffer_pct / 100), remaining_to_max)  # User buffer %, capped at max
                adjusted_price = min(0.99, price + price_buffer)

                # Detailed log showing all calculations
                self.root.after(0, lambda: self.log(
                    f"💰 BUY {outcome}: ${amount:.2f} → ${safe_amount:.2f} (+1%) | Price: ${price:.4f} → ${adjusted_price:.4f} (+{price_buffer_pct}%)", "cyan"
                ))

                result = self.bot.place_bet(
                    token_id=token_id,
                    side="BUY",
                    price=adjusted_price,
                    total_amount=safe_amount,
                    confirm=False
                )

                if result and result.get('success'):
                    order_id = result.get('orderID', 'N/A')[:12]
                    self.root.after(0, lambda: self.log(f"✓ BUY SUCCESS: {order_id}", "green"))
                    self.root.after(0, lambda: self.toast(f"Bought {outcome}!", "success"))
                else:
                    error = result.get('error', 'Unknown') if result else 'No response'
                    self.root.after(0, lambda: self.log(f"✗ BUY FAILED: {error}", "red"))
                    self.root.after(0, lambda: self.toast(f"Failed: {error}", "error"))

            except Exception as e:
                self.root.after(0, lambda: self.log(f"✗ ERROR: {e}", "red"))
                self.root.after(0, lambda: self.toast(f"Error: {e}", "error"))
            finally:
                self.root.after(0, self.buy_yes_btn.enable)
                self.root.after(0, self.buy_no_btn.enable)

        threading.Thread(target=_buy, daemon=True).start()


def main():
    root = tk.Tk()
    app = UltraSimplePolymarketGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
