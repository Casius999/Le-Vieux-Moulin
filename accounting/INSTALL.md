# Guide d'Installation - Module de Comptabilité Avancé

Ce guide détaille les étapes d'installation et de configuration du module de comptabilité avancé pour le système de gestion du restaurant "Le Vieux Moulin".

## Prérequis

- Python 3.9 ou supérieur
- Base de données PostgreSQL 13 ou supérieur
- Serveur central du système "Le Vieux Moulin" fonctionnel
- Accès au réseau interne du restaurant pour les connexions aux modules (caisse, stocks, etc.)

## Dépendances Python

Le module nécessite les packages Python suivants :
```
aiohttp>=3.8.1
fastapi>=0.75.0
uvicorn>=0.17.6
sqlalchemy>=1.4.36
asyncpg>=0.25.0
pydantic>=1.9.0
python-jose>=3.3.0
python-multipart>=0.0.5
pandas>=1.4.2
numpy>=1.22.3
matplotlib>=3.5.1
PyPDF2>=2.3.0
XlsxWriter>=3.0.3
cryptography>=37.0.2
email-validator>=1.2.1
jinja2>=3.1.1
python-dateutil>=2.8.2
aiocache>=0.11.1
structlog>=22.1.0
tenacity>=8.0.1
```

## Étapes d'Installation

### 1. Préparation de l'Environnement

```bash
# Créer un environnement virtuel
python -m venv venv_accounting
source venv_accounting/bin/activate  # Sur Linux/Mac
# ou
venv_accounting\Scripts\activate  # Sur Windows

# Installer les dépendances
pip install -r requirements.txt
```

### 2. Configuration de la Base de Données

```bash
# Créer une base de données dédiée
psql -U postgres -c "CREATE DATABASE levieuxmoulin_accounting;"
psql -U postgres -c "CREATE USER accounting_user WITH ENCRYPTED PASSWORD 'secure_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE levieuxmoulin_accounting TO accounting_user;"
```

### 3. Configuration du Module

1. Copiez le fichier de configuration modèle :

```bash
cp config/config.example.json config/config.json
```

2. Modifiez le fichier de configuration avec vos paramètres :

```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "database": "levieuxmoulin_accounting",
    "user": "accounting_user",
    "password": "secure_password",
    "pool_size": 10
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8081,
    "debug": false,
    "log_level": "info"
  },
  "security": {
    "secret_key": "your-secret-key-here",
    "algorithm": "HS256",
    "token_expire_minutes": 60,
    "ssl_cert": "/path/to/certificate.pem",
    "ssl_key": "/path/to/key.pem"
  },
  "integration": {
    "central_server_url": "https://server.levieuxmoulin.fr/api",
    "api_key": "your-api-key-here",
    "retry_attempts": 3,
    "timeout_seconds": 30
  },
  "reporting": {
    "report_directory": "/path/to/reports",
    "temp_directory": "/tmp/accounting",
    "default_format": "pdf"
  },
  "email": {
    "smtp_server": "smtp.example.com",
    "smtp_port": 587,
    "username": "accounting@levieuxmoulin.fr",
    "password": "email-password",
    "default_sender": "Comptabilité Le Vieux Moulin <accounting@levieuxmoulin.fr>"
  },
  "data_sources": {
    "pos": {
      "type": "api",
      "url": "https://server.levieuxmoulin.fr/api/pos",
      "auth_type": "bearer",
      "refresh_interval_minutes": 60
    },
    "inventory": {
      "type": "api",
      "url": "https://server.levieuxmoulin.fr/api/inventory",
      "auth_type": "bearer",
      "refresh_interval_minutes": 30
    },
    "suppliers": {
      "type": "api",
      "url": "https://server.levieuxmoulin.fr/api/suppliers",
      "auth_type": "bearer",
      "refresh_interval_minutes": 180
    },
    "payroll": {
      "type": "file_import",
      "directory": "/path/to/payroll/imports",
      "file_pattern": "*.csv",
      "import_schedule": "0 0 1 * *"  # Cron syntax: At midnight on the 1st of each month
    }
  }
}
```

