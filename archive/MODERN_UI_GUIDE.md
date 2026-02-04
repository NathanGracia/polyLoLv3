# 🎮 POLYMARKET BOT - MODERN UI

Interface futuriste flat design avec néons cyber.

## 🚀 Lancement

**Double-clic sur `START_MODERN.bat`**

ou:
```bash
python gui_modern.py
```

## 🎨 Design

### Couleurs Néon
- **Cyan** `#00ffff` - Accents primaires, recherche
- **Magenta** `#ff00ff` - Headers, refresh
- **Vert néon** `#00ff88` - Succès, bouton BET
- **Rouge néon** `#ff0066` - Erreurs
- **Fond noir** `#0a0a0a` - Fond principal

### Flat Design
- Pas de bordures 3D
- Pas d'ombres
- Lignes fines néon
- Effets hover subtils

## ⚡ Vitesse Maximale

### Mode Auto-Confirm (RECOMMANDÉ)
1. Coche **"AUTO CONFIRM (NO POPUP)"**
2. Sélectionne marché + outcome
3. Clic sur **BET NOW**
4. **DONE** - Pari placé instantanément!

**3 clics, 0 popup, <5 secondes** ⚡

### Mode Normal (avec confirmation)
- Décoche "AUTO CONFIRM"
- Petite fenêtre de confirmation moderne (pas de popup bloquant)
- Boutons CONFIRM/CANCEL

## 🎯 Interface

### Left Panel - Markets
```
MARKETS [42]
┌──────────────────────────────────────┐
│ [League of Legends___] [SEARCH] [↻] │
├──────────────────────────────────────┤
│ 1. Will T1 win Worlds 2025?         │ ← Hover: Cyan
│ 2. Fnatic vs G2 - Who wins?         │
│ 3. ...                               │
└──────────────────────────────────────┘
```

### Right Panel - Bet
```
PLACE BET

Selected Market Title

OUTCOMES
┌────────────────────────────┐
│ Yes: $0.4850              │ ← Clic pour sélectionner
│ No: $0.5150               │   (border cyan quand sélectionné)
└────────────────────────────┘

AMOUNT
┌────────────────┐
│ $ [1.0________]│
└────────────────┘
[1] [5] [10] [25] [50] [100]

☑ AUTO CONFIRM (NO POPUP)

╔══════════════════════╗
║                      ║
║      BET NOW         ║ ← Gros bouton vert néon
║                      ║   Hover: Cyan
╚══════════════════════╝

ACTIVITY LOG
[14:23:05] Searching: LoL
[14:23:06] Found 5 markets
[14:23:10] Selected: T1 vs G2...
[14:23:12] Placing bet...
[14:23:14] ✓ BET PLACED: 0x7985...
```

## 📱 Toast Notifications

Au lieu de popups bloquants, petites notifications en bas à droite:

```
┌─────────────────────────┐
│ ✓ Bet placed! 0x7985... │ ← Auto-dismiss après 3s
└─────────────────────────┘
```

Types:
- **Success** (vert) - Pari placé
- **Error** (rouge) - Erreur
- **Warning** (orange) - Attention
- **Info** (cyan) - Information

## 🔧 Fonctionnalités

### Recherche
- Tape n'importe quoi
- Enter ou clic SEARCH
- Résultats instantanés
- Compteur de marchés

### Sélection
- Clic sur marché → Affiche outcomes
- Clic sur outcome → Sélectionné (border cyan)
- Bouton BET activé

### Montants rapides
- Boutons 1, 5, 10, 25, 50, 100
- Clic = montant défini
- Ou tape manuellement

### Auto-confirm
- Checkbox en haut du panel bet
- ☑ = Pas de confirmation du tout
- ☐ = Confirmation minimale moderne

### Log coloré
- Cyan = Actions
- Vert = Succès
- Rouge = Erreurs
- Magenta = Sélections

## ⌨️ Raccourcis

- `Enter` dans search → Rechercher
- `Clic` marché → Sélectionner
- `Clic` outcome → Choisir
- `Clic` BET NOW → Parier
- `Espace` sur checkbox → Toggle auto-confirm

## 💡 Tips

### Vitesse maximale
1. Active AUTO CONFIRM
2. Pré-sélectionne le montant
3. Clic marché → Clic outcome → Clic BET
4. **3 clics = pari placé**

### Multi-paris rapides
- Laisse la fenêtre ouverte
- Après un pari, sélectionne direct un autre marché
- Pas besoin de refresh ou reload

### Surveillance
- Laisse tourner en fond
- Clic refresh régulièrement
- Log montre tout l'historique

## 🎨 Customisation

Pour changer les couleurs, édite `gui_modern.py`:

```python
# Colors
self.neon_cyan = "#00ffff"      # Cyan
self.neon_magenta = "#ff00ff"   # Magenta
self.neon_green = "#00ff88"     # Vert
self.neon_red = "#ff0066"       # Rouge
```

## ⚡ Performances

- **Threading** - Pas de freeze
- **Async** - Toutes les API calls en background
- **Responsive** - Scroll fluide
- **Light** - Pure tkinter, pas de dépendances lourdes

---

## 📊 Comparaison

| Feature | Web UI | Old GUI | Modern UI |
|---------|--------|---------|-----------|
| **Design** | Old | 3D | Flat Neon |
| **Popups** | Oui | Oui | Non |
| **Auto-confirm** | Non | Non | ✅ Oui |
| **Speed** | ~30s | ~10s | **~5s** |
| **Toast** | Non | Non | ✅ Oui |
| **Couleurs** | Basique | Sombre | **Néon** |

---

**L'interface la plus rapide pour parier sur Polymarket! 🚀**
