import os
import sys
import time
from typing import List, Dict, Optional
import requests
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON
from py_clob_client.clob_types import OrderArgs
import dataclasses

# Fix Windows encoding for emojis
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()


class PolymarketLolBot:
    """Bot pour parier rapidement sur des games LoL via Polymarket."""

    def __init__(self):
        """Initialize le bot avec les credentials depuis .env"""
        self.pk = os.getenv("PRIVATE_KEY").strip().replace('"', '')
        self.funder = os.getenv("FUNDER_ADDRESS")

        # Setup proxy if configured
        proxy_http = os.getenv("PROXY_HTTP", "").strip()
        proxy_https = os.getenv("PROXY_HTTPS", "").strip()

        self.proxies = None
        if proxy_http or proxy_https:
            self.proxies = {}
            if proxy_http:
                self.proxies['http'] = proxy_http
            if proxy_https:
                self.proxies['https'] = proxy_https

            # Set system environment variables so py-clob-client uses proxy too
            os.environ['HTTP_PROXY'] = proxy_http
            os.environ['HTTPS_PROXY'] = proxy_https
            os.environ['http_proxy'] = proxy_http  # lowercase for compatibility
            os.environ['https_proxy'] = proxy_https

            print(f"🌐 Proxy configured: {proxy_https or proxy_http}")
            print(f"   → System proxy env vars set for py-clob-client")
        else:
            print("🌐 No proxy - direct connection")

        # Create requests session with proxy
        self.session = requests.Session()
        if self.proxies:
            self.session.proxies.update(self.proxies)

        print("🚀 Initialisation du bot LoL Polymarket...")
        self.client = ClobClient(
            host="https://clob.polymarket.com",
            key=self.pk,
            chain_id=POLYGON,
            funder=self.funder,
            signature_type=1
        )

        # Authentification
        self.client.set_api_creds(self.client.create_or_derive_api_creds())
        print("✅ Bot connecté et authentifié\n")


    def search_lol_markets(self, query: str = "Jesus", include_closed: bool = False) -> List[Dict]:
        """
        Recherche les marchés LoL disponibles.

        Args:
            query: Terme de recherche (par défaut "Jesus")
            include_closed: Inclure les marchés fermés (défaut: False)

        Returns:
            Liste des marchés trouvés
        """
        print(f"🔍 Recherche de marchés: '{query}'...")

        try:
            # API Gamma (meilleures données)
            url = "https://gamma-api.polymarket.com/markets"
            params = {
                "limit": 200,
                "closed": "true" if include_closed else "false"
            }

            response = self.session.get(url, params=params, timeout=10)
            markets = response.json()

            # Filtrer les marchés LoL/esports
            keywords = query.lower().split()
            lol_markets = []

            for market in markets:
                question = market.get("question", "").lower()
                description = market.get("description", "").lower()
                tags = [t.lower() for t in market.get("tags", [])]

                # Chercher dans question, description, ou tags
                for keyword in keywords:
                    if (keyword in question or
                        keyword in description or
                        any(keyword in tag for tag in tags)):
                        lol_markets.append(market)
                        break

            print(f"📊 {len(lol_markets)} marchés trouvés\n")
            return lol_markets

        except Exception as e:
            print(f"❌ Erreur recherche: {e}")
            import traceback
            traceback.print_exc()
            return []

    def display_market(self, market: Dict):
        """Affiche les informations d'un marché de façon lisible."""
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"📌 {market.get('question', 'N/A')}")
        print(f"🔗 ID: {market.get('condition_id', 'N/A')}")

        # Statut
        closed = market.get("closed", False)
        active = market.get("active", True)
        status = "🔴 Fermé" if closed else "🟢 Actif" if active else "🟡 Inactif"
        print(f"📊 Statut: {status}")

        # Afficher les outcomes (YES/NO ou équipes)
        outcomes = market.get("outcomes", [])
        tokens = market.get("tokens", [])

        for i, outcome in enumerate(outcomes):
            if i < len(tokens):
                token_id = tokens[i].get("token_id", "N/A")
                # Récupérer le prix en temps réel
                price = self.get_token_price(token_id)
                if price is not None:
                    print(f"  • {outcome}: ${price:.3f} (Token: {token_id[:20]}...)")
                else:
                    print(f"  • {outcome}: Prix N/A (Token: {token_id[:20]}...)")

        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    def get_token_price(self, token_id: str) -> Optional[float]:
        """Récupère le prix actuel d'un token."""
        if not token_id:
            print("❌ No token_id provided")
            return None

        # Method 1: Try simplified prices endpoint
        try:
            # The correct format is /prices?token_id=XXX (singular, not plural)
            url = f"https://clob.polymarket.com/prices?token_id={token_id}"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and token_id in data:
                    price = float(data[token_id])
                    if price > 0:
                        return price
        except Exception as e:
            print(f"⚠️  Method 1 (prices endpoint) failed: {e}")

        # Method 2: Try using py-clob-client's built-in method
        try:
            if hasattr(self.client, 'get_last_trade_price'):
                result = self.client.get_last_trade_price(token_id)
                if result:
                    # Can be a dict, float, or string
                    if isinstance(result, dict):
                        # Try common dict keys
                        price = result.get('price') or result.get('last_price') or result.get('last')
                        if price:
                            price = float(price)
                            if price > 0:
                                print(f"✓ Got price from last trade: ${price:.4f}")
                                return price
                    else:
                        price = float(result)
                        if price > 0:
                            print(f"✓ Got price from last trade: ${price:.4f}")
                            return price
        except Exception as e:
            print(f"⚠️  Method 2 (last trade) failed: {e}")

        # Method 3: Try order book
        try:
            if hasattr(self.client, 'get_order_book'):
                book = self.client.get_order_book(token_id)
                if book:
                    # OrderBookSummary object has attributes, not dict keys
                    best_bid = None
                    best_ask = None

                    # Try attribute access first (OrderBookSummary object)
                    if hasattr(book, 'bids') and book.bids and len(book.bids) > 0:
                        bid_item = book.bids[0]
                        if hasattr(bid_item, 'price'):
                            best_bid = float(bid_item.price)
                        elif isinstance(bid_item, dict):
                            best_bid = float(bid_item['price'])

                    if hasattr(book, 'asks') and book.asks and len(book.asks) > 0:
                        ask_item = book.asks[0]
                        if hasattr(ask_item, 'price'):
                            best_ask = float(ask_item.price)
                        elif isinstance(ask_item, dict):
                            best_ask = float(ask_item['price'])

                    if best_bid and best_ask:
                        mid_price = (best_bid + best_ask) / 2
                        print(f"✓ Got mid price from order book: ${mid_price:.4f}")
                        return mid_price
                    elif best_bid:
                        print(f"✓ Got bid price from order book: ${best_bid:.4f}")
                        return best_bid
                    elif best_ask:
                        print(f"✓ Got ask price from order book: ${best_ask:.4f}")
                        return best_ask
        except Exception as e:
            print(f"⚠️  Method 3 (order book) failed: {e}")

        # Method 4: Try Gamma API (market data) - Most reliable for active markets
        try:
            print(f"🔍 Trying Gamma API for token {token_id[:20]}...")
            gamma_url = "https://gamma-api.polymarket.com/markets?limit=500&closed=false"
            response = self.session.get(gamma_url, timeout=15)

            if response.status_code == 200:
                markets = response.json()
                print(f"   Searching through {len(markets)} active markets...")

                for market in markets:
                    # Try clobTokenIds first (newer format)
                    clob_token_ids = market.get('clobTokenIds', [])
                    if clob_token_ids:
                        # Parse JSON string if needed
                        if isinstance(clob_token_ids, str):
                            import json
                            clob_token_ids = json.loads(clob_token_ids)

                        for i, clob_token_id in enumerate(clob_token_ids):
                            if clob_token_id == token_id:
                                # Found it! Get price from outcomePrices
                                outcome_prices = market.get('outcomePrices')
                                if isinstance(outcome_prices, str):
                                    import json
                                    outcome_prices = json.loads(outcome_prices)

                                if outcome_prices and i < len(outcome_prices):
                                    price = float(outcome_prices[i])
                                    if price > 0:
                                        market_name = market.get('question', 'Unknown')[:50]
                                        print(f"✓ Got price from Gamma API: ${price:.4f} (market: {market_name}...)")
                                        return price

                    # Fallback: try old tokens format
                    tokens = market.get('tokens', [])
                    for i, token in enumerate(tokens):
                        token_id_field = token.get('token_id') if isinstance(token, dict) else None
                        if token_id_field == token_id:
                            outcome_prices = market.get('outcomePrices')
                            if isinstance(outcome_prices, str):
                                import json
                                outcome_prices = json.loads(outcome_prices)

                            if outcome_prices and i < len(outcome_prices):
                                price = float(outcome_prices[i])
                                if price > 0:
                                    market_name = market.get('question', 'Unknown')[:50]
                                    print(f"✓ Got price from Gamma API (legacy): ${price:.4f} (market: {market_name}...)")
                                    return price

                print(f"   Token not found in {len(markets)} active markets")
            else:
                print(f"   Gamma API returned status {response.status_code}")
        except Exception as e:
            print(f"⚠️  Method 4 (Gamma API) failed: {e}")
            import traceback
            traceback.print_exc()

        print(f"❌ All 4 methods failed for token {token_id[:20]}...")
        return None

    def place_bet(
        self,
        token_id: str,
        side: str,
        price: float,
        size: float = None,
        total_amount: float = None,
        confirm: bool = True
    ) -> Optional[Dict]:
        """
        Place un pari rapidement.

        Args:
            token_id: ID du token (outcome)
            side: "BUY" ou "SELL"
            price: Prix (entre 0.01 et 0.99)
            size: Taille en USD (optionnel si total_amount fourni)
            total_amount: Montant total à dépenser (calcule size auto)
            confirm: Demander confirmation avant d'envoyer

        Returns:
            Réponse de l'API ou None si échec

        Note:
            - Si total_amount est fourni, size est calculé automatiquement
            - Sinon, utilise size (ajusté si total < $1)
        """
        # Validation prix
        if not (0.01 <= price <= 0.99):
            print("❌ Prix doit être entre 0.01 et 0.99")
            return None

        # Calculer size à partir de total_amount si fourni
        if total_amount is not None:
            size = total_amount / price
            print(f"\n💡 Calcul automatique: Pour dépenser ${total_amount:.2f} à ${price:.4f}")
            print(f"   → Taille calculée: {size:.2f} shares")

        elif size is None:
            print("❌ Vous devez fournir soit 'size' soit 'total_amount'")
            return None

        # Calculer le montant total
        calculated_total = price * size

        # Pour un ordre marketable, le montant total doit être >= $1
        min_total = 1.0
        if calculated_total < min_total:
            size = min_total / price
            calculated_total = price * size
            print(f"\n⚠️  Ajusté pour respecter le minimum de $1")

        print(f"\n💰 Préparation du pari:")
        print(f"   Token: {token_id[:30]}...")
        print(f"   Side: {side}")
        print(f"   Prix: ${price:.4f}")
        print(f"   Taille: {size:.4f} shares")
        print(f"   💵 Montant total: ${calculated_total:.2f}")

        # Validation: montant total minimum
        if calculated_total < min_total:
            print(f"❌ Montant total minimum: ${min_total}")
            return None

        if confirm:
            confirmation = input("\n⚠️  Confirmer le pari? (y/n): ")
            if confirmation.lower() != 'y':
                print("❌ Pari annulé")
                return None

        try:
            # Créer l'ordre
            args = OrderArgs(
                price=price,
                size=size,
                token_id=token_id,
                side=side.upper()
            )

            print("🛠️  Création de l'ordre signé...")
            signed_order = self.client.create_order(args)

            print("🚀 Envoi de l'ordre...")
            # Gestion du bug SDK (attribut vs dict)
            try:
                response = self.client.post_order(signed_order)
            except AttributeError:
                as_dict = dataclasses.asdict(signed_order) if not isinstance(signed_order, dict) else signed_order
                response = self.client.post_order(as_dict)

            # Debug: afficher la réponse complète
            print(f"\n📋 Réponse API complète: {response}")

            if response and response.get('success'):
                print(f"✅ PARI PLACÉ!")
            else:
                error_msg = response.get('error', response.get('errorMsg', 'Unknown error')) if response else 'No response'
                print(f"⚠️  ATTENTION: {error_msg}")

            print(f"🔗 Vérifie ton compte: https://polymarket.com/\n")
            return response

        except Exception as e:
            print(f"❌ Erreur placement: {e}")
            return None

    def quick_bet_on_team(
        self,
        market: Dict,
        team_name: str,
        size: float = 1.1,
        confirm: bool = True
    ) -> Optional[Dict]:
        """
        Parie rapidement sur une équipe dans un marché.

        Args:
            market: Dictionnaire du marché
            team_name: Nom de l'équipe (cherche dans outcomes)
            size: Montant en USD
            confirm: Demander confirmation
        """
        outcomes = market.get("outcomes", [])
        tokens = market.get("tokens", [])

        # Chercher l'équipe
        for i, outcome in enumerate(outcomes):
            if team_name.lower() in outcome.lower():
                token_id = tokens[i].get("token_id")
                current_price = self.get_token_price(token_id)

                if current_price:
                    print(f"🎯 {outcome}: Prix actuel ${current_price}")
                    # Acheter au meilleur prix disponible
                    return self.place_bet(
                        token_id=token_id,
                        side="BUY",
                        price=min(current_price + 0.01, 0.99),  # Légèrement au-dessus
                        size=size,
                        confirm=confirm
                    )

        print(f"❌ Équipe '{team_name}' non trouvée dans le marché")
        return None

    def get_user_positions(self, market_id: Optional[str] = None) -> List[Dict]:
        """
        Get user's current positions from Polymarket API.

        Args:
            market_id: Optional market ID to filter positions

        Returns:
            List of dicts with: token_id, market_id, outcome, net_size,
            avg_entry_price, current_price, unrealized_pnl, unrealized_roi
        """
        try:
            # Get user's open orders and trades
            # Note: ClobClient may have get_orders() or similar methods
            # We'll use the API directly if needed

            # Try to get orders from the client
            try:
                # Attempt to get open orders (may vary by SDK version)
                orders = self.client.get_orders()
            except AttributeError:
                # Fallback: use API directly
                try:
                    url = "https://clob.polymarket.com/orders"
                    headers = {
                        "Authorization": f"Bearer {self.client.creds.api_key}" if hasattr(self.client, 'creds') else ""
                    }
                    response = requests.get(url, headers=headers, timeout=10)
                    orders = response.json() if response.status_code == 200 else []
                except Exception:
                    orders = []

            # Aggregate positions by token_id
            positions_map = {}

            for order in orders:
                if not isinstance(order, dict):
                    continue

                # Skip if filtering by market and this order doesn't match
                order_market_id = order.get('market', order.get('condition_id'))
                if market_id and order_market_id != market_id:
                    continue

                token_id = order.get('asset_id', order.get('token_id'))
                if not token_id:
                    continue

                side = order.get('side', 'BUY').upper()
                size = float(order.get('size', 0))
                price = float(order.get('price', 0))
                status = order.get('status', '')

                # Only count filled orders
                if status.lower() not in ['filled', 'matched', 'active']:
                    continue

                if token_id not in positions_map:
                    positions_map[token_id] = {
                        'token_id': token_id,
                        'market_id': order_market_id,
                        'outcome': order.get('outcome', 'Unknown'),
                        'buy_size': 0.0,
                        'buy_cost': 0.0,
                        'sell_size': 0.0,
                        'sell_revenue': 0.0
                    }

                pos = positions_map[token_id]
                if side == 'BUY':
                    pos['buy_size'] += size
                    pos['buy_cost'] += size * price
                elif side == 'SELL':
                    pos['sell_size'] += size
                    pos['sell_revenue'] += size * price

            # Calculate net positions and P&L
            positions = []
            for token_id, pos in positions_map.items():
                net_size = pos['buy_size'] - pos['sell_size']

                # Skip closed positions
                if abs(net_size) < 0.01:
                    continue

                # Calculate average entry price
                if net_size > 0:
                    # Net long position
                    avg_entry_price = pos['buy_cost'] / pos['buy_size'] if pos['buy_size'] > 0 else 0
                else:
                    # Net short position
                    avg_entry_price = pos['sell_revenue'] / pos['sell_size'] if pos['sell_size'] > 0 else 0

                # Get current price
                current_price = self.get_token_price(token_id)
                if current_price is None:
                    current_price = avg_entry_price

                # Calculate unrealized P&L
                if net_size > 0:
                    # Long position: profit if price went up
                    unrealized_pnl = net_size * (current_price - avg_entry_price)
                else:
                    # Short position: profit if price went down
                    unrealized_pnl = abs(net_size) * (avg_entry_price - current_price)

                # Calculate ROI
                cost_basis = abs(net_size) * avg_entry_price
                unrealized_roi = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0

                positions.append({
                    'token_id': token_id,
                    'market_id': pos['market_id'],
                    'outcome': pos['outcome'],
                    'net_size': net_size,
                    'avg_entry_price': avg_entry_price,
                    'current_price': current_price,
                    'unrealized_pnl': unrealized_pnl,
                    'unrealized_roi': unrealized_roi
                })

            return positions

        except Exception as e:
            print(f"⚠️  Error fetching positions: {e}")
            return []

    def monitor_markets(self, interval: int = 10):
        """
        Surveille les marchés LoL en temps réel.

        Args:
            interval: Intervalle de rafraîchissement en secondes
        """
        print(f"👀 Surveillance des marchés LoL (refresh toutes les {interval}s)")
        print("   Appuyez sur Ctrl+C pour arrêter\n")

        try:
            while True:
                markets = self.search_lol_markets()

                for i, market in enumerate(markets[:5], 1):  # Top 5
                    print(f"\n[{i}] {market.get('question', 'N/A')}")
                    tokens = market.get("tokens", [])
                    outcomes = market.get("outcomes", [])

                    for j, outcome in enumerate(outcomes):
                        if j < len(tokens):
                            token_id = tokens[j].get("token_id")
                            price = self.get_token_price(token_id)
                            if price:
                                print(f"    • {outcome}: ${price:.3f}")

                print(f"\n⏳ Prochain refresh dans {interval}s...")
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n👋 Arrêt de la surveillance")


