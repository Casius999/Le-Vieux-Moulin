FROM python:3.9-slim

# Définir des variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Exposer le port pour l'API
EXPOSE 8000

# Variable d'environnement pour spécifier le répertoire des modèles
ENV MODELS_DIR=/app/models

# Créer les répertoires nécessaires
RUN mkdir -p /app/models /app/data /app/logs /app/output

# Commande par défaut (peut être remplacée lors de l'exécution)
CMD ["python", "-m", "prediction_module", "serve", "--host", "0.0.0.0", "--port", "8000"]

# Instructions d'utilisation:
# 
# Construction de l'image:
#   docker build -t levieuxmoulin/prediction:latest -f Dockerfile .
#
# Démarrage du serveur API:
#   docker run -p 8000:8000 -v /chemin/local/models:/app/models levieuxmoulin/prediction:latest
#
# Exécution de l'entraînement:
#   docker run -v /chemin/local/data:/app/data -v /chemin/local/models:/app/models levieuxmoulin/prediction:latest python -m prediction_module train --all
#
# Exécution de l'évaluation:
#   docker run -v /chemin/local/data:/app/data -v /chemin/local/models:/app/models -v /chemin/local/output:/app/output levieuxmoulin/prediction:latest python -m prediction_module evaluate --all
