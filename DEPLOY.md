# 🚀 Déploiement PolyBet

## Architecture

```
Internet → HTTPS (443) → Nginx (reverse proxy) → Docker (8080) → Flask App
```

## Setup initial (une seule fois)

### 1. Sur le serveur OVH

```bash
# Cloner le repo
git clone <ton-repo> ~/polymarket-web
cd ~/polymarket-web

# Copier et configurer .env
cp .env.example .env
nano .env  # Configurer PRIVATE_KEY, WEB_USERNAME, WEB_PASSWORD

# Installer la config nginx
sudo cp nginx.conf /etc/nginx/sites-available/polybet
sudo ln -sf /etc/nginx/sites-available/polybet /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Tester et recharger nginx
sudo nginx -t
sudo systemctl reload nginx

# Rendre le script de déploiement exécutable
chmod +x deploy.sh

# Premier déploiement
./deploy.sh
```

### 2. Configurer SSL (une seule fois)

```bash
sudo certbot --nginx -d polybet.nathangracia.com
```

Après ça, Certbot aura modifié `/etc/nginx/sites-available/polybet` avec les certificats SSL.

**⚠️ IMPORTANT:** La prochaine fois que tu déploies, la config nginx sera écrasée par `nginx.conf` du repo.
Donc après le premier `certbot`, récupère la config complète :

```bash
# Copier la config modifiée par Certbot dans le repo local
sudo cat /etc/nginx/sites-available/polybet > ~/polymarket-web/nginx.conf
cd ~/polymarket-web
git add nginx.conf
git commit -m "Update nginx config with SSL from Certbot"
git push
```

Puis en local, fais un `git pull` pour récupérer la config avec SSL.

## Déploiement (après chaque changement)

### En local (Windows)

```bash
# Modifier ton code
# Commit et push
git add .
git commit -m "Update: description"
git push
```

### Sur le serveur (OVH)

```bash
cd ~/polymarket-web
./deploy.sh
```

C'est tout ! 🎉

## Commandes utiles

```bash
# Voir les logs en temps réel
sudo docker-compose logs -f

# Redémarrer l'app
sudo docker-compose restart

# Voir le statut
sudo docker-compose ps

# Tester nginx
sudo nginx -t

# Recharger nginx sans downtime
sudo systemctl reload nginx

# Voir les certificats SSL
sudo certbot certificates

# Renouveler SSL manuellement (auto tous les 90j)
sudo certbot renew
```

## Troubleshooting

### 502 Bad Gateway
```bash
# Vérifier que Docker tourne
sudo docker-compose ps

# Voir les logs
sudo docker-compose logs

# Vérifier le port
curl http://localhost:8080
```

### 404 Not Found
```bash
# Vérifier la config nginx
cat /etc/nginx/sites-available/polybet

# Tester la config
sudo nginx -t

# Recharger
sudo systemctl reload nginx
```

### Container ne démarre pas
```bash
# Voir les logs complets
sudo docker-compose logs

# Rebuild from scratch
sudo docker-compose down
sudo docker-compose build --no-cache
sudo docker-compose up -d
```

## Variables d'environnement (.env)

```bash
# Polymarket API
PRIVATE_KEY=0x...
FUNDER_ADDRESS=0x...

# App web
WEB_USERNAME=admin
WEB_PASSWORD=ton-password-securise
SECRET_KEY=ton-secret-key-random
```

**⚠️ Ne jamais commit .env sur git !**

## 🌐 Accès

**Production:** https://polybet.nathangracia.com
