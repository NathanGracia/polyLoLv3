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

    def search_lol_markets(self, query: str = "League of Legends", include_closed: bool = False) -> List[Dict]:
        """
        Recherche les marchés LoL disponibles.

        Args:
            query: Terme de recherche (par défaut "League of Legends")
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

            response = requests.get(url, params=params, timeout=10)
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
        try:
            url = "https://clob.polymarket.com/prices"
            params = {"token_ids": token_id}
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if token_id in data and data[token_id] is not None:
                price = float(data[token_id])
                return price if price > 0 else None
            return None
        except Exception as e:
            # Ne pas afficher l'erreur pour chaque token sans prix
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
        print(f"   Taille: {size:.2f} shares")
        print(f"   💵 Montant total: ${calculated_total:.2f}")

        # Validation taille
        if size < 1.0:
            print("❌ Taille minimale: 1.0")
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

            print(f"\n✅ PARI PLACÉ! Réponse: {response}")
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
