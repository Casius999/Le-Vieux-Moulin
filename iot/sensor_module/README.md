# Module Capteurs IoT - Le Vieux Moulin

Ce dossier contient tous les éléments nécessaires pour l'installation, la configuration et la maintenance des différents capteurs IoT déployés dans le restaurant "Le Vieux Moulin".

## Types de Capteurs et Installation

### 1. Cellules de Charge pour Bacs d'Ingrédients

Ces capteurs permettent de mesurer en temps réel le poids des ingrédients dans les bacs de stockage.

#### Matériel requis
- Cellule de charge HX711 (modèle 5kg ou 10kg selon le bac)
- Amplificateur HX711
- Boîtier étanche IP65
- Câble blindé 4 conducteurs
- Support métallique pour installation sous le bac

#### Installation
1. Fixez solidement la cellule de charge sous le bac d'ingrédients
2. Connectez l'amplificateur HX711 à la cellule de charge
3. Reliez l'amplificateur au microcontrôleur ESP32 selon le schéma de câblage fourni dans `/wiring_diagrams/weight_sensor.pdf`
4. Placez le boîtier de protection pour protéger les composants électroniques

#### Calibration
```arduino
// Exemple de code de calibration pour cellule de charge
#include "HX711.h"

#define DOUT_PIN  5
#define SCK_PIN  6
#define REFERENCE_WEIGHT 1000  // en grammes

HX711 scale;

void setup() {
  Serial.begin(9600);
  scale.begin(DOUT_PIN, SCK_PIN);
  
  Serial.println("Retirez tout poids du capteur...");
  delay(5000);
  scale.tare();  // Réinitialisation à zéro
  
  Serial.println("Placez un poids de référence...");
  delay(5000);
  
  float reading = scale.get_value(10);  // Moyenne sur 10 lectures
  float calibration_factor = reading / REFERENCE_WEIGHT;
  
  Serial.print("Facteur de calibration: ");
  Serial.println(calibration_factor);
}

void loop() {}
```

### 2. Sonde Niveau d'Huile Friteuse

Cette sonde surveille le niveau et la qualité de l'huile dans la friteuse.

#### Matériel requis
- Capteur de niveau à ultrasons résistant à la chaleur
- Sonde de température DS18B20 haute température
- Boîtier résistant à la chaleur
- Câble haute température

#### Installation
1. Fixez le capteur de niveau sur le bord supérieur de la friteuse
2. Placez la sonde de température à mi-hauteur dans l'huile (sans toucher les résistances)
3. Acheminez les câbles vers le boîtier contenant l'ESP32
4. Suivez le schéma de câblage dans `/wiring_diagrams/oil_sensor.pdf`

#### Configuration
```json
// Exemple de configuration pour la sonde d'huile
{
  "sensor_id": "friteuse_01",
  "sensor_type": "oil_level",
  "update_frequency": 60,  // secondes
  "alert_threshold_low": 2.5,  // cm du fond
  "alert_threshold_high": 10.0,  // cm du fond
  "temperature_max": 180,  // °C
  "temperature_idle": 120,  // °C
  "mqtt_topic": "restaurant/kitchen/fryer/oil_level"
}
```

### 3. Capteurs de Température

Ces capteurs surveillent la température des équipements de cuisson et de réfrigération.

#### Matériel requis
- Capteurs DS18B20 (version standard ou haute température selon l'usage)
- Câble résistant à la chaleur pour les fours
- Boîtier de protection

#### Installation
1. Pour les réfrigérateurs: placez le capteur à l'intérieur, à mi-hauteur
2. Pour les fours: installez le capteur dans l'emplacement prévu par le fabricant
3. Connectez les capteurs au bus OneWire de l'ESP32
4. Configurez l'adresse unique de chaque capteur

## Communication et Configuration

### MQTT Topics

Tous les capteurs publient leurs données sur des topics MQTT structurés comme suit:
```
restaurant/[zone]/[equipement]/[mesure]
```

Exemples:
- `restaurant/stockage/bac_farine/poids`
- `restaurant/cuisine/friteuse/niveau_huile`
- `restaurant/cuisine/four_pizza/temperature`

### Format des Données

Les données sont publiées au format JSON:
```json
{
  "sensor_id": "bac_farine_01",
  "timestamp": 1617283200,
  "value": 2.45,
  "unit": "kg",
  "battery": 92,
  "rssi": -67
}
```

## Dépannage

### Problèmes courants et solutions

| Problème | Cause possible | Solution |
|----------|----------------|----------|
| Lectures instables de poids | Interférences électriques | Vérifier le blindage des câbles |
| Capteur non répondant | Batterie faible / Perte de connexion | Remplacer la batterie / Vérifier la connexion WiFi |
| Dérive des mesures | Décalibration | Exécuter la routine de calibration |
| Alertes fréquentes | Seuils mal configurés | Ajuster les seuils d'alerte |

### Maintenance préventive

- Calibrer les cellules de charge tous les 3 mois
- Vérifier les batteries des capteurs sans fil mensuellement
- Nettoyer les capteurs de température tous les 6 mois
- Mettre à jour le firmware des ESP32 lors des nouvelles versions

## Consommation Énergétique

| Type de capteur | Mode actif | Mode veille | Autonomie (batterie) |
|-----------------|------------|-------------|----------------------|
| Cellule de charge | 15mA | 0.1mA | 3-6 mois |
| Sonde niveau huile | 25mA | N/A (alimenté) | N/A |
| Capteur température | 4mA | 0.01mA | 6-12 mois |

---

Pour toute question ou problème, consultez la documentation complète ou contactez l'équipe de support technique.
