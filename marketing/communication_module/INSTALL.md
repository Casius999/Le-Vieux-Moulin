# Guide d'Installation et de Déploiement

Ce document détaille les étapes pour installer, configurer et déployer le module de communication et d'automatisation marketing du système "Le Vieux Moulin".

## Prérequis

### Système
- Python 3.9 ou supérieur
- PostgreSQL 12 ou supérieur
- Redis 6 ou supérieur
- RabbitMQ 3.8 ou supérieur
- Accès réseau pour les API externes (Facebook, Instagram, etc.)

### Comptes et Accès
- Comptes développeur pour les plateformes de réseaux sociaux (Facebook, Instagram, Twitter)
- Compte d'envoi d'emails (SendGrid, Mailjet ou configuration SMTP)
- Compte d'envoi de SMS (Twilio, OVH)
- Accès API aux autres modules du système (CRM, recettes, etc.)

## Installation

### 1. Préparation de l'Environnement

```bash
# Cloner le dépôt (si ce n'est pas déjà fait)
git clone https://github.com/Casius999/Le-Vieux-Moulin.git
cd Le-Vieux-Moulin/marketing/communication_module

# Créer un environnement virtuel Python
python -m venv venv

# Activer l'environnement virtuel
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt
```

### 2. Configuration de la Base de Données

```bash
# Se connecter à PostgreSQL
psql -U postgres

# Créer un utilisateur et une base de données
CREATE USER communication_user WITH PASSWORD 'votre_mot_de_passe_sécurisé';
CREATE DATABASE vieuxmoulin_communication OWNER communication_user;
GRANT ALL PRIVILEGES ON DATABASE vieuxmoulin_communication TO communication_user;
\q

# Initialiser la base de données (les migrations sont exécutées automatiquement au premier démarrage)
```

### 3. Configuration du Service de File d'Attente

```bash
# S'assurer que RabbitMQ est en cours d'exécution
# Créer un utilisateur et un vhost dédiés (optionnel mais recommandé)
rabbitmqctl add_user communication_user votre_mot_de_passe_sécurisé
rabbitmqctl add_vhost communication_vhost
rabbitmqctl set_permissions -p communication_vhost communication_user ".*" ".*" ".*"
```

### 4. Configuration du Service de Cache

```bash
# S'assurer que Redis est en cours d'exécution
# Créer une base de données dédiée (optionnel)
# Par défaut, la base 0 est utilisée
```

### 5. Configuration du Module

```bash
# Exécuter le script de configuration interactif
python src/setup.py

# Suivre les instructions pour configurer les accès aux bases de données, 
# API, et autres paramètres du module
```

## Configuration des Services Externes

### 1. API Facebook

