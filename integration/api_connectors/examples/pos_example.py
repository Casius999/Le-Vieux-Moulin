"""Exemples d'utilisation des connecteurs pour caisses enregistreuses (POS).

Ce module illustre comment utiliser les connecteurs POS pour interagir
avec les systèmes de caisse Lightspeed et Square.
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
from integration.api_connectors.pos import LightspeedConnector, SquareConnector

# Chemins vers les fichiers de configuration
CONFIG_DIR = os.path.join(os.path.dirname(__file__), "../config")
LIGHTSPEED_CONFIG = os.path.join(CONFIG_DIR, "lightspeed_config.yaml")
SQUARE_CONFIG = os.path.join(CONFIG_DIR, "square_config.yaml")

async def lightspeed_example():
    """Exemple d'utilisation du connecteur Lightspeed."""
    # Si vous utilisez un dictionnaire de configuration directement au lieu d'un fichier
    config = {
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
        },
        "connection": {
            "timeout": 30,
            "max_retries": 3
        },
        "rate_limit": {
            "max_requests_per_minute": 60
        }
    }
    
    # Initialiser le connecteur avec un fichier de configuration
    # pos = LightspeedConnector(config_path=LIGHTSPEED_CONFIG)
    
    # Ou avec un dictionnaire de configuration
    pos = LightspeedConnector(config_dict=config)
    
    try:
        # Connecter à l'API
        print("\n[Lightspeed] Connexion à l'API...")
        await pos.connect()
        
        # Vérifier l'état de l'API
        health_status = await pos.check_health()
        print(f"[Lightspeed] État de l'API: {'OK' if health_status else 'Problème de connexion'}")
        
        # Définir la période pour les transactions (7 derniers jours)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Récupérer les transactions
        print("\n[Lightspeed] Récupération des transactions récentes...")
        transactions = await pos.get_transactions(
            start_date=start_date,
            end_date=end_date,
            status="completed",
            limit=10
        )
        
        # Afficher les résultats
        print(f"[Lightspeed] {len(transactions)} transactions trouvées")
        for i, transaction in enumerate(transactions[:3], 1):
            print(f"  Transaction {i}: ID={transaction.get('saleID')}, "  
                  f"Total={transaction.get('total')} €, "
                  f"Date={transaction.get('timeStamp')}")
        
        # Récupérer les produits
        print("\n[Lightspeed] Récupération des produits...")
        products = await pos.get_products(limit=10)
        
        print(f"[Lightspeed] {len(products)} produits trouvés")
        for i, product in enumerate(products[:3], 1):
            print(f"  Produit {i}: ID={product.get('itemID')}, "
                  f"Nom={product.get('description')}, "
                  f"Prix={product.get('defaultPrice')} €")
        
        # Récupérer les niveaux de stock
        print("\n[Lightspeed] Récupération des niveaux de stock...")
        inventory = await pos.get_inventory()
        
        print(f"[Lightspeed] {len(inventory)} entrées de stock trouvées")
        for i, item in enumerate(inventory[:3], 1):
            print(f"  Stock {i}: ID={item.get('itemID')}, "
                  f"Quantité={item.get('quantity')}")
        
    except Exception as e:
        print(f"[Lightspeed] Erreur: {str(e)}")
    finally:
        # Fermer la connexion
        await pos.disconnect()
        print("\n[Lightspeed] Déconnexion effectuée")

