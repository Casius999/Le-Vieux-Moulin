"""Exemples d'utilisation des connecteurs pour les fournisseurs.

Ce module illustre comment utiliser les connecteurs pour interagir
avec les API des fournisseurs (Metro, Transgourmet, Pomona).
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
from integration.api_connectors.suppliers import MetroConnector, TransgourmetConnector, PomonaConnector

# Chemins vers les fichiers de configuration
CONFIG_DIR = os.path.join(os.path.dirname(__file__), "../config")
METRO_CONFIG = os.path.join(CONFIG_DIR, "metro_config.yaml")
TRANSGOURMET_CONFIG = os.path.join(CONFIG_DIR, "transgourmet_config.yaml")
POMONA_CONFIG = os.path.join(CONFIG_DIR, "pomona_config.yaml")

async def metro_example():
    """Exemple d'utilisation du connecteur Metro."""
    # Configuration pour Metro
    config = {
        "api": {
            "base_url": "https://api.metro.fr/",
            "client_number": "YOUR_CLIENT_NUMBER"
        },
        "auth": {
            "method": "api_key",
            "api_key": "YOUR_API_KEY",
            "header_name": "X-API-KEY"
        },
        "connection": {
            "timeout": 30,
            "max_retries": 3
        }
    }
    
    # Initialiser le connecteur
    supplier = MetroConnector(config_dict=config)
    
    try:
        # Connecter à l'API
        print("\n[Metro] Connexion à l'API...")
        await supplier.connect()
        
        # Vérifier l'état de l'API
        health_status = await supplier.check_health()
        print(f"[Metro] État de l'API: {'OK' if health_status else 'Problème de connexion'}")
        
        # Récupérer le catalogue
        print("\n[Metro] Récupération du catalogue de produits...")
        products = await supplier.get_catalog(category="DAIRY", limit=10)
        
        # Afficher les résultats
        print(f"[Metro] {len(products)} produits trouvés dans la catégorie 'DAIRY'")
        for i, product in enumerate(products[:3], 1):
            print(f"  Produit {i}: ID={product.get('id')}, "
                  f"Nom={product.get('name')}, "
                  f"Prix={product.get('price')} €")
        
        # Vérifier la disponibilité des produits
        if products:
            product_ids = [product["id"] for product in products[:5]]
            print("\n[Metro] Vérification de la disponibilité des produits...")
            availability = await supplier.check_product_availability(product_ids)
            
            print("[Metro] Résultats de disponibilité:")
            for product_id, status in availability.items():
                print(f"  Produit {product_id}: {'Disponible' if status.get('available') else 'Non disponible'}, "
                      f"Stock: {status.get('quantity')}")
        
        # Préparer une commande d'exemple
        if products:
            print("\n[Metro] Préparation d'une commande d'exemple...")
            order_items = [
                {"id": products[0]["id"], "quantity": 5, "unit": "PC"},
                {"id": products[1]["id"], "quantity": 2, "unit": "KG"}
            ]
            
            # Date de livraison souhaitée (demain)
            delivery_date = datetime.now() + timedelta(days=1)
            
            # Créer la commande (simulée, ne pas exécuter réellement)
            print("[Metro] Simulation de création de commande...")
            print(f"  Articles: {len(order_items)} produits")
            print(f"  Date de livraison: {delivery_date.strftime('%Y-%m-%d')}")
            print("  Note: Livraison avant 10h si possible")
            
            # Pour réellement créer la commande, décommentez le code suivant:
            # order = await supplier.create_order(
            #     items=order_items,
            #     delivery_date=delivery_date,
            #     notes="Livraison avant 10h si possible"
            # )
            # print(f"[Metro] Commande créée avec succès: ID={order.get('order_id')}")
        
        # Récupérer le planning de livraison
        print("\n[Metro] Récupération du planning de livraison...")
        delivery_schedule = await supplier.get_delivery_schedule()
        
        print("[Metro] Planning de livraison:")
        days = delivery_schedule.get("delivery_days", [])
        for day in days[:3]:
            print(f"  {day['day']}: {day['time_slots']}")
        
    except Exception as e:
        print(f"[Metro] Erreur: {str(e)}")
    finally:
        # Fermer la connexion
        await supplier.disconnect()
        print("\n[Metro] Déconnexion effectuée")