def demo_interactive():
    """Mode interactif pour tester le bot."""
    bot = PolymarketLolBot()

    while True:
        print("\n" + "="*50)
        print("🎮 BOT POLYMARKET LOL - Menu Principal")
        print("="*50)
        print("1. Rechercher des marchés LoL")
        print("2. Surveiller les marchés en temps réel")
        print("3. Placer un pari manuel")
        print("4. Quitter")

        choice = input("\nChoix: ")

        if choice == "1":
            markets = bot.search_lol_markets()
            for i, market in enumerate(markets, 1):
                print(f"\n[{i}]")
                bot.display_market(market)

                if i >= 10:  # Limite à 10 pour lisibilité
                    if input("Voir plus? (y/n): ").lower() != 'y':
                        break

        elif choice == "2":
            interval = input("Intervalle de refresh (secondes, défaut=10): ")
            interval = int(interval) if interval.isdigit() else 10
            bot.monitor_markets(interval)

        elif choice == "3":
            token_id = input("Token ID: ")
            side = input("BUY ou SELL: ").upper()
            price = float(input("Prix (0.01-0.99): "))
            size = float(input("Montant ($, min 1.1): "))

            bot.place_bet(token_id, side, price, size)

        elif choice == "4":
            print("👋 Au revoir!")
            break


if __name__ == "__main__":
    # Décommenter selon le mode souhaité:

    # Mode interactif
    demo_interactive()

    # Ou test rapide:
    # bot = PolymarketLolBot()
    # markets = bot.search_lol_markets()
    # if markets:
    #     bot.display_market(markets[0])