async def square_example():
    """Exemple d'utilisation du connecteur Square."""
    # Configuration pour Square
    config = {
        "api": {
            "base_url": "https://connect.squareup.com/",
            "location_id": "YOUR_LOCATION_ID"
        },
        "auth": {
            "method": "oauth2_client_credentials",
            "client_id": "YOUR_CLIENT_ID",
            "client_secret": "YOUR_CLIENT_SECRET",
            "token_url": "https://connect.squareup.com/oauth2/token",
            "token_path": "/path/to/tokens/square_token.json"
        },
        "connection": {
            "timeout": 20,
            "max_retries": 3
        }
    }
    
    # Initialiser le connecteur
    pos = SquareConnector(config_dict=config)
    
    try:
        # Connecter à l'API
        print("\n[Square] Connexion à l'API...")
        await pos.connect()
        
        # Vérifier l'état de l'API
        health_status = await pos.check_health()
        print(f"[Square] État de l'API: {'OK' if health_status else 'Problème de connexion'}")
        
        # Définir la période pour les transactions (7 derniers jours)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Récupérer les transactions
        print("\n[Square] Récupération des transactions récentes...")
        transactions = await pos.get_transactions(
            start_date=start_date,
            end_date=end_date,
            status="completed",
            limit=10
        )
        
        # Afficher les résultats
        print(f"[Square] {len(transactions)} transactions trouvées")
        for i, transaction in enumerate(transactions[:3], 1):
            print(f"  Transaction {i}: ID={transaction.get('id')}, "
                  f"Total=${transaction.get('total_money', {}).get('amount', 0) / 100:.2f}, "
                  f"Date={transaction.get('created_at')}")
        
        # Récupérer les produits
        print("\n[Square] Récupération des produits...")
        products = await pos.get_products(limit=10)
        
        print(f"[Square] {len(products)} produits trouvés")
        for i, product in enumerate(products[:3], 1):
            item_data = product.get('item_data', {})
            print(f"  Produit {i}: ID={product.get('id')}, "
                  f"Nom={item_data.get('name')}")
        
        # Récupérer les niveaux de stock
        print("\n[Square] Récupération des niveaux de stock...")
        inventory = await pos.get_inventory()
        
        print(f"[Square] {len(inventory)} entrées de stock trouvées")
        for i, item in enumerate(inventory[:3], 1):
            print(f"  Stock {i}: ID={item.get('catalog_object_id')}, "
                  f"Quantité={item.get('quantity')}")
        
    except Exception as e:
        print(f"[Square] Erreur: {str(e)}")
    finally:
        # Fermer la connexion
        await pos.disconnect()
        print("\n[Square] Déconnexion effectuée")

async def get_sales_summary_example():
    """Exemple de génération de résumé des ventes sur une période."""
    # Configuration pour Lightspeed
    config = {
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
    
    # Initialiser le connecteur
    pos = LightspeedConnector(config_dict=config)
    
    try:
        # Connecter à l'API
        print("\n[Sales Summary] Connexion à l'API...")
        await pos.connect()
        
        # Définir la période pour le résumé (30 derniers jours)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Récupérer le résumé des ventes
        print("\n[Sales Summary] Génération du résumé des ventes par jour...")
        sales_summary = await pos.get_sales_summary(
            start_date=start_date,
            end_date=end_date,
            group_by="day"
        )
        
        # Afficher les résultats
        print(f"\n[Sales Summary] Période: {sales_summary['period']['start']} au {sales_summary['period']['end']}")
        print(f"[Sales Summary] Total des ventes: {sales_summary['total_sales']:.2f} €")
        print(f"[Sales Summary] Nombre de transactions: {sales_summary['total_transactions']}")
        print(f"[Sales Summary] Panier moyen: {sales_summary['average_sale']:.2f} €")
        
        # Afficher les ventes par jour
        print("\n[Sales Summary] Ventes par jour:")
        if 'groups' in sales_summary:
            for date, data in list(sales_summary['groups'].items())[:5]:
                print(f"  {date}: {data['total']:.2f} € ({data['count']} transactions)")
        
    except Exception as e:
        print(f"[Sales Summary] Erreur: {str(e)}")
    finally:
        # Fermer la connexion
        await pos.disconnect()
        print("\n[Sales Summary] Déconnexion effectuée")

async def main():
    """Fonction principale exécutant tous les exemples."""
    print("=== EXEMPLES D'UTILISATION DES CONNECTEURS POS ===\n")
    
    # Exécuter l'exemple Lightspeed
    await lightspeed_example()
    
    # Exécuter l'exemple Square
    await square_example()
    
    # Exécuter l'exemple de résumé des ventes
    await get_sales_summary_example()

if __name__ == "__main__":
    # Exécuter la fonction principale de manière asynchrone
    asyncio.run(main())