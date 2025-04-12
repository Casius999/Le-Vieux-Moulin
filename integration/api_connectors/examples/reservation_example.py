"""Exemples d'utilisation des connecteurs pour les plateformes de réservation.

Ce module illustre comment utiliser les connecteurs pour interagir
avec les API des plateformes de réservation (TheFork, OpenTable).
"""

import asyncio
import os
from datetime import datetime, timedelta
import logging

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Importer les connecteurs
from integration.api_connectors.reservation import TheForkConnector, OpenTableConnector

# Chemins vers les fichiers de configuration
CONFIG_DIR = os.path.join(os.path.dirname(__file__), "../config")
THEFORK_CONFIG = os.path.join(CONFIG_DIR, "thefork_config.yaml")
OPENTABLE_CONFIG = os.path.join(CONFIG_DIR, "opentable_config.yaml")

async def thefork_example():
    """Exemple d'utilisation du connecteur TheFork."""
    # Configuration pour TheFork
    config = {
        "api": {
            "base_url": "https://api.thefork.com/",
            "restaurant_id": "YOUR_RESTAURANT_ID"
        },
        "auth": {
            "method": "oauth2_client_credentials",
            "client_id": "YOUR_CLIENT_ID",
            "client_secret": "YOUR_CLIENT_SECRET",
            "token_url": "https://api.thefork.com/oauth/token",
            "scope": "public_api reservations",
            "token_path": "/path/to/tokens/thefork_token.json"
        },
        "connection": {
            "timeout": 30,
            "max_retries": 3
        }
    }
    
    # Initialiser le connecteur
    reservation = TheForkConnector(config_dict=config)
    
    try:
        # Connecter à l'API
        print("\n[TheFork] Connexion à l'API...")
        await reservation.connect()
        
        # Vérifier l'état de l'API
        health_status = await reservation.check_health()
        print(f"[TheFork] État de l'API: {'OK' if health_status else 'Problème de connexion'}")
        
        # Définir la période pour les réservations (aujourd'hui + 7 jours)
        start_date = datetime.now()
        end_date = start_date + timedelta(days=7)
        
        # Récupérer les réservations
        print("\n[TheFork] Récupération des réservations...")
        reservations = await reservation.get_reservations(
            start_date=start_date,
            end_date=end_date,
            status="confirmed",
            limit=10
        )
        
        # Afficher les résultats
        print(f"[TheFork] {len(reservations)} réservations trouvées")
        for i, booking in enumerate(reservations[:3], 1):
            print(f"  Réservation {i}: ID={booking.get('id')}, "
                  f"Date={booking.get('date')} {booking.get('time')}, "
                  f"Couverts={booking.get('partySize')}, "
                  f"Client={booking.get('customer', {}).get('firstName')} {booking.get('customer', {}).get('lastName')}")
        
        # Vérifier les disponibilités pour demain
        tomorrow = datetime.now() + timedelta(days=1)
        print(f"\n[TheFork] Vérification des disponibilités pour le {tomorrow.strftime('%Y-%m-%d')}...")
        availabilities = await reservation.get_availability(
            date=tomorrow,
            party_size=4,
            time_start="18:00",
            time_end="22:00"
        )
        
        # Afficher les créneaux disponibles
        print(f"[TheFork] {len(availabilities)} créneaux disponibles:")
        for i, slot in enumerate(availabilities[:5], 1):
            print(f"  Créneau {i}: {slot.get('time')}, "
                  f"Places disponibles: {slot.get('seats')}, "
                  f"Tables: {slot.get('tables')}")
        
        # Rechercher un client
        print("\n[TheFork] Recherche d'un client...")
        customers = await reservation.search_customers(search_term="dupont", limit=5)
        
        # Afficher les résultats de la recherche
        print(f"[TheFork] {len(customers)} clients trouvés:")
        for i, customer in enumerate(customers[:3], 1):
            print(f"  Client {i}: ID={customer.get('id')}, "
                  f"Nom={customer.get('firstName')} {customer.get('lastName')}, "
                  f"Email={customer.get('email')}, "
                  f"Téléphone={customer.get('phoneNumber')}")
        
        # Obtenir les informations du restaurant
        print("\n[TheFork] Récupération des informations du restaurant...")
        restaurant_info = await reservation.get_restaurant_info()
        
        print("[TheFork] Informations du restaurant:")
        print(f"  Nom: {restaurant_info.get('name')}")
        print(f"  Adresse: {restaurant_info.get('address', {}).get('street')}, "
              f"{restaurant_info.get('address', {}).get('postalCode')} "
              f"{restaurant_info.get('address', {}).get('city')}")
        print(f"  Capacité: {restaurant_info.get('capacity')} couverts")
        print(f"  Note: {restaurant_info.get('rating')}/10")
        
    except Exception as e:
        print(f"[TheFork] Erreur: {str(e)}")
    finally:
        # Fermer la connexion
        await reservation.disconnect()
        print("\n[TheFork] Déconnexion effectuée")

