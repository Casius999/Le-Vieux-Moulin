"""Exemples d'utilisation des connecteurs pour les systèmes CRM.

Ce module illustre comment utiliser les connecteurs pour interagir
avec les API des systèmes CRM (HubSpot, Zoho).
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
from integration.api_connectors.crm import HubSpotConnector, ZohoCRMConnector

# Chemins vers les fichiers de configuration
CONFIG_DIR = os.path.join(os.path.dirname(__file__), "../config")
HUBSPOT_CONFIG = os.path.join(CONFIG_DIR, "hubspot_config.yaml")
ZOHO_CONFIG = os.path.join(CONFIG_DIR, "zoho_config.yaml")

async def hubspot_example():
    """Exemple d'utilisation du connecteur HubSpot."""
    # Configuration pour HubSpot
    config = {
        "api": {
            "base_url": "https://api.hubapi.com/",
            "default_headers": {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        },
        "auth": {
            "method": "oauth2_authorization_code",
            "client_id": "YOUR_CLIENT_ID",
            "client_secret": "YOUR_CLIENT_SECRET",
            "redirect_uri": "https://levieuxmoulin.fr/oauth/callback",
            "authorization_url": "https://app.hubspot.com/oauth/authorize",
            "token_url": "https://api.hubapi.com/oauth/v1/token",
            "scope": "crm.objects.contacts.read crm.objects.contacts.write crm.objects.deals.read crm.objects.deals.write",
            "token_path": "/path/to/tokens/hubspot_token.json"
        },
        "connection": {
            "timeout": 30,
            "max_retries": 3
        }
    }
    
    # Initialiser le connecteur
    crm = HubSpotConnector(config_dict=config)
    
    try:
        # Connecter à l'API
        print("\n[HubSpot] Connexion à l'API...")
        await crm.connect()
        
        # Vérifier l'état de l'API
        health_status = await crm.check_health()
        print(f"[HubSpot] État de l'API: {'OK' if health_status else 'Problème de connexion'}")
        
        # Récupérer les contacts
        print("\n[HubSpot] Récupération des contacts...")
        contacts = await crm.get_contacts(limit=10)
        
        # Afficher les résultats
        print(f"[HubSpot] {len(contacts)} contacts trouvés")
        for i, contact in enumerate(contacts[:3], 1):
            properties = contact.get("properties", {})
            print(f"  Contact {i}: ID={contact.get('id')}, "
                  f"Nom={properties.get('firstname', '')} {properties.get('lastname', '')}, "
                  f"Email={properties.get('email', 'N/A')}, "
                  f"Téléphone={properties.get('phone', 'N/A')}")
        
        # Recherche de contacts
        print("\n[HubSpot] Recherche de contacts...")
        search_results = await crm.search_contacts(query="dupont", limit=5)
        
        print(f"[HubSpot] {len(search_results)} contacts trouvés pour la recherche 'dupont':")
        for i, contact in enumerate(search_results[:3], 1):
            properties = contact.get("properties", {})
            print(f"  Résultat {i}: {properties.get('firstname', '')} {properties.get('lastname', '')}, "
                  f"Email={properties.get('email', 'N/A')}")
        
        # Récupération des points de fidélité
        if contacts:
            contact_id = contacts[0]["id"]
            print(f"\n[HubSpot] Récupération des points de fidélité pour le contact {contact_id}...")
            loyalty = await crm.get_loyalty_points(contact_id)
            
            print(f"[HubSpot] Points de fidélité:")
            print(f"  Contact ID: {loyalty['contact_id']}")
            print(f"  Points: {loyalty['points']}")
            print(f"  Dernière visite: {loyalty['last_visit'] or 'Jamais'}")
            
            # Simulation de mise à jour des points
            print("\n[HubSpot] Simulation de mise à jour des points de fidélité...")
            points_to_add = 10
            print(f"  Ajout de {points_to_add} points au contact {contact_id}")
            print(f"  Points actuels: {loyalty['points']}")
            print(f"  Nouveaux points: {loyalty['points'] + points_to_add}")
            
            # Pour réellement mettre à jour les points, décommentez le code suivant:
            # updated_loyalty = await crm.update_loyalty_points(
            #     contact_id=contact_id,
            #     points=points_to_add,
            #     reason="Repas du 12/04/2025"
            # )
            # print(f"  Points mis à jour: {updated_loyalty['new_points']}")
        
    except Exception as e:
        print(f"[HubSpot] Erreur: {str(e)}")
    finally:
        # Fermer la connexion
        await crm.disconnect()
        print("\n[HubSpot] Déconnexion effectuée")

async def zoho_example():
    """Exemple d'utilisation du connecteur Zoho CRM."""
    # Configuration pour Zoho CRM
    config = {
        "api": {
            "base_url": "https://www.zohoapis.eu/",
            "default_headers": {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        },
        "auth": {
            "method": "oauth2_authorization_code",
            "client_id": "YOUR_CLIENT_ID",
            "client_secret": "YOUR_CLIENT_SECRET",
            "redirect_uri": "https://levieuxmoulin.fr/oauth/callback",
            "authorization_url": "https://accounts.zoho.eu/oauth/v2/auth",
            "token_url": "https://accounts.zoho.eu/oauth/v2/token",
            "scope": "ZohoCRM.modules.ALL",
            "token_path": "/path/to/tokens/zoho_token.json"
        },
        "connection": {
            "timeout": 30,
            "max_retries": 3
        }
    }
    
    # Initialiser le connecteur
    crm = ZohoCRMConnector(config_dict=config)
    
    try:
        # Connecter à l'API
        print("\n[Zoho] Connexion à l'API...")
        await crm.connect()
        
        # Vérifier l'état de l'API
        health_status = await crm.check_health()
        print(f"[Zoho] État de l'API: {'OK' if health_status else 'Problème de connexion'}")
        
        # Récupérer les contacts
        print("\n[Zoho] Récupération des contacts...")
        contacts = await crm.get_contacts(limit=10)
        
        # Afficher les résultats
        print(f"[Zoho] {len(contacts)} contacts trouvés")
        for i, contact in enumerate(contacts[:3], 1):
            print(f"  Contact {i}: ID={contact.get('id')}, "
                  f"Nom={contact.get('First_Name', '')} {contact.get('Last_Name', '')}, "
                  f"Email={contact.get('Email', 'N/A')}, "
                  f"Téléphone={contact.get('Phone', 'N/A')}")
        
        # Récupérer les transactions (deals)
        print("\n[Zoho] Récupération des transactions récentes...")
        start_date = datetime.now() - timedelta(days=30)
        
        if contacts:
            contact_id = contacts[0]["id"]
            transactions = await crm.get_transactions(
                contact_id=contact_id,
                start_date=start_date
            )
            
            print(f"[Zoho] {len(transactions)} transactions trouvées pour le contact {contact_id}:")
            for i, transaction in enumerate(transactions[:3], 1):
                print(f"  Transaction {i}: ID={transaction.get('id')}, "
                      f"Nom={transaction.get('Deal_Name')}, "
                      f"Montant={transaction.get('Amount')} €, "
                      f"Date={transaction.get('Closing_Date')}")
        
    except Exception as e:
        print(f"[Zoho] Erreur: {str(e)}")
    finally:
        # Fermer la connexion
        await crm.disconnect()
        print("\n[Zoho] Déconnexion effectuée")

async def loyalty_integration_example():
    """Exemple d'intégration de fidélité client avec synchronisation POS <-> CRM."""
    # Configuration pour HubSpot
    hubspot_config = {
        "api": {
            "base_url": "https://api.hubapi.com/",
        },
        "auth": {
            "method": "oauth2_authorization_code",
            "client_id": "YOUR_CLIENT_ID",
            "client_secret": "YOUR_CLIENT_SECRET",
            "redirect_uri": "https://levieuxmoulin.fr/oauth/callback",
            "authorization_url": "https://app.hubspot.com/oauth/authorize",
            "token_url": "https://api.hubapi.com/oauth/v1/token",
            "scope": "crm.objects.contacts.read crm.objects.contacts.write",
            "token_path": "/path/to/tokens/hubspot_token.json"
        }
    }
    
    # Configuration pour Lightspeed
    lightspeed_config = {
        "api": {
            "base_url": "https://api.lightspeedapp.com/API/",
            "account_id": "YOUR_ACCOUNT_ID"
        },
        "auth": {
            "method": "oauth2_authorization_code",
            "client_id": "YOUR_CLIENT_ID",
            "client_secret": "YOUR_CLIENT_SECRET",
            "redirect_uri": "https://levieuxmoulin.fr/oauth/callback",
            "authorization_url": "https://cloud.lightspeedapp.com/oauth/authorize.php",
            "token_url": "https://cloud.lightspeedapp.com/oauth/access_token.php",
            "scope": "employee:inventory employee:sales",
            "token_path": "/path/to/tokens/lightspeed_token.json"
        }
    }
    
    # Initialiser les connecteurs
    from integration.api_connectors.crm import HubSpotConnector
    from integration.api_connectors.pos import LightspeedConnector
    
    crm = HubSpotConnector(config_dict=hubspot_config)
    pos = LightspeedConnector(config_dict=lightspeed_config)
    
    try:
        # Connecter aux APIs
        print("\n[Loyalty Integration] Connexion aux APIs...")
        await crm.connect()
        await pos.connect()
        
        print("[Loyalty Integration] Connexion établie")
        
        # Supposons que nous avons un client qui vient de passer une commande
        email = "jean.dupont@example.com"
        amount = 75.80
        
        # 1. Rechercher le client dans le CRM par email
        print(f"\n[Loyalty Integration] Recherche du client avec l'email {email}...")
        contacts = await crm.get_contacts(filters={"email": {"operator": "EQ", "value": email}})
        
        contact_id = None
        if contacts:
            contact_id = contacts[0]["id"]
            properties = contacts[0].get("properties", {})
            print(f"[Loyalty Integration] Client trouvé: {properties.get('firstname', '')} {properties.get('lastname', '')}")
            
            # 2. Récupérer les points de fidélité actuels
            loyalty = await crm.get_loyalty_points(contact_id)
            current_points = loyalty["points"]
            print(f"[Loyalty Integration] Points de fidélité actuels: {current_points}")
            
            # 3. Calculer les nouveaux points (1 point par euro dépensé)
            points_to_add = int(amount)  # Arrondi à l'entier inférieur
            new_points = current_points + points_to_add
            print(f"[Loyalty Integration] Ajout de {points_to_add} points pour un achat de {amount:.2f} €")
            print(f"[Loyalty Integration] Nouveaux points: {new_points}")
            
            # 4. Mise à jour des points de fidélité (simulé)
            print("\n[Loyalty Integration] Simulation de mise à jour des points de fidélité...")
            
            # Pour réellement mettre à jour les points, décommentez le code suivant:
            # updated_loyalty = await crm.update_loyalty_points(
            #     contact_id=contact_id,
            #     points=points_to_add,
            #     reason=f"Achat du {datetime.now().strftime('%d/%m/%Y')} - {amount:.2f} €"
            # )
            
            # 5. Vérifier les règles de fidélité (exemple: offre spéciale à 500 points)
            threshold = 500
            if new_points >= threshold:
                print(f"\n[Loyalty Integration] Le client a atteint {new_points} points!")
                print(f"[Loyalty Integration] Action: Envoi d'une offre spéciale pour récompenser sa fidélité")
                
                # Enregistrement de l'action dans le CRM (simulé)
                print("[Loyalty Integration] Création d'une note dans le CRM...")
                note_content = f"Client fidèle ayant atteint {new_points} points. Offre spéciale envoyée le {datetime.now().strftime('%d/%m/%Y')}.")
                
                # Pour réellement créer la note, décommentez le code suivant:
                # await crm.create_note(
                #     contact_id=contact_id,
                #     content=note_content,
                #     type="loyalty_reward"
                # )
        else:
            print(f"[Loyalty Integration] Aucun client trouvé avec l'email {email}")
            
            # Création d'un nouveau contact (simulé)
            print("\n[Loyalty Integration] Simulation de création d'un nouveau contact...")
            new_contact_data = {
                "email": email,
                "firstName": "Jean",
                "lastName": "Dupont",
                "phone": "+33612345678",
                "loyalty_points": int(amount)  # Points initiaux basés sur l'achat
            }
            
            print(f"[Loyalty Integration] Nouveau contact: {new_contact_data['firstName']} {new_contact_data['lastName']}")
            print(f"[Loyalty Integration] Points initiaux: {new_contact_data['loyalty_points']}")
            
            # Pour réellement créer le contact, décommentez le code suivant:
            # new_contact = await crm.create_contact(new_contact_data)
            # contact_id = new_contact["id"]
            # print(f"[Loyalty Integration] Nouveau contact créé avec ID: {contact_id}")
        
        # 6. Enregistrer la transaction dans le CRM (simulé)
        if contact_id:
            print("\n[Loyalty Integration] Enregistrement de la transaction dans le CRM...")
            transaction_data = {
                "amount": amount,
                "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "name": f"Repas du {datetime.now().strftime('%d/%m/%Y')}",
                "description": "Menu du jour + dessert",
                "items": [
                    {"name": "Menu du jour", "quantity": 2, "price": 29.90},
                    {"name": "Dessert", "quantity": 2, "price": 8.00}
                ]
            }
            
            print(f"[Loyalty Integration] Transaction: {transaction_data['name']}")
            print(f"[Loyalty Integration] Montant: {transaction_data['amount']:.2f} €")
            print(f"[Loyalty Integration] Date: {transaction_data['date']}")
            
            # Pour réellement enregistrer la transaction, décommentez le code suivant:
            # transaction = await crm.create_transaction(
            #     contact_id=contact_id,
            #     data=transaction_data
            # )
            # print(f"[Loyalty Integration] Transaction enregistrée avec ID: {transaction.get('id')}")
        
    except Exception as e:
        print(f"[Loyalty Integration] Erreur: {str(e)}")
    finally:
        # Fermer les connexions
        await crm.disconnect()
        await pos.disconnect()
        print("\n[Loyalty Integration] Déconnexion effectuée")

async def main():
    """Fonction principale exécutant tous les exemples."""
    print("=== EXEMPLES D'UTILISATION DES CONNECTEURS CRM ===\n")
    
    # Exécuter l'exemple HubSpot
    await hubspot_example()
    
    # Exécuter l'exemple Zoho
    await zoho_example()
    
    # Exécuter l'exemple d'intégration de fidélité
    await loyalty_integration_example()

if __name__ == "__main__":
    # Exécuter la fonction principale de manière asynchrone
    asyncio.run(main())