1. Rendez-vous sur [Facebook Developers](https://developers.facebook.com/)
2. Créez une nouvelle application
3. Configurez l'API Graph et les permissions nécessaires (manage_pages, publish_pages)
4. Obtenez l'ID de l'application, le secret, l'ID de page et le token d'accès
5. Mettez à jour le fichier `config/platforms.json` avec ces informations

### 2. API Instagram

1. Connectez votre compte Instagram à une page Facebook
2. Sur Facebook Developers, ajoutez le produit Instagram à votre application
3. Obtenez l'ID du compte business et le token d'accès
4. Mettez à jour le fichier `config/platforms.json` avec ces informations

### 3. Service d'Envoi d'Emails (SendGrid)

1. Créez un compte sur [SendGrid](https://sendgrid.com/)
2. Générez une clé API dans les paramètres
3. Vérifiez votre domaine d'envoi
4. Mettez à jour le fichier `config/settings.json` avec ces informations

### 4. Service d'Envoi de SMS (Twilio)

1. Créez un compte sur [Twilio](https://www.twilio.com/)
2. Obtenez un numéro de téléphone pour l'envoi de SMS
3. Notez votre SID de compte et votre token d'authentification
4. Mettez à jour le fichier `config/settings.json` avec ces informations

## Déploiement

### Option 1 : Déploiement Direct

```bash
# Démarrer le module en tant que service
python src/main.py
```

Pour un environnement de production, il est recommandé d'utiliser un gestionnaire de processus comme systemd ou supervisor pour assurer que le service reste actif et redémarre automatiquement si nécessaire.

### Option 2 : Déploiement avec Docker

```bash
# Construire l'image Docker
docker build -t vieuxmoulin/communication:latest .

# Démarrer le conteneur
docker run -d --name vieuxmoulin-communication \
  -p 5000:5000 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  vieuxmoulin/communication:latest
```

### Option 3 : Déploiement avec Docker Compose

Créez un fichier `docker-compose.yml` :

```yaml
version: '3.8'
services:
  communication-api:
    build: .
    image: vieuxmoulin/communication-api:latest
    restart: always
    ports:
      - "5000:5000"
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    environment:
      - DB_CONNECTION_STRING=postgresql://communication_user:password@db:5432/vieuxmoulin_communication
      - REDIS_URL=redis://redis:6379
      - RABBITMQ_URL=amqp://user:password@rabbitmq:5672/vhost
      - LOG_LEVEL=info
    depends_on:
      - db
      - redis
      - rabbitmq
  
  db:
    image: postgres:14
    restart: always
    environment:
      - POSTGRES_USER=communication_user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=vieuxmoulin_communication
    volumes:
      - communication-data:/var/lib/postgresql/data
  
  redis:
    image: redis:6
    restart: always
    volumes:
      - communication-cache:/data
  
  rabbitmq:
    image: rabbitmq:3-management
    restart: always
    ports:
      - "15672:15672"
    environment:
      - RABBITMQ_DEFAULT_USER=user
      - RABBITMQ_DEFAULT_PASS=password
      - RABBITMQ_DEFAULT_VHOST=vhost
    volumes:
      - communication-queue:/var/lib/rabbitmq

volumes:
  communication-data:
  communication-cache:
  communication-queue:
```

Puis démarrez les services :

```bash
docker-compose up -d
```

## Vérification du Déploiement

### API Health Check

```bash
curl http://localhost:5000/api/communication/status
```

La réponse devrait inclure un statut "ok" et des informations sur les services connectés.

### Test des fonctionnalités principales

1. **Publication sur les réseaux sociaux**

```bash
curl -X POST http://localhost:5000/api/communication/publish \
  -H "Content-Type: application/json" \
  -H "X-API-Key: VOTRE_CLE_API" \
  -d '{
    "content": {
      "title": "Test de publication",
      "body": "Ceci est un test de publication automatique.",
      "media_urls": []
    },
    "platforms": ["facebook"],
    "dry_run": true
  }'
```

2. **Envoi de notification**

```bash
curl -X POST http://localhost:5000/api/communication/notify \
  -H "Content-Type: application/json" \
  -H "X-API-Key: VOTRE_CLE_API" \
  -d '{
    "template": "test",
    "recipients": ["email@example.com"],
    "data": {
      "message": "Ceci est un test de notification."
    },
    "channels": ["email"],
    "dry_run": true
  }'
```

## Maintenance

### Logs

Les logs sont stockés dans le répertoire `logs/` et sont également envoyés à la sortie standard.

### Surveillance

Pour une surveillance avancée, il est recommandé d'utiliser un outil comme Prometheus + Grafana ou ELK Stack.

### Sauvegardes

N'oubliez pas de sauvegarder régulièrement :
- La base de données PostgreSQL
- Les fichiers de configuration dans `config/`
- Les données Redis (si elles sont persistantes)

## Résolution des problèmes

### Problèmes de connexion aux services externes

1. Vérifiez les paramètres de connexion dans les fichiers de configuration
2. Assurez-vous que les services sont accessibles depuis le serveur où le module s'exécute
3. Vérifiez que les tokens d'API n'ont pas expiré

### Problèmes d'envoi de notifications

1. Vérifiez les logs pour les messages d'erreur spécifiques
2. Testez les paramètres d'envoi directement avec l'API du fournisseur
3. Vérifiez que les templates de message sont correctement formatés

### Problèmes de publication sur les réseaux sociaux

1. Vérifiez que les tokens d'accès sont valides et n'ont pas expiré
2. Assurez-vous que les permissions sont correctement configurées
3. Vérifiez que le contenu respecte les limitations des plateformes

## Support

Pour toute question ou problème supplémentaire, consultez :
- La documentation technique dans `COMMUNICATION.md`
- Les exemples d'utilisation dans le répertoire `examples/`
