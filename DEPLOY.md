# 🚀 Déploiement Web App sur VPS

## 📦 Préparation

**Sur ton PC, créer un zip avec:**

```bash
# Aller dans le dossier
cd C:\Users\natha\Documents\polyLoLv3

# Créer un dossier deploy
mkdir deploy
cp web_app.py deploy/
cp bot.py deploy/
cp requirements.txt deploy/
cp Dockerfile deploy/
cp docker-compose.yml deploy/
cp -r templates deploy/
cp .env deploy/
```

## 🌐 Upload sur VPS

**1. Transférer sur VPS (depuis PowerShell):**

```powershell
scp -r deploy ubuntu@141.227.165.46:~/polymarket-web
```

**2. SSH vers VPS:**

```bash
ssh ubuntu@141.227.165.46
```

## 🐳 Installation Docker sur VPS

```bash
# Update
sudo apt update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose -y

# Add user to docker group
sudo usermod -aG docker $USER
```

**Déconnecte et reconnecte SSH pour appliquer les permissions**

## 🚀 Lancer l'application

```bash
# Aller dans le dossier
cd ~/polymarket-web

# Construire et lancer
docker-compose up -d

# Voir les logs
docker-compose logs -f
```

## 🌍 Accès

**Ouvre dans ton navigateur:**

```
http://141.227.165.46:5000
```

## 🛠️ Commandes utiles

```bash
# Stopper
docker-compose down

# Redémarrer
docker-compose restart

# Voir les logs en temps réel
docker-compose logs -f

# Rebuild après modification
docker-compose up -d --build
```

## 🔥 Ouvrir le port firewall

Si tu ne peux pas accéder, ouvre le port:

```bash
sudo ufw allow 5000/tcp
```

## ✅ Test rapide

```bash
# Depuis ton PC
curl http://141.227.165.46:5000/api/health
```

Tu devrais voir: `{"success":true,"status":"online"}`

## 🎯 C'est prêt!

Accède à: **http://141.227.165.46:5000**

Design neon + Trading ultra rapide depuis l'Autriche! 🇦🇹⚡
