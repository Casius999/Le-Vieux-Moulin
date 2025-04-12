# Module IoT - Le Vieux Moulin

Ce répertoire contient l'ensemble du code et de la documentation pour les modules IoT qui équipent le restaurant "Le Vieux Moulin". Ces modules permettent la collecte en temps réel des données sur les stocks, l'état des équipements et les conditions de travail.

## Structure du Répertoire

- **/sensor_module/** - Modules capteurs et configuration
- **/gateway/** - Passerelle IoT et serveur MQTT local
- **/firmware/** - Firmware pour les différents types de capteurs
- **/calibration/** - Outils et procédures de calibration
- **/monitoring/** - Outils de surveillance et d'alerte

## Types de Capteurs Implémentés

1. **Cellules de charge pour bacs d'ingrédients**
   - Capteurs de poids haute précision pour tous les ingrédients stockés
   - Sensibilité adaptée à différents types d'ingrédients (solides, liquides, granuleux)

2. **Sonde de niveau d'huile pour friteuse**
   - Mesure en temps réel du niveau d'huile
   - Analyse de la qualité de l'huile (température, turbidité)
   - Alerte automatique pour changement d'huile

3. **Capteurs de température**
   - Surveillance des équipements de cuisson (four à pizza, etc.)
   - Surveillance des équipements de réfrigération
   - Monitoring de la température ambiante

4. **Autres capteurs**
   - Détecteurs d'humidité
   - Capteurs de porte ouverte/fermée
   - Capteurs de consommation électrique

## Passerelle IoT

La passerelle IoT est basée sur ESP32/Raspberry Pi et assure les fonctions suivantes:
- Collecte des données des capteurs via WiFi, Bluetooth ou filaire
- Mise en cache local en cas de perte de connexion
- Prétraitement des données (filtrage, agrégation)
- Transmission sécurisée vers le serveur central

## Protocoles Utilisés

- **MQTT** - Communication légère et efficace entre capteurs et passerelle
- **HTTPS/TLS** - Communication sécurisée entre passerelle et serveur central
- **BLE (Bluetooth Low Energy)** - Pour les capteurs à faible consommation
- **WiFi** - Pour les capteurs nécessitant plus de bande passante

## Sécurité

- Toutes les communications sont chiffrées
- Authentification forte pour chaque capteur et passerelle
- Mise à jour sécurisée du firmware (OTA)
- Isolation réseau des dispositifs IoT

## Installation et Configuration

Référez-vous au dossier `/sensor_module/README.md` pour les instructions détaillées d'installation et de configuration des différents capteurs.

La procédure générale d'installation est la suivante:

1. Installation physique des capteurs aux emplacements prévus
2. Configuration de la passerelle IoT
3. Calibration des capteurs selon les spécifications
4. Configuration de la connexion au serveur central
5. Vérification et validation du système

## Développement et Extension

Pour ajouter un nouveau type de capteur:
1. Créez un sous-dossier dans `/firmware/` pour le nouveau capteur
2. Implémentez le firmware compatible avec le protocole MQTT
3. Ajoutez la configuration dans la passerelle IoT
4. Mettez à jour la documentation appropriée

## Dépendances Matérielles

- ESP32 ou Arduino pour les capteurs simples
- Raspberry Pi 4 (ou supérieur) pour la passerelle
- Cellules de charge HX711 pour les capteurs de poids
- Capteurs de température DS18B20
- Modules WiFi et Bluetooth pour la connectivité

## Dépendances Logicielles

- Arduino IDE ou PlatformIO pour le développement firmware
- Bibliothèque MQTT (PubSubClient)
- Bibliothèque pour cellules de charge HX711
- Bibliothèque pour capteurs de température
- Mosquitto MQTT Broker pour la passerelle

---

Pour toute question spécifique ou assistance, référez-vous à la documentation détaillée des modules ou contactez l'équipe de développement.