async def transgourmet_example():
    """Exemple d'utilisation du connecteur Transgourmet."""
    # Configuration pour Transgourmet
    config = {
        "api": {
            "base_url": "https://api.transgourmet.fr/",
            "customer_id": "YOUR_CUSTOMER_ID"
        },
        "auth": {
            "method": "oauth2_client_credentials",
            "client_id": "YOUR_CLIENT_ID",
            "client_secret": "YOUR_CLIENT_SECRET",
            "token_url": "https://api.transgourmet.fr/api/oauth/token",
            "token_path": "/path/to/tokens/transgourmet_token.json"
        },
        "connection": {
            "timeout": 30,
            "max_retries": 3
        }
    }
    
    # Initialiser le connecteur
    supplier = TransgourmetConnector(config_dict=config)
    
    try:
        # Connecter à l'API
        print("\n[Transgourmet] Connexion à l'API...")
        await supplier.connect()
        
        # Vérifier l'état de l'API
        health_status = await supplier.check_health()
        print(f"[Transgourmet] État de l'API: {'OK' if health_status else 'Problème de connexion'}")
        
        # Récupérer le catalogue
        print("\n[Transgourmet] Récupération du catalogue de produits...")
        products = await supplier.get_catalog(category="FRUITS_LEGUMES", limit=10)
        
        # Afficher les résultats
        print(f"[Transgourmet] {len(products)} produits trouvés dans la catégorie 'FRUITS_LEGUMES'")
        for i, product in enumerate(products[:3], 1):
            print(f"  Produit {i}: ID={product.get('productId')}, "
                  f"Nom={product.get('name')}, "
                  f"Prix={product.get('price')} €")
        
        # Récupérer les commandes récentes
        print("\n[Transgourmet] Récupération des commandes récentes...")
        start_date = datetime.now() - timedelta(days=30)
        orders = await supplier.get_orders(start_date=start_date, limit=5)
        
        print(f"[Transgourmet] {len(orders)} commandes récentes trouvées")
        for i, order in enumerate(orders[:3], 1):
            print(f"  Commande {i}: ID={order.get('id')}, "
                  f"Date={order.get('date')}, "
                  f"Statut={order.get('status')}, "
                  f"Total={order.get('total')} €")
    
    except Exception as e:
        print(f"[Transgourmet] Erreur: {str(e)}")
    finally:
        # Fermer la connexion
        await supplier.disconnect()
        print("\n[Transgourmet] Déconnexion effectuée")

async def pomona_example():
    """Exemple d'utilisation du connecteur Pomona."""
    # Configuration pour Pomona
    config = {
        "api": {
            "base_url": "https://api.pomona.fr/",
            "establishment_code": "YOUR_ESTABLISHMENT_CODE"
        },
        "auth": {
            "method": "basic_auth",
            "username": "YOUR_USERNAME",
            "password": "YOUR_PASSWORD"
        },
        "connection": {
            "timeout": 30,
            "max_retries": 3
        }
    }
    
    # Initialiser le connecteur
    supplier = PomonaConnector(config_dict=config)
    
    try:
        # Connecter à l'API
        print("\n[Pomona] Connexion à l'API...")
        await supplier.connect()
        
        # Vérifier l'état de l'API
        health_status = await supplier.check_health()
        print(f"[Pomona] État de l'API: {'OK' if health_status else 'Problème de connexion'}")
        
        # Récupérer le catalogue
        print("\n[Pomona] Récupération du catalogue de produits...")
        products = await supplier.get_catalog(category="VIANDES", limit=10)
        
        # Afficher les résultats
        print(f"[Pomona] {len(products)} produits trouvés dans la catégorie 'VIANDES'")
        for i, product in enumerate(products[:3], 1):
            print(f"  Produit {i}: ID={product.get('product_code')}, "
                  f"Nom={product.get('name')}, "
                  f"Prix={product.get('price')} €")
        
        # Récupérer les informations du compte
        print("\n[Pomona] Récupération des informations du compte...")
        account_info = await supplier.get_account_info()
        
        print("[Pomona] Informations du compte:")
        print(f"  Établissement: {account_info.get('establishment_name')}")
        print(f"  Solde: {account_info.get('balance')} €")
        print(f"  Limite de crédit: {account_info.get('credit_limit')} €")
        
    except Exception as e:
        print(f"[Pomona] Erreur: {str(e)}")
    finally:
        # Fermer la connexion
        await supplier.disconnect()
        print("\n[Pomona] Déconnexion effectuée")

