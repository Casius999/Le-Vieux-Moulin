# Dockerfile pour le module de commande vocale du système Le Vieux Moulin
FROM python:3.11-slim

# Métadonnées
LABEL maintainer="Équipe Technique Le Vieux Moulin <tech@levieuxmoulin.fr>"
LABEL version="1.0.0"
LABEL description="Module de commande vocale pour le système de gestion intelligente Le Vieux Moulin"

# Installation des dépendances système pour PyAudio et PocketSphinx
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    swig \
    libpulse-dev \
    libasound2-dev \
    gcc \
    g++ \
    make \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Définition du répertoire de travail
WORKDIR /app

# Copie des fichiers de dépendances
COPY requirements.txt .

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copie de l'application
COPY . .

# Création d'un utilisateur non-root pour la sécurité
RUN useradd -m voiceapp
RUN chown -R voiceapp:voiceapp /app
USER voiceapp

# Exposition du port de l'interface web
EXPOSE 5000

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=run.py

# Commande de démarrage
CMD ["python", "run.py", "--host", "0.0.0.0", "--port", "5000"]
