# Multi-stage build pour optimiser la taille de l'image

# Étape 1: Build du frontend
FROM node:18-alpine as frontend-build
WORKDIR /app/frontend

# Copie des fichiers package.json et installation des dépendances
COPY frontend/package*.json ./
RUN npm ci

# Copie des fichiers source et build
COPY frontend/ ./
RUN npm run build

# Étape 2: Build du backend
FROM node:18-alpine as backend-build
WORKDIR /app/backend

# Copie des fichiers package.json et installation des dépendances
COPY backend/package*.json ./
RUN npm ci --only=production

# Étape 3: Image finale
FROM node:18-alpine
WORKDIR /app

# Copie des fichiers nécessaires depuis les étapes précédentes
COPY --from=backend-build /app/backend/node_modules /app/node_modules
COPY backend/ /app/
COPY --from=frontend-build /app/frontend/build /app/public

# Création du dossier de logs
RUN mkdir -p logs

# Exposition du port
EXPOSE 5000

# Commande de démarrage
CMD ["node", "server.js"]