3. Configurez les paramètres spécifiques à votre installation :

- Remplacez `your-secret-key-here` par une clé secrète générée (voir section Sécurité)
- Adaptez les chemins de fichiers aux répertoires de votre serveur
- Configurez les identifiants de base de données, d'email et d'API

### 4. Sécurité

Pour générer une clé secrète sécurisée :

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Initialisation de la Base de Données

Exécutez le script d'initialisation de la base de données :

```bash
python -m accounting.scripts.init_db
```

### 6. Configuration des Rapports Automatiques

Modifiez le fichier de configuration des rapports pour définir les périodicités et destinataires :

```bash
cp config/reports.example.json config/reports.json
```

Puis modifiez-le selon vos besoins.

### 7. Déploiement comme Service

#### Avec Systemd (Linux)

1. Créez un fichier service :

```bash
sudo nano /etc/systemd/system/accounting-module.service
```

2. Ajoutez la configuration suivante :

```
[Unit]
Description=Le Vieux Moulin Accounting Module
After=network.target postgresql.service

[Service]
User=accounting_user
Group=accounting_user
WorkingDirectory=/path/to/accounting
ExecStart=/path/to/accounting/venv_accounting/bin/python -m accounting.main
Restart=always
RestartSec=5
Environment=PYTHONPATH=/path/to/accounting

[Install]
WantedBy=multi-user.target
```

3. Activez et démarrez le service :

```bash
sudo systemctl daemon-reload
sudo systemctl enable accounting-module
sudo systemctl start accounting-module
```

#### Avec Docker

1. Assurez-vous que Docker est installé sur votre système
2. Construisez l'image :

```bash
docker build -t levieuxmoulin/accounting-module .
```

3. Lancez le conteneur :

```bash
docker run -d --name accounting-module \
  -v /path/to/config:/app/config \
  -v /path/to/reports:/app/reports \
  -p 8081:8081 \
  levieuxmoulin/accounting-module
```

## Vérification de l'Installation

Une fois le module démarré, vérifiez que tout fonctionne correctement :

```bash
# Vérifier que le service est actif
curl http://localhost:8081/health

# Vérifier l'accès à l'API (nécessite un token valide)
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8081/api/v1/status
```

## Configuration du Client Comptable

1. Générez des identifiants API pour le comptable externe :

```bash
python -m accounting.scripts.create_external_account --role accountant --name "Cabinet Comptable"
```

2. Fournissez au comptable :
   - L'URL d'accès au portail comptable
   - Les identifiants générés
   - La documentation d'utilisation du portail

## Tâches planifiées

Les rapports automatiques et les tâches de maintenance sont gérés par le planificateur interne. Pour configurer des tâches supplémentaires, modifiez le fichier `config/scheduler.json`.

## Dépannage

### Problèmes de connexion à la base de données

Vérifiez :
- Les paramètres de connexion dans `config.json`
- Que PostgreSQL est en cours d'exécution
- Les autorisations du compte utilisateur

### Problèmes d'intégration avec les autres modules

Vérifiez :
- La connectivité réseau
- Les logs d'erreur dans `/logs/integration.log`
- Les identifiants API dans la configuration

### Erreurs dans la génération des rapports

Consultez les logs dans `/logs/reporting.log` et vérifiez :
- Les permissions des répertoires de sortie
- La validité des données sources
- La configuration des modèles de rapports

## Mise à jour du Module

Pour mettre à jour le module :

```bash
# Arrêter le service
sudo systemctl stop accounting-module

# Mettre à jour les fichiers
git pull

# Installer les nouvelles dépendances
source venv_accounting/bin/activate
pip install -r requirements.txt

# Appliquer les migrations de base de données
python -m accounting.scripts.migrate_db

# Redémarrer le service
sudo systemctl start accounting-module
```

## Support

Pour toute question ou assistance, contactez l'équipe technique à support@levieuxmoulin.fr ou créez une issue sur le dépôt Git du projet.
