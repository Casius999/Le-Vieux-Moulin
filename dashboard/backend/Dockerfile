FROM node:18-alpine

# Créer le répertoire de l'application
WORKDIR /app

# Copier les fichiers de dépendances
COPY package*.json ./

# Installer les dépendances
RUN npm ci --only=production

# Copier les fichiers de l'application
COPY . .

# Créer le dossier de logs
RUN mkdir -p logs

# Exposer le port
EXPOSE 5000

# Commande de démarrage
CMD ["node", "server.js"]
