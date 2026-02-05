"""
🌐 POLYMARKET WEB - Ultra Fast Trading (VPS Version)
Flask backend with neon UI
"""

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_cors import CORS
from functools import wraps
import os
from bot import PolymarketLolBot
from dotenv import load_dotenv
import threading
import time

load_dotenv()

app = Flask(__name__)
CORS(app)

# Secret key for sessions (change this to a random string!)
app.secret_key = os.getenv('SECRET_KEY', 'change-this-to-random-secret-key-in-production')

# Login credentials from .env
USERNAME = os.getenv('WEB_USERNAME', 'admin')
PASSWORD = os.getenv('WEB_PASSWORD', 'changeme')

# Global bot instance
bot = None
bot_lock = threading.Lock()

def get_bot():
    """Get or create bot instance (thread-safe)"""
    global bot
    with bot_lock:
        if bot is None:
            bot = PolymarketLolBot()
        return bot

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Main page - requires login"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        data = request.json
        username = data.get('username', '')
        password = data.get('password', '')

        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/api/markets', methods=['GET'])
@login_required
def get_markets():
    """Search markets"""
    try:
        import json as json_lib

        query = request.args.get('query', '')
        bot = get_bot()
        markets = bot.search_lol_markets(query, include_closed=False)

        # Filter active markets
        active = [m for m in markets if not m.get('closed', False)]

        # Normalize market data - ensure tokens field is properly formatted
        for market in active:
            # Try clobTokenIds first (newer format)
            if 'clobTokenIds' in market and not market.get('tokens'):
                clob_ids = market['clobTokenIds']
                # Parse if it's a JSON string
                if isinstance(clob_ids, str):
                    clob_ids = json_lib.loads(clob_ids)
                # Convert to tokens format
                market['tokens'] = clob_ids

            # Ensure tokens is parsed if it's a string
            elif 'tokens' in market and isinstance(market['tokens'], str):
                market['tokens'] = json_lib.loads(market['tokens'])

            # Ensure outcomes is parsed if it's a string
            if 'outcomes' in market and isinstance(market['outcomes'], str):
                market['outcomes'] = json_lib.loads(market['outcomes'])

            # Ensure outcomePrices is parsed if it's a string
            if 'outcomePrices' in market and isinstance(market['outcomePrices'], str):
                market['outcomePrices'] = json_lib.loads(market['outcomePrices'])

        return jsonify({
            'success': True,
            'markets': active[:50]  # Limit to 50
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/price/<token_id>', methods=['GET'])
@login_required
def get_price(token_id):
    """Get token price"""
    try:
        bot = get_bot()
        price = bot.get_token_price(token_id)

        return jsonify({
            'success': True,
            'price': price
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/bet', methods=['POST'])
@login_required
def place_bet():
    """Place a bet"""
    try:
        data = request.json

        token_id = data.get('token_id')
        side = data.get('side', 'BUY')
        price = float(data.get('price'))
        amount = float(data.get('amount'))

        # Price buffer (1% on amount, configurable% on price)
        price_buffer_pct = float(data.get('price_buffer', 0.5))
        amount_multiplier = 1.01  # Fixed 1% on amount

        safe_amount = amount * amount_multiplier

        # Apply price buffer
        remaining_to_max = 0.99 - price
        price_buffer = min(price * (price_buffer_pct / 100), remaining_to_max)
        adjusted_price = min(0.99, price + price_buffer)

        bot = get_bot()
        result = bot.place_bet(
            token_id=token_id,
            side=side,
            price=adjusted_price,
            total_amount=safe_amount,
            confirm=False
        )

        if result and result.get('success'):
            return jsonify({
                'success': True,
                'order_id': result.get('orderID', 'N/A'),
                'amount': safe_amount,
                'price': adjusted_price
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error')
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/load-url', methods=['POST'])
@login_required
def load_url():
    """Load market from Polymarket URL"""
    try:
        import re
        import requests

        data = request.json
        url = data.get('url', '').strip()

        if not url:
            return jsonify({
                'success': False,
                'error': 'URL is required'
            }), 400

        # Extract slug from URL
        slug_match = re.search(r'(?:event|market)/([^/?#]+)', url)

        if not slug_match:
            return jsonify({
                'success': False,
                'error': 'Invalid Polymarket URL'
            }), 400

        slug = slug_match.group(1)

        # Query Gamma API
        api_url = f"https://gamma-api.polymarket.com/events?slug={slug}"
        resp = requests.get(api_url, timeout=15)

        if resp.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'API returned {resp.status_code}'
            }), 400

        events = resp.json()

        if not events or len(events) == 0:
            return jsonify({
                'success': False,
                'error': 'Event not found'
            }), 404

        event = events[0]
        markets = event.get('markets', [])

        if not markets:
            return jsonify({
                'success': False,
                'error': 'No markets in this event'
            }), 404

        # Normalize market data - ensure tokens field is properly formatted
        import json as json_lib
        for market in markets:
            # Try clobTokenIds first (newer format)
            if 'clobTokenIds' in market and not market.get('tokens'):
                clob_ids = market['clobTokenIds']
                # Parse if it's a JSON string
                if isinstance(clob_ids, str):
                    clob_ids = json_lib.loads(clob_ids)
                # Convert to tokens format
                market['tokens'] = clob_ids

            # Ensure tokens is parsed if it's a string
            elif 'tokens' in market and isinstance(market['tokens'], str):
                market['tokens'] = json_lib.loads(market['tokens'])

            # Ensure outcomes is parsed if it's a string
            if 'outcomes' in market and isinstance(market['outcomes'], str):
                market['outcomes'] = json_lib.loads(market['outcomes'])

            # Ensure outcomePrices is parsed if it's a string
            if 'outcomePrices' in market and isinstance(market['outcomePrices'], str):
                market['outcomePrices'] = json_lib.loads(market['outcomePrices'])

        return jsonify({
            'success': True,
            'markets': markets
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'success': True,
        'status': 'online',
        'proxy': os.getenv('PROXY_HTTP', 'none')
    })

if __name__ == '__main__':
    print("🌐 Starting Polymarket Web App...")
    print("🇦🇹 Running from VPS (no geo restrictions)")
    print("⚡ Access at: http://0.0.0.0:5000")

    app.run(host='0.0.0.0', port=5000, debug=False)
