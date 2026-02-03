# 🎮 Polymarket LoL Bot

Bot Python ultra-rapide pour parier sur des games de League of Legends (ou autre) en direct sur Polymarket.

**Interface moderne flat design avec néons cyber - Paris en 3 clics et <5 secondes.**

![Version](https://img.shields.io/badge/version-1.0.0-cyan)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## ⚡ Quick Start

1. **Clone le repo**
   ```bash
   git clone https://github.com/VOTRE_USERNAME/polyLoLv3.git
   cd polyLoLv3
   ```

2. **Installe les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure tes clés**
   ```bash
   cp .env.example .env
   # Édite .env avec tes clés Polymarket
   ```

4. **Lance l'interface**
   ```bash
   python gui_modern.py
   # Ou double-clic sur START_MODERN.bat (Windows)
   ```

## 🎨 Interface Moderne

### Design
- **Flat design épuré** - Pas de 3D, tout plat
- **Néons cyber** - Cyan `#00ffff`, Magenta `#ff00ff`, Vert `#00ff88`
- **Minimaliste** - Seulement l'essentiel
- **Futuriste** - Hover effects, animations subtiles

### Features
- 🔍 **Recherche instantanée** - Trouve n'importe quel marché
- 📊 **Liste scrollable** - Tous les marchés visibles
- ⚡ **Auto-confirm mode** - Paris sans popup (0 friction)
- 💬 **Toast notifications** - Pas de popups bloquants
- 📝 **Log coloré** - Historique en temps réel
- 💰 **Quick amounts** - Boutons 1$, 5$, 10$, 25$, 50$, 100$

### Workflow Ultra-Rapide
1. Active **"AUTO CONFIRM"** ☑
2. Clic sur marché
3. Clic sur outcome
4. Clic sur **BET NOW**

**3 clics, 0 popup, <5 secondes** 🚀

Voir [MODERN_UI_GUIDE.md](MODERN_UI_GUIDE.md) pour plus de détails.

## 🤖 Utilisation CLI

Le bot peut aussi être utilisé en ligne de commande:

```python
from bot import PolymarketLolBot

# Initialiser
bot = PolymarketLolBot()

# Rechercher des marchés
markets = bot.search_lol_markets("League of Legends")

# Parier avec montant total fixe (recommandé)
bot.place_bet(
    token_id="...",
    side="BUY",
    price=0.55,
    total_amount=1.0,  # Dépenser exactement 1$
    confirm=False
)

# Ou avec taille fixe
bot.place_bet(
    token_id="...",
    side="BUY",
    price=0.55,
    size=2.0,  # 2 shares
    confirm=False
)
```

## 📁 Structure

```
polyLoLv3/
├── bot.py              # Bot principal (classe PolymarketLolBot)
├── gui_modern.py       # Interface graphique moderne
├── START_MODERN.bat    # Lanceur Windows
├── requirements.txt    # Dépendances Python
├── .env.example        # Template de configuration
├── .env                # Tes clés (gitignored!)
├── .gitignore          # Fichiers ignorés
├── README.md           # Ce fichier
└── MODERN_UI_GUIDE.md  # Guide détaillé de l'interface
```

## 🔧 Configuration

Copie `.env.example` vers `.env` et remplis avec tes clés:

```bash
PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE
FUNDER_ADDRESS=0xYOUR_WALLET_ADDRESS_HERE
SIGNATURE_TYPE=1
CHAIN_ID=137
```

## 🚀 Avantages vs Interface Web

| Feature | Web Polymarket | Ce Bot |
|---------|----------------|--------|
| **Vitesse** | ~30s | **<5s** ⚡ |
| **Clics** | 10+ | **3** |
| **Popups** | Oui | **Non** |
| **Auto-confirm** | Non | **Oui** |
| **Recherche** | Lente | **Instantanée** |
| **Multi-marchés** | Non | **Oui** |
| **Historique** | Non | **Oui** |

**Tu es 6x plus rapide! 🎯**

## 📊 Features

- ✅ Recherche de marchés en temps réel
- ✅ Affichage des prix live
- ✅ Placement d'ordres automatique
- ✅ Calcul automatique de la taille pour montant fixe
- ✅ Interface graphique moderne
- ✅ Mode auto-confirm (sans friction)
- ✅ Toast notifications
- ✅ Log d'activité coloré
- ✅ Threading (pas de freeze)

## ⚠️ Sécurité

- 🔒 **Clés locales** - Tes clés restent dans `.env` (gitignored)
- 🔐 **Signature locale** - Ordres signés sur ta machine
- 🚫 **Pas de transmission** - Aucune clé envoyée à l'API
- ✅ **Open source** - Code 100% auditable

**Ne JAMAIS commit le fichier `.env` avec tes vraies clés!**

## 📝 License

MIT License - Utilise librement, modifie, distribue.

## 🤝 Contribution

Pull requests welcome! Pour des changements majeurs, ouvre d'abord une issue.

## ⚡ Support

Des questions? Ouvre une issue sur GitHub.

---

**Made with ⚡ by the community - Trade fast, trade smart.**