async def automation_example():
    """Exemple d'automatisation des commandes."""
    # Configuration pour Metro
    config = {
        "api": {
            "base_url": "https://api.metro.fr/",
            "client_number": "YOUR_CLIENT_NUMBER"
        },
        "auth": {
            "method": "api_key",
            "api_key": "YOUR_API_KEY"
        }
    }
    
    # Initialiser le connecteur
    supplier = MetroConnector(config_dict=config)
    
    try:
        # Connecter à l'API
        print("\n[Automation] Connexion à l'API...")
        await supplier.connect()
        
        # Exemple d'automatisation des commandes basée sur les niveaux de stock
        print("\n[Automation] Simulation d'automatisation des commandes...")
        
        # 1. Supposons que nous avons une liste de produits à surveiller avec leurs seuils
        monitored_products = [
            {"id": "P123456", "name": "Farine T45", "threshold": 10, "order_amount": 25, "unit": "KG"},
            {"id": "P234567", "name": "Huile d'olive", "threshold": 5, "order_amount": 10, "unit": "L"},
            {"id": "P345678", "name": "Mozzarella", "threshold": 8, "order_amount": 15, "unit": "KG"},
        ]
        
        # 2. Supposons que nous avons vérifié les niveaux de stock actuels (simulé)
        current_stocks = {
            "P123456": 7,  # Sous le seuil
            "P234567": 12,  # Au-dessus du seuil
            "P345678": 6,  # Sous le seuil
        }
        
        # 3. Identifier les produits à commander (sous le seuil)
        products_to_order = []
        for product in monitored_products:
            current_stock = current_stocks.get(product["id"], 0)
            print(f"  Produit: {product['name']}, Stock actuel: {current_stock}, Seuil: {product['threshold']}")
            
            if current_stock < product["threshold"]:
                print(f"  -> Niveau sous le seuil, ajout à la commande: {product['order_amount']} {product['unit']}")
                products_to_order.append({
                    "id": product["id"],
                    "quantity": product["order_amount"],
                    "unit": product["unit"]
                })
        
        # 4. Créer la commande si nécessaire
        if products_to_order:
            print("\n[Automation] Création d'une commande automatique:")
            for item in products_to_order:
                product_name = next((p["name"] for p in monitored_products if p["id"] == item["id"]), "Inconnu")
                print(f"  - {product_name}: {item['quantity']} {item['unit']}")
            
            # Pour réellement créer la commande, décommentez le code suivant:
            # delivery_date = datetime.now() + timedelta(days=1)
            # order = await supplier.create_order(
            #     items=products_to_order,
            #     delivery_date=delivery_date,
            #     notes="Commande automatique générée par le système"
            # )
            # print(f"[Automation] Commande automatique créée: ID={order.get('order_id')}")
        else:
            print("\n[Automation] Aucun produit n'a besoin d'être commandé.")
    
    except Exception as e:
        print(f"[Automation] Erreur: {str(e)}")
    finally:
        # Fermer la connexion
        await supplier.disconnect()
        print("\n[Automation] Déconnexion effectuée")

async def main():
    """Fonction principale exécutant tous les exemples."""
    print("=== EXEMPLES D'UTILISATION DES CONNECTEURS FOURNISSEURS ===\n")
    
    # Exécuter l'exemple Metro
    await metro_example()
    
    # Exécuter l'exemple Transgourmet
    await transgourmet_example()
    
    # Exécuter l'exemple Pomona
    await pomona_example()
    
    # Exécuter l'exemple d'automatisation
    await automation_example()

if __name__ == "__main__":
    # Exécuter la fonction principale de manière asynchrone
    asyncio.run(main())