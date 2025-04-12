# Module Capteurs IoT - Le Vieux Moulin

Ce module gère l'ensemble des capteurs IoT installés dans le restaurant "Le Vieux Moulin" pour la surveillance en temps réel des stocks et équipements. Il permet la collecte, le traitement et la transmission sécurisée des données vers le serveur central.

## Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Capteurs supportés](#capteurs-supportés)
3. [Architecture du module](#architecture-du-module)
4. [Installation](#installation)
   - [Prérequis matériels](#prérequis-matériels)
   - [Prérequis logiciels](#prérequis-logiciels)
   - [Installation des dépendances](#installation-des-dépendances)
   - [Configuration du système](#configuration-du-système)
5. [Câblage et branchements](#câblage-et-branchements)
   - [Cellules de charge (HX711)](#cellules-de-charge-hx711)
   - [Capteur ultrasonique (HC-SR04)](#capteur-ultrasonique-hc-sr04)
   - [Capteur de température (DS18B20)](#capteur-de-température-ds18b20)
   - [Capteur de turbidité](#capteur-de-turbidité)
6. [Configuration](#configuration)
   - [Fichier de configuration](#fichier-de-configuration)
   - [Options de configuration](#options-de-configuration)
7. [Utilisation](#utilisation)
   - [Démarrage du système](#démarrage-du-système)
   - [Interface en ligne de commande](#interface-en-ligne-de-commande)
   - [Calibration des capteurs](#calibration-des-capteurs)
8. [Transmission des données](#transmission-des-données)
   - [Format des données](#format-des-données)
   - [Protocole MQTT](#protocole-mqtt)
   - [Gestion hors ligne](#gestion-hors-ligne)
9. [Maintenance](#maintenance)
   - [Vérification des capteurs](#vérification-des-capteurs)
   - [Dépannage courant](#dépannage-courant)
   - [Journaux (logs)](#journaux-logs)
10. [Développement](#développement)
    - [Structure du code](#structure-du-code)
    - [Ajouter un nouveau type de capteur](#ajouter-un-nouveau-type-de-capteur)
    - [Tests](#tests)
11. [Support](#support)

## Vue d'ensemble

Le module Capteurs IoT est conçu pour surveiller en temps réel les niveaux de stock d'ingrédients (via des cellules de charge sous les bacs) et l'état de la friteuse (niveau et qualité d'huile). Les données collectées sont transmises au serveur central via WiFi ou Bluetooth, avec mise en cache locale en cas de perte de connexion.

Ce système permet d'optimiser la gestion des stocks, de réduire le gaspillage et d'anticiper les besoins en approvisionnement, tout en assurant un suivi de la qualité des équipements de cuisson.

## Capteurs supportés

- **Cellules de charge HX711** : Pour mesurer le poids des ingrédients dans différents bacs
- **Capteur ultrasonique HC-SR04** : Pour mesurer le niveau d'huile dans la friteuse
- **Capteur de température DS18B20** : Pour surveiller la température de l'huile
- **Capteur de turbidité** (optionnel) : Pour évaluer la qualité de l'huile

## Architecture du module

Le module est organisé en trois composants principaux :

1. **`weight_sensor.py`** : Gère les cellules de charge pour la mesure du poids des ingrédients
2. **`oil_level_sensor.py`** : Gère les capteurs de niveau et de qualité d'huile pour la friteuse
3. **`network_manager.py`** : Gère la connexion réseau et la transmission des données

Un script principal **`main.py`** orchestre l'ensemble du système et permet son exécution en tant que service.

## Installation

### Prérequis matériels

- Raspberry Pi 3B+ ou supérieur (ou équivalent)
- Cellules de charge avec amplificateurs HX711
- Capteur ultrasonique HC-SR04
- Capteur de température DS18B20 résistant à la chaleur
- Capteur de turbidité (optionnel)
- Câblage et connecteurs
- Alimentation stable

### Prérequis logiciels

- Raspberry Pi OS (ou équivalent)
- Python 3.7+
- Accès réseau (WiFi ou Ethernet)

### Installation des dépendances

```bash
# Cloner le dépôt
git clone https://github.com/Casius999/Le-Vieux-Moulin.git
cd Le-Vieux-Moulin/iot/sensor_module

# Installer les dépendances
pip install -r requirements.txt

# Activer le bus 1-Wire pour le capteur DS18B20
echo "dtoverlay=w1-gpio,gpiopin=4" | sudo tee -a /boot/config.txt
sudo reboot
```

### Configuration du système

1. Créez un fichier de configuration basé sur l'exemple :
   ```bash
   cp config.example.json config.json
   ```

2. Modifiez le fichier de configuration selon votre installation :
   ```bash
   nano config.json
   ```

3. Configuration comme service (optionnel) :
   ```bash
   sudo cp lvm_sensors.service /etc/systemd/system/
   sudo systemctl enable lvm_sensors.service
   sudo systemctl start lvm_sensors.service
   ```

## Câblage et branchements

### Cellules de charge (HX711)

Pour chaque cellule de charge :

1. Connectez la cellule de charge à l'amplificateur HX711 :
   - Fil rouge → E+
   - Fil noir → E-
   - Fil blanc → A+
   - Fil vert → A-

2. Connectez l'amplificateur HX711 au Raspberry Pi :
   - VCC → 3.3V (Pin 1)
   - GND → GND (Pin 6)
   - DT (Data) → GPIO assigné (ex: GPIO 5)
   - SCK (Clock) → GPIO assigné (ex: GPIO 6)

### Capteur ultrasonique (HC-SR04)

1. Connectez le capteur HC-SR04 au Raspberry Pi :
   - VCC → 5V (Pin 2)
   - GND → GND (Pin 6)
   - TRIG → GPIO assigné (ex: GPIO 23)
   - ECHO → Diviseur de tension → GPIO assigné (ex: GPIO 24)

   > **Note**: Un diviseur de tension est nécessaire pour l'ECHO car il renvoie 5V, alors que le Raspberry Pi accepte 3.3V max.

### Capteur de température (DS18B20)

1. Connectez le capteur DS18B20 au Raspberry Pi :
   - VCC → 3.3V (Pin 1)
   - GND → GND (Pin 6)
   - DATA → GPIO4 (Pin 7) avec résistance pull-up de 4.7kΩ

2. Pour une utilisation dans l'huile, utilisez une version étanche et résistante à la chaleur.

### Capteur de turbidité

Si utilisé, connectez selon les spécifications du capteur choisi. Généralement :
   - VCC → 5V
   - GND → GND
   - OUT → ADC → GPIO

## Configuration

### Fichier de configuration

Le système utilise un fichier de configuration JSON pour définir les paramètres des capteurs et du réseau. Exemple :

```json
{
  "device_id": "cuisine_principale",
  "server": {
    "host": "192.168.1.100",
    "mqtt_port": 1883,
    "mqtt_use_tls": false
  },
  "network": {
    "type": "wifi",
    "ssid": "LVM_Network",
    "password": "password123"
  },
  "sensors": {
    "weight": [
      {
        "name": "bac_farine",
        "pins": {"dout": 5, "sck": 6},
        "reference_unit": 2145.3,
        "min_weight": 0.0,
        "max_weight": 5000.0
      },
      {
        "name": "bac_sucre",
        "pins": {"dout": 17, "sck": 18},
        "reference_unit": 1998.7,
        "min_weight": 0.0,
        "max_weight": 2000.0
      }
    ],
    "fryer": {
      "name": "friteuse_principale",
      "ultrasonic": {"trigger": 23, "echo": 24},
      "temp_pin": 4,
      "turbidity_pin": 17,
      "depth": 15.0
    }
  },
  "update_interval": 60
}
```

### Options de configuration

| Paramètre | Description | Valeur par défaut |
|-----------|-------------|-------------------|
| `device_id` | Identifiant unique du dispositif | `"lvm_kitchen_01"` |
| `server.host` | Adresse IP ou hostname du serveur | `"localhost"` |
| `server.mqtt_port` | Port MQTT du serveur | `1883` |
| `server.mqtt_use_tls` | Utilisation de TLS pour MQTT | `false` |
| `network.type` | Type de connexion (`wifi`, `bluetooth`, `ethernet`) | `"wifi"` |
| `network.ssid` | SSID du réseau WiFi | - |
| `network.password` | Mot de passe WiFi | - |
| `sensors.weight[].name` | Nom du capteur de poids | - |
| `sensors.weight[].pins` | Pins GPIO pour le capteur | - |
| `sensors.weight[].reference_unit` | Facteur de calibration | `1.0` |
| `sensors.fryer.ultrasonic` | Pins pour le capteur ultrasonique | - |
| `sensors.fryer.temp_pin` | Pin GPIO pour le capteur de température | - |
| `update_interval` | Intervalle d'envoi des données (secondes) | `60` |

## Utilisation

### Démarrage du système

Exécutez le script principal :

```bash
python main.py --config config.json
```

Options de ligne de commande :
- `--config` : Chemin vers le fichier de configuration
- `--log-level` : Niveau de journalisation (`DEBUG`, `INFO`, `WARNING`, `ERROR`)

### Interface en ligne de commande

Le script principal offre une interface simple en ligne de commande qui affiche l'état des capteurs et les messages importants.

Pour arrêter proprement le système, utilisez Ctrl+C.

### Calibration des capteurs

#### Calibration des cellules de charge

Pour une calibration précise des cellules de charge :

1. Exécutez le script de calibration :
   ```bash
   python calibrate_weight.py --sensor bac_farine
   ```

2. Suivez les instructions à l'écran pour placer des poids de référence et enregistrer la valeur de calibration.

3. Mettez à jour la valeur `reference_unit` dans le fichier de configuration.

#### Calibration du capteur de niveau d'huile

1. Assurez-vous que la friteuse est vide et propre.

2. Exécutez le script de calibration :
   ```bash
   python calibrate_oil_level.py
   ```

3. Suivez les instructions pour mesurer la profondeur et calibrer le capteur.

## Transmission des données

### Format des données

Les données sont envoyées au format JSON avec la structure suivante :

```json
{
  "timestamp": 1649247668.453,
  "device_id": "cuisine_principale",
  "type": "weight_sensors",
  "data": {
    "bac_farine": 2450.5,
    "bac_sucre": 1230.8
  }
}
```

```json
{
  "timestamp": 1649247668.556,
  "device_id": "cuisine_principale",
  "type": "fryer",
  "name": "friteuse_principale",
  "operating_status": "ready",
  "level": {
    "level_cm": 10.5,
    "level_percent": 70.0,
    "status": "normal"
  },
  "quality": {
    "temperature": 175.2,
    "quality_percent": 85.0,
    "needs_replacement": false
  }
}
```

### Protocole MQTT

Les données sont publiées sur des topics MQTT structurés comme suit :
- `data/{device_id}/weight` - Données des capteurs de poids
- `data/{device_id}/fryer` - Données de la friteuse

Le système souscrit aux topics de contrôle :
- `control/{device_id}/restart` - Commande de redémarrage
- `control/{device_id}/configure` - Mise à jour de configuration

### Gestion hors ligne

En cas de perte de connexion, les données sont stockées localement dans un cache et envoyées dès que la connexion est rétablie. Le cache est géré automatiquement pour éviter de remplir l'espace disque.

## Maintenance

### Vérification des capteurs

Pour vérifier l'état des capteurs :

```bash
python check_sensors.py
```

Ce script teste chaque capteur et affiche son état et les éventuels problèmes détectés.

### Dépannage courant

| Problème | Cause possible | Solution |
|----------|----------------|----------|
| Lectures de poids instables | Interférences électriques | Vérifier le blindage des câbles |
| Capteur non répondant | Connexion défectueuse | Vérifier les branchements |
| Dérive des mesures | Décalibration | Recalibrer le capteur |
| Connexion réseau perdue | Problème WiFi | Vérifier la configuration réseau |

### Journaux (logs)

Les journaux sont stockés dans `/var/log/lvm_sensors.log` (si configuré comme service) ou affichés dans la console.

Pour analyser les journaux :

```bash
tail -f /var/log/lvm_sensors.log
```

## Développement

### Structure du code

- `weight_sensor.py` : Classes pour les capteurs de poids
  - `HX711` : Interface bas niveau pour l'amplificateur HX711
  - `WeightSensor` : Gestion d'un capteur de poids individuel
  - `WeightSensorArray` : Gestion de plusieurs capteurs

- `oil_level_sensor.py` : Classes pour la friteuse
  - `OilQualitySensor` : Capteur de qualité d'huile
  - `OilLevelSensor` : Capteur de niveau d'huile
  - `FryerMonitor` : Classe principale combinant niveau et qualité

- `network_manager.py` : Gestion réseau
  - `NetworkManager` : Classe principale pour la connectivité
  - `MQTTClient` : Client MQTT pour la communication
  - `DataCache` : Système de mise en cache local

### Ajouter un nouveau type de capteur

1. Créez un nouveau fichier Python pour votre capteur (ex: `temperature_sensor.py`).

2. Implémentez une classe pour gérer votre capteur avec au minimum :
   - Méthode d'initialisation (`__init__`)
   - Méthode de lecture (`read` ou équivalent)
   - Méthode pour obtenir l'état (`get_status`)

3. Intégrez votre capteur dans `main.py` et mettez à jour la configuration.

### Tests

Des tests unitaires sont disponibles dans le dossier `tests/` :

```bash
# Exécuter tous les tests
pytest

# Exécuter des tests spécifiques
pytest tests/test_weight_sensor.py
```

## Support

Pour toute question ou problème :
- Consultez la documentation complète dans le dossier `/docs`
- Créez une issue sur le dépôt GitHub
- Contactez l'équipe technique à support@levieuxmoulin.fr