async def opentable_example():
    """Exemple d'utilisation du connecteur OpenTable."""
    # Configuration pour OpenTable
    config = {
        "api": {
            "base_url": "https://api.opentable.com/",
            "restaurant_id": "YOUR_RESTAURANT_ID"
        },
        "auth": {
            "method": "oauth2_client_credentials",
            "client_id": "YOUR_CLIENT_ID",
            "client_secret": "YOUR_CLIENT_SECRET",
            "token_url": "https://oauth.opentable.com/v3/token",
            "scope": "reservations.read reservations.write availability.read availability.write",
            "token_path": "/path/to/tokens/opentable_token.json"
        },
        "connection": {
            "timeout": 20,
            "max_retries": 3
        }
    }
    
    # Initialiser le connecteur
    reservation = OpenTableConnector(config_dict=config)
    
    try:
        # Connecter à l'API
        print("\n[OpenTable] Connexion à l'API...")
        await reservation.connect()
        
        # Vérifier l'état de l'API
        health_status = await reservation.check_health()
        print(f"[OpenTable] État de l'API: {'OK' if health_status else 'Problème de connexion'}")
        
        # Définir la période pour les réservations (aujourd'hui + 7 jours)
        start_date = datetime.now()
        end_date = start_date + timedelta(days=7)
        
        # Récupérer les réservations
        print("\n[OpenTable] Récupération des réservations...")
        reservations = await reservation.get_reservations(
            start_date=start_date,
            end_date=end_date,
            status="confirmed",
            limit=10
        )
        
        # Afficher les résultats
        print(f"[OpenTable] {len(reservations)} réservations trouvées")
        for i, booking in enumerate(reservations[:3], 1):
            print(f"  Réservation {i}: ID={booking.get('id')}, "
                  f"Date={booking.get('date')} {booking.get('time')}, "
                  f"Couverts={booking.get('party_size')}, "
                  f"Client={booking.get('customer', {}).get('first_name')} {booking.get('customer', {}).get('last_name')}")
        
        # Vérifier les disponibilités pour demain
        tomorrow = datetime.now() + timedelta(days=1)
        print(f"\n[OpenTable] Vérification des disponibilités pour le {tomorrow.strftime('%Y-%m-%d')}...")
        availabilities = await reservation.get_availability(
            date=tomorrow,
            party_size=4,
            time_start="18:00",
            time_end="22:00"
        )
        
        # Afficher les créneaux disponibles
        print(f"[OpenTable] {len(availabilities)} créneaux disponibles:")
        for i, slot in enumerate(availabilities[:5], 1):
            print(f"  Créneau {i}: {slot.get('time')}, "
                  f"Places disponibles: {slot.get('available_seats')}, "
                  f"Tables: {slot.get('table_combination')}")
    
    except Exception as e:
        print(f"[OpenTable] Erreur: {str(e)}")
    finally:
        # Fermer la connexion
        await reservation.disconnect()
        print("\n[OpenTable] Déconnexion effectuée")

async def create_reservation_example():
    """Exemple de création d'une réservation."""
    # Configuration pour TheFork
    config = {
        "api": {
            "base_url": "https://api.thefork.com/",
            "restaurant_id": "YOUR_RESTAURANT_ID"
        },
        "auth": {
            "method": "oauth2_client_credentials",
            "client_id": "YOUR_CLIENT_ID",
            "client_secret": "YOUR_CLIENT_SECRET",
            "token_url": "https://api.thefork.com/oauth/token",
            "scope": "public_api reservations",
            "token_path": "/path/to/tokens/thefork_token.json"
        }
    }
    
    # Initialiser le connecteur
    reservation = TheForkConnector(config_dict=config)
    
    try:
        # Connecter à l'API
        print("\n[Create Reservation] Connexion à l'API...")
        await reservation.connect()
        
        # Paramètres de la réservation
        tomorrow = datetime.now() + timedelta(days=1)
        reservation_date = tomorrow.strftime("%Y-%m-%d")
        reservation_time = "20:00"
        party_size = 4
        
        # Données du client
        customer_data = {
            "firstName": "Jean",
            "lastName": "Dupont",
            "email": "jean.dupont@example.com",
            "phoneNumber": "+33612345678"
        }
        
        # Préparer les données de la réservation
        reservation_data = {
            "date": reservation_date,
            "time": reservation_time,
            "partySize": party_size,
            "customer": customer_data,
            "notes": "Table près de la fenêtre si possible. Anniversaire de mariage.",
            "source": "PHONE"  # Réservation par téléphone
        }
        
        # Simulation de création de réservation
        print("\n[Create Reservation] Simulation de création d'une réservation...")
        print(f"  Date: {reservation_date} {reservation_time}")
        print(f"  Couverts: {party_size}")
        print(f"  Client: {customer_data['firstName']} {customer_data['lastName']}")
        print(f"  Email: {customer_data['email']}")
        print(f"  Téléphone: {customer_data['phoneNumber']}")
        print(f"  Notes: {reservation_data['notes']}")
        
        # Pour réellement créer la réservation, décommentez le code suivant:
        # booking = await reservation.create_reservation(reservation_data)
        # print(f"\n[Create Reservation] Réservation créée avec succès:")
        # print(f"  ID: {booking.get('id')}")
        # print(f"  Statut: {booking.get('status')}")
        # print(f"  Table assignée: {booking.get('table', 'Non assignée')}")
        
    except Exception as e:
        print(f"[Create Reservation] Erreur: {str(e)}")
    finally:
        # Fermer la connexion
        await reservation.disconnect()
        print("\n[Create Reservation] Déconnexion effectuée")

async def main():
    """Fonction principale exécutant tous les exemples."""
    print("=== EXEMPLES D'UTILISATION DES CONNECTEURS DE RÉSERVATION ===\n")
    
    # Exécuter l'exemple TheFork
    await thefork_example()
    
    # Exécuter l'exemple OpenTable
    await opentable_example()
    
    # Exécuter l'exemple de création de réservation
    await create_reservation_example()

if __name__ == "__main__":
    # Exécuter la fonction principale de manière asynchrone
    asyncio.run(main())