# Documentation du Module de Comptabilité Avancé - Le Vieux Moulin

## Table des matières

1. [Introduction](#introduction)
2. [Architecture du module](#architecture-du-module)
   - [Vue d'ensemble](#vue-densemble)
   - [Sources de données](#sources-de-données)
   - [Flux de données](#flux-de-données)
3. [Collecte et consolidation des données](#collecte-et-consolidation-des-données)
   - [Caisse enregistreuse (POS)](#caisse-enregistreuse-pos)
   - [Gestion des stocks](#gestion-des-stocks)
   - [Commandes fournisseurs](#commandes-fournisseurs)
   - [Réservations](#réservations)
   - [Données RH et paie](#données-rh-et-paie)
   - [Campagnes marketing](#campagnes-marketing)
4. [Mécanismes d'agrégation et de calcul](#mécanismes-dagrégation-et-de-calcul)
   - [Chiffre d'affaires](#chiffre-daffaires)
   - [Marge brute et nette](#marge-brute-et-nette)
   - [Coûts d'exploitation](#coûts-dexploitation)
   - [Rentabilité par période](#rentabilité-par-période)
   - [Analyse des coûts par catégorie](#analyse-des-coûts-par-catégorie)
   - [Prévisions financières](#prévisions-financières)
5. [Génération automatique des rapports](#génération-automatique-des-rapports)
   - [Types de rapports disponibles](#types-de-rapports-disponibles)
   - [Format des rapports](#format-des-rapports)
   - [Programmation et automatisation](#programmation-et-automatisation)
   - [Notifications et distribution](#notifications-et-distribution)
6. [Vérification d'intégrité des données](#vérification-dintégrité-des-données)
   - [Contrôles automatiques](#contrôles-automatiques)
   - [Détection d'anomalies](#détection-danomalies)
   - [Réconciliation des données](#réconciliation-des-données)
7. [Exemples de rapports financiers](#exemples-de-rapports-financiers)
   - [Rapport journalier](#rapport-journalier)
   - [Rapport hebdomadaire](#rapport-hebdomadaire)
   - [Rapport mensuel](#rapport-mensuel)
   - [Rapport trimestriel](#rapport-trimestriel)
   - [Rapport annuel](#rapport-annuel)
   - [Analyse comparative](#analyse-comparative)
8. [Intégration avec d'autres modules](#intégration-avec-dautres-modules)
   - [Interface avec le serveur central](#interface-avec-le-serveur-central)
   - [API REST](#api-rest)
   - [Webhooks](#webhooks)
   - [Format des données échangées](#format-des-données-échangées)
9. [Sécurité des données](#sécurité-des-données)
   - [Chiffrement](#chiffrement)
   - [Contrôle d'accès](#contrôle-daccès)
   - [Traçabilité](#traçabilité)
10. [Annexes](#annexes)
    - [Plan comptable](#plan-comptable)
    - [Codes TVA](#codes-tva)
    - [Formules de calcul détaillées](#formules-de-calcul-détaillées)

## Introduction

Le module de comptabilité avancé du système "Le Vieux Moulin" est conçu pour automatiser intégralement le processus de comptabilité du restaurant, en réduisant au strict minimum l'intervention humaine. Il collecte et consolide automatiquement les données financières et opérationnelles provenant de tous les autres modules du système, génère des rapports détaillés et des tableaux de bord financiers, vérifie l'intégrité et la cohérence des données, et exporte ces informations dans différents formats pour le comptable.

Ce module s'inscrit dans la stratégie globale d'automatisation du restaurant, visant à:
- Réduire les erreurs humaines dans la saisie et le traitement des données comptables
- Fournir des informations financières en temps réel pour une prise de décision éclairée
- Simplifier et accélérer le travail du comptable externe
- Assurer la conformité avec les normes comptables et fiscales françaises
- Permettre une analyse détaillée de la performance financière de l'établissement

## Architecture du module

### Vue d'ensemble

Le module de comptabilité est conçu selon une architecture modulaire à plusieurs couches:

1. **Couche d'acquisition de données**: Collecte les données depuis les différentes sources (API, fichiers exports, etc.)
2. **Couche de traitement**: Normalise, valide et consolide les données brutes
3. **Couche d'analyse**: Applique les règles comptables et calcule les indicateurs financiers
4. **Couche de présentation**: Génère les rapports et tableaux de bord
5. **Couche d'exportation**: Produit les fichiers aux formats requis pour le comptable et les autorités

Cette architecture garantit:
- L'indépendance entre les composants
- La possibilité d'évolution indépendante de chaque couche
- Une maintenance facilitée
- La réutilisation de code entre différentes fonctionnalités

### Sources de données

Le module s'interface avec plusieurs sources de données internes et externes:

| Source | Type de données | Méthode d'acquisition | Fréquence |
|--------|-----------------|------------------------|-----------|
| Caisse enregistreuse | Transactions de vente, TVA, modes de paiement | API REST | Temps réel / Fin de journée |
| Système de stocks | Inventaire, valorisation des stocks, mouvements | API REST | Temps réel / Quotidienne |
| Module commandes | Achats fournisseurs, livraisons, factures | API REST | À chaque événement |
| Module RH | Salaires, heures travaillées, congés | Export CSV | Hebdomadaire |
| Module réservations | Réservations, annulations, acomptes | API REST | Temps réel |
| Module marketing | Dépenses marketing, campagnes promotionnelles | API REST | Quotidienne |
| Système bancaire | Relevés bancaires, frais bancaires | Import CFONB / CSV | Quotidienne |
| Comptable externe | Écritures comptables validées | Import/Export | Mensuelle |

### Flux de données

Le flux de données dans le module suit un parcours logique:

1. **Collecte**: Les données sont extraites des sources via des connecteurs dédiés
2. **Normalisation**: Les données sont converties dans un format standard interne
3. **Validation**: Des contrôles sont effectués pour détecter les anomalies
4. **Enrichissement**: Des métadonnées comptables sont ajoutées (comptes, codes TVA, etc.)
5. **Agrégation**: Les données sont regroupées selon les dimensions d'analyse
6. **Calcul**: Les indicateurs financiers sont calculés
7. **Journalisation**: Les entrées du journal comptable sont générées
8. **Reporting**: Les rapports sont générés selon les modèles prédéfinis
9. **Export**: Les données sont exportées dans les formats requis

## Collecte et consolidation des données

### Caisse enregistreuse (POS)

Les données de vente constituent la principale source de revenus et sont récupérées via l'intégration API avec le système de caisse:

```python
# Exemple de récupération des données de vente (Lightspeed POS)
async def collect_pos_data(start_date, end_date):
    """Collecte les données de vente depuis la caisse enregistreuse."""
    pos_connector = api_connectors.get_connector("lightspeed")
    
    # Récupération des transactions sur la période
    transactions = await pos_connector.get_transactions(
        start_date=start_date,
        end_date=end_date
    )
    
    # Transformation en modèle comptable standardisé
    sales_entries = []
    for transaction in transactions:
        # Extraction des données pertinentes
        entry = {
            "date": transaction["timeStamp"],
            "type": "SALE",
            "amount": transaction["total"],
            "tax_details": extract_tax_details(transaction),
            "payment_method": transaction["paymentType"],
            "items": extract_items(transaction),
            "source_id": transaction["saleID"],
            "source": "POS"
        }
        sales_entries.append(entry)
    
    return sales_entries
```

Les données collectées incluent:
- Montant total de chaque transaction
- Détail des articles vendus
- Montant de TVA par taux applicable
- Mode de paiement (espèces, carte bancaire, etc.)
- Date et heure de la transaction
- Informations sur les remises appliquées

### Gestion des stocks

Les données d'inventaire et de stock sont essentielles pour calculer la valeur des actifs et le coût des marchandises vendues:

```python
# Exemple de récupération des données de stock
async def collect_inventory_data():
    """Collecte les données d'inventaire depuis le module IoT."""
    inventory_api = api_connectors.get_connector("inventory")
    
    # Récupération de l'état actuel des stocks
    current_inventory = await inventory_api.get_current_inventory()
    
    # Récupération des mouvements de stock sur la période
    inventory_movements = await inventory_api.get_inventory_movements(
        start_date=period_start_date,
        end_date=period_end_date
    )
    
    # Transformations en écritures comptables
    inventory_entries = []
    
    # Calcul de la valorisation du stock
    for item in current_inventory:
        entry = {
            "date": datetime.now().isoformat(),
            "type": "INVENTORY_VALUATION",
            "item_id": item["id"],
            "item_name": item["name"],
            "quantity": item["quantity"],
            "unit_cost": item["unit_cost"],
            "total_value": item["quantity"] * item["unit_cost"],
            "source": "INVENTORY"
        }
        inventory_entries.append(entry)
    
    # Traitement des mouvements de stock
    for movement in inventory_movements:
        movement_entry = {
            "date": movement["timestamp"],
            "type": "INVENTORY_MOVEMENT",
            "movement_type": movement["type"],  # IN, OUT, ADJUSTMENT
            "item_id": movement["item_id"],
            "item_name": movement["item_name"],
            "quantity": movement["quantity"],
            "unit_cost": movement["unit_cost"],
            "total_value": movement["quantity"] * movement["unit_cost"],
            "source_id": movement["id"],
            "source": "INVENTORY"
        }
        inventory_entries.append(movement_entry)
    
    return inventory_entries
```

Les informations collectées comprennent:
- État actuel des stocks (quantités et valeurs)
- Entrées de stock (achats, retours)
- Sorties de stock (ventes, pertes, gaspillage)
- Ajustements d'inventaire
- Valorisation selon la méthode FIFO (First In, First Out)

### Commandes fournisseurs

Les commandes et factures fournisseurs représentent les principales dépenses du restaurant:

```python
# Exemple de récupération des données de commandes fournisseurs
async def collect_purchase_data(start_date, end_date):
    """Collecte les données de commandes et factures fournisseurs."""
    suppliers_connector = api_connectors.get_connector("suppliers")
    
    # Récupération des commandes sur la période
    orders = await suppliers_connector.get_orders(
        start_date=start_date,
        end_date=end_date
    )
    
    # Récupération des factures sur la période
    invoices = await suppliers_connector.get_invoices(
        start_date=start_date,
        end_date=end_date
    )
    
    # Transformation en écritures comptables
    purchase_entries = []
    
    # Traitement des commandes
    for order in orders:
        entry = {
            "date": order["order_date"],
            "type": "PURCHASE_ORDER",
            "supplier_id": order["supplier_id"],
            "supplier_name": order["supplier_name"],
            "order_id": order["id"],
            "amount": order["total_amount"],
            "tax_amount": order["tax_amount"],
            "items": order["items"],
            "status": order["status"],
            "source": "SUPPLIERS"
        }
        purchase_entries.append(entry)
    
    # Traitement des factures
    for invoice in invoices:
        invoice_entry = {
            "date": invoice["invoice_date"],
            "type": "SUPPLIER_INVOICE",
            "supplier_id": invoice["supplier_id"],
            "supplier_name": invoice["supplier_name"],
            "invoice_id": invoice["id"],
            "amount": invoice["total_amount"],
            "tax_details": invoice["tax_details"],
            "payment_due_date": invoice["payment_due_date"],
            "payment_status": invoice["payment_status"],
            "source": "SUPPLIERS"
        }
        purchase_entries.append(invoice_entry)
    
    return purchase_entries
```

Les données collectées incluent:
- Détails des commandes passées
- Factures reçues des fournisseurs
- Détail des articles commandés
- Détail des taxes (TVA) sur les achats
- État des paiements aux fournisseurs
- Délais de paiement négociés

### Réservations

Les données de réservation fournissent des informations sur les revenus futurs et les acomptes:

```python
# Exemple de récupération des données de réservations
async def collect_booking_data(start_date, end_date):
    """Collecte les données de réservations et acomptes."""
    booking_connector = api_connectors.get_connector("booking")
    
    # Récupération des réservations
    bookings = await booking_connector.get_bookings(
        start_date=start_date,
        end_date=end_date
    )
    
    # Transformation en écritures comptables
    booking_entries = []
    
    for booking in bookings:
        # Ne traiter que les réservations avec acompte
        if booking.get("deposit_amount", 0) > 0:
            entry = {
                "date": booking["booking_date"],
                "type": "BOOKING_DEPOSIT",
                "customer_id": booking.get("customer_id"),
                "customer_name": booking.get("customer_name"),
                "booking_id": booking["id"],
                "amount": booking["deposit_amount"],
                "tax_amount": calculate_tax_from_total(booking["deposit_amount"]),
                "status": booking["status"],
                "source": "BOOKINGS"
            }
            booking_entries.append(entry)
    
    return booking_entries
```

### Données RH et paie

Les informations sur les salaires et charges sociales sont importées depuis le système de paie:

```python
# Exemple d'importation des données de paie
def import_payroll_data(csv_file_path):
    """Importe les données de paie depuis un fichier CSV exporté."""
    payroll_entries = []
    
    with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            entry = {
                "date": row["date_paie"],
                "type": "PAYROLL",
                "employee_id": row["id_employe"],
                "employee_name": row["nom_employe"],
                "gross_salary": float(row["salaire_brut"]),
                "employer_contributions": float(row["charges_patronales"]),
                "employee_contributions": float(row["charges_salariales"]),
                "net_salary": float(row["salaire_net"]),
                "hours_worked": float(row["heures_travaillees"]),
                "source": "PAYROLL"
            }
            payroll_entries.append(entry)
    
    return payroll_entries
```

### Campagnes marketing

Les dépenses marketing sont importantes pour évaluer le retour sur investissement:

```python
# Exemple de récupération des données marketing
async def collect_marketing_data(start_date, end_date):
    """Collecte les données des campagnes marketing."""
    marketing_connector = api_connectors.get_connector("marketing")
    
    # Récupération des campagnes actives sur la période
    campaigns = await marketing_connector.get_campaigns(
        start_date=start_date,
        end_date=end_date
    )
    
    # Récupération des dépenses marketing
    expenses = await marketing_connector.get_expenses(
        start_date=start_date,
        end_date=end_date
    )
    
    # Transformation en écritures comptables
    marketing_entries = []
    
    # Traitement des dépenses marketing
    for expense in expenses:
        entry = {
            "date": expense["date"],
            "type": "MARKETING_EXPENSE",
            "campaign_id": expense["campaign_id"],
            "campaign_name": expense["campaign_name"],
            "amount": expense["amount"],
            "tax_amount": expense["tax_amount"],
            "category": expense["category"],
            "source": "MARKETING"
        }
        marketing_entries.append(entry)
    
    return marketing_entries
```

## Mécanismes d'agrégation et de calcul

### Chiffre d'affaires

Le chiffre d'affaires est calculé à partir des transactions de vente, en tenant compte des différentes catégories de produits et des taux de TVA:

```python
# Exemple de calcul du chiffre d'affaires
def calculate_revenue(sales_entries, period_start, period_end, group_by='day'):
    """Calcule le chiffre d'affaires sur la période donnée."""
    # Filtrer les entrées sur la période
    filtered_entries = [
        entry for entry in sales_entries
        if period_start <= parse_date(entry["date"]) <= period_end
    ]
    
    # Grouper par la dimension demandée
    grouped_data = {}
    
    for entry in filtered_entries:
        date = parse_date(entry["date"])
        
        if group_by == 'day':
            key = date.strftime('%Y-%m-%d')
        elif group_by == 'week':
            key = f"{date.isocalendar()[0]}-W{date.isocalendar()[1]}"
        elif group_by == 'month':
            key = date.strftime('%Y-%m')
        else:
            key = 'total'
        
        if key not in grouped_data:
            grouped_data[key] = {
                'total': 0,
                'tax': 0,
                'by_category': {},
                'by_tax_rate': {}
            }
        
        # Ajouter au total
        grouped_data[key]['total'] += entry['amount']
        
        # Ajouter les taxes
        for tax_item in entry.get('tax_details', []):
            tax_rate = tax_item['rate']
            tax_amount = tax_item['amount']
            
            grouped_data[key]['tax'] += tax_amount
            
            if tax_rate not in grouped_data[key]['by_tax_rate']:
                grouped_data[key]['by_tax_rate'][tax_rate] = 0
            
            grouped_data[key]['by_tax_rate'][tax_rate] += tax_amount
        
        # Ajouter par catégorie
        for item in entry.get('items', []):
            category = item.get('category', 'Autre')
            item_amount = item.get('amount', 0)
            
            if category not in grouped_data[key]['by_category']:
                grouped_data[key]['by_category'][category] = 0
            
            grouped_data[key]['by_category'][category] += item_amount
    
    return grouped_data
```

### Marge brute et nette

La marge est calculée en tenant compte du coût des marchandises vendues:

```python
# Exemple de calcul de la marge
def calculate_margins(sales_data, cost_data, period_start, period_end):
    """Calcule les marges brute et nette sur la période donnée."""
    # Récupérer le chiffre d'affaires
    revenue = calculate_revenue(sales_data, period_start, period_end, group_by='total')
    total_revenue = revenue.get('total', {}).get('total', 0)
    
    # Calculer le coût des marchandises vendues
    cogs = calculate_cogs(cost_data, sales_data, period_start, period_end)
    
    # Calculer les autres coûts d'exploitation
    operating_costs = calculate_operating_costs(cost_data, period_start, period_end)
    
    # Calculer les marges
    gross_margin = total_revenue - cogs
    gross_margin_percentage = (gross_margin / total_revenue * 100) if total_revenue > 0 else 0
    
    net_margin = gross_margin - operating_costs
    net_margin_percentage = (net_margin / total_revenue * 100) if total_revenue > 0 else 0
    
    return {
        'revenue': total_revenue,
        'cogs': cogs,
        'operating_costs': operating_costs,
        'gross_margin': gross_margin,
        'gross_margin_percentage': gross_margin_percentage,
        'net_margin': net_margin,
        'net_margin_percentage': net_margin_percentage
    }
```

### Coûts d'exploitation

Les coûts d'exploitation sont ventilés par catégorie pour une analyse détaillée:

```python
# Exemple de calcul des coûts d'exploitation
def calculate_operating_costs(cost_entries, period_start, period_end, group_by='category'):
    """Calcule les coûts d'exploitation sur la période donnée."""
    # Filtrer les entrées sur la période
    filtered_entries = [
        entry for entry in cost_entries
        if period_start <= parse_date(entry["date"]) <= period_end
    ]
    
    # Grouper par la dimension demandée
    grouped_costs = {}
    
    for entry in filtered_entries:
        # Ne considérer que les entrées pertinentes pour les coûts d'exploitation
        if entry["type"] not in ["SUPPLIER_INVOICE", "PAYROLL", "MARKETING_EXPENSE", "UTILITY_BILL"]:
            continue
        
        # Déterminer la catégorie
        if group_by == 'category':
            if entry["type"] == "SUPPLIER_INVOICE":
                key = "Approvisionnements"
            elif entry["type"] == "PAYROLL":
                key = "Salaires et charges"
            elif entry["type"] == "MARKETING_EXPENSE":
                key = "Marketing"
            elif entry["type"] == "UTILITY_BILL":
                key = entry.get("utility_type", "Charges diverses")
            else:
                key = "Autres charges"
        else:
            key = 'total'
        
        if key not in grouped_costs:
            grouped_costs[key] = 0
        
        # Ajouter au total de la catégorie
        grouped_costs[key] += entry.get('amount', 0)
    
    return grouped_costs
```

### Rentabilité par période

L'analyse de rentabilité est effectuée sur différentes périodes pour suivre l'évolution:

```python
# Exemple de calcul de rentabilité par période
def calculate_profitability_by_period(financial_data, period='month', last_n_periods=12):
    """Calcule la rentabilité sur plusieurs périodes."""
    end_date = datetime.now()
    
    if period == 'day':
        start_date = end_date - timedelta(days=last_n_periods)
        date_format = '%Y-%m-%d'
        delta = timedelta(days=1)
    elif period == 'week':
        start_date = end_date - timedelta(weeks=last_n_periods)
        date_format = '%Y-W%W'
        delta = timedelta(weeks=1)
    elif period == 'month':
        start_date = end_date - relativedelta(months=last_n_periods)
        date_format = '%Y-%m'
        delta = relativedelta(months=1)
    else:  # year
        start_date = end_date - relativedelta(years=last_n_periods)
        date_format = '%Y'
        delta = relativedelta(years=1)
    
    # Générer la liste des périodes
    periods = []
    current_date = start_date
    while current_date <= end_date:
        periods.append(current_date.strftime(date_format))
        current_date += delta
    
    # Calculer la rentabilité pour chaque période
    profitability_data = []
    
    for period_str in periods:
        if period == 'day':
            period_start = datetime.strptime(period_str, date_format)
            period_end = period_start + timedelta(days=1) - timedelta(seconds=1)
        elif period == 'week':
            year, week = period_str.split('-W')
            period_start = datetime.strptime(f'{year}-{week}-1', '%Y-%W-%w')
            period_end = period_start + timedelta(days=7) - timedelta(seconds=1)
        elif period == 'month':
            period_start = datetime.strptime(period_str, date_format)
            period_end = period_start + relativedelta(months=1) - timedelta(seconds=1)
        else:  # year
            period_start = datetime.strptime(period_str, date_format)
            period_end = period_start + relativedelta(years=1) - timedelta(seconds=1)
        
        # Calculer les métriques pour cette période
        margins = calculate_margins(
            financial_data['sales'],
            financial_data['costs'],
            period_start,
            period_end
        )
        
        profitability_data.append({
            'period': period_str,
            'revenue': margins['revenue'],
            'gross_margin': margins['gross_margin'],
            'gross_margin_percentage': margins['gross_margin_percentage'],
            'net_margin': margins['net_margin'],
            'net_margin_percentage': margins['net_margin_percentage']
        })
    
    return profitability_data
```

### Analyse des coûts par catégorie

L'analyse détaillée des coûts permet d'identifier les postes de dépenses importants:

```python
# Exemple d'analyse des coûts par catégorie
def analyze_costs_by_category(cost_entries, period_start, period_end):
    """Analyse les coûts par catégorie sur la période donnée."""
    # Obtenir les coûts ventilés par catégorie
    costs_by_category = calculate_operating_costs(
        cost_entries, period_start, period_end, group_by='category'
    )
    
    # Calculer le total
    total_costs = sum(costs_by_category.values())
    
    # Calculer les pourcentages
    cost_analysis = []
    for category, amount in costs_by_category.items():
        percentage = (amount / total_costs * 100) if total_costs > 0 else 0
        
        cost_analysis.append({
            'category': category,
            'amount': amount,
            'percentage': percentage
        })
    
    # Trier par montant décroissant
    cost_analysis.sort(key=lambda x: x['amount'], reverse=True)
    
    return {
        'total': total_costs,
        'breakdown': cost_analysis
    }
```

### Prévisions financières

Les prévisions intègrent les données historiques et les projections du module IA/ML:

```python
# Exemple de génération de prévisions financières
async def generate_financial_forecast(historical_data, forecast_period=3, period_unit='month'):
    """Génère des prévisions financières basées sur les données historiques et le ML."""
    # Récupérer les prévisions de vente depuis le module IA/ML
    ml_connector = api_connectors.get_connector("ml")
    sales_forecast = await ml_connector.get_sales_forecast(
        forecast_periods=forecast_period,
        period_unit=period_unit
    )
    
    # Récupérer les prévisions de coûts
    cost_forecast = await ml_connector.get_cost_forecast(
        forecast_periods=forecast_period,
        period_unit=period_unit
    )
    
    # Projeter les marges et la rentabilité
    forecast_data = []
    
    for i in range(forecast_period):
        if period_unit == 'month':
            forecast_date = datetime.now() + relativedelta(months=i+1)
            period_label = forecast_date.strftime('%Y-%m')
        elif period_unit == 'quarter':
            forecast_date = datetime.now() + relativedelta(months=(i+1)*3)
            period_label = f"{forecast_date.year}-Q{(forecast_date.month-1)//3+1}"
        else:  # year
            forecast_date = datetime.now() + relativedelta(years=i+1)
            period_label = forecast_date.strftime('%Y')
        
        # Obtenir les prévisions pour cette période
        period_sales = sales_forecast[i]['predicted_amount']
        period_costs = cost_forecast[i]['predicted_amount']
        
        # Calculer les indicateurs financiers
        gross_margin = period_sales - period_costs['cogs']
        operating_costs = sum([
            period_costs.get('payroll', 0),
            period_costs.get('marketing', 0),
            period_costs.get('utilities', 0),
            period_costs.get('rent', 0),
            period_costs.get('other', 0)
        ])
        net_margin = gross_margin - operating_costs
        
        forecast_data.append({
            'period': period_label,
            'revenue': period_sales,
            'cogs': period_costs['cogs'],
            'gross_margin': gross_margin,
            'gross_margin_percentage': (gross_margin / period_sales * 100) if period_sales > 0 else 0,
            'operating_costs': operating_costs,
            'operating_costs_breakdown': {
                'payroll': period_costs.get('payroll', 0),
                'marketing': period_costs.get('marketing', 0),
                'utilities': period_costs.get('utilities', 0),
                'rent': period_costs.get('rent', 0),
                'other': period_costs.get('other', 0)
            },
            'net_margin': net_margin,
            'net_margin_percentage': (net_margin / period_sales * 100) if period_sales > 0 else 0
        })
    
    return forecast_data
```

## Génération automatique des rapports

### Types de rapports disponibles

Le module génère plusieurs types de rapports financiers, adaptés aux besoins de différentes parties prenantes:

1. **Rapports journaliers**:
   - Chiffre d'affaires du jour
   - Ventes par catégorie de produits
   - Marge brute journalière
   - Comparaison avec les objectifs
   - TOP 10 des produits vendus

2. **Rapports hebdomadaires**:
   - Synthèse des ventes de la semaine
   - Analyse des coûts directs
   - Analyse de la fréquentation
   - Comparaison avec la semaine précédente
   - Alertes sur les écarts significatifs

3. **Rapports mensuels**:
   - Compte de résultat mensuel
   - Analyse des marges par catégorie
   - Évolution des ventes/coûts
   - Analyse des ratios financiers
   - Suivi budgétaire

4. **Rapports trimestriels**:
   - États financiers complets
   - Analyse de rentabilité
   - Comparaison avec le trimestre précédent
   - Projection pour le trimestre suivant
   - Analyse des tendances

5. **Rapports annuels**:
   - Compte de résultat annuel
   - Bilan simplifié
   - Indicateurs clés de performance
   - Comparaison avec l'année précédente
   - Analyse d'évolution pluriannuelle

### Format des rapports

Les rapports sont générés dans plusieurs formats pour répondre aux besoins différents:

```python
# Exemple de génération de rapport en différents formats
async def generate_report(report_type, period_start, period_end, format='pdf'):
    """Génère un rapport dans le format demandé."""
    # Collecter les données nécessaires
    financial_data = await collect_financial_data(period_start, period_end)
    
    # Générer le contenu du rapport selon le type
    if report_type == 'daily':
        report_content = generate_daily_report_content(financial_data, period_start)
    elif report_type == 'weekly':
        report_content = generate_weekly_report_content(financial_data, period_start, period_end)
    elif report_type == 'monthly':
        report_content = generate_monthly_report_content(financial_data, period_start, period_end)
    elif report_type == 'quarterly':
        report_content = generate_quarterly_report_content(financial_data, period_start, period_end)
    elif report_type == 'annual':
        report_content = generate_annual_report_content(financial_data, period_start, period_end)
    else:
        raise ValueError(f"Type de rapport inconnu: {report_type}")
    
    # Générer le rapport dans le format demandé
    if format == 'pdf':
        return generate_pdf_report(report_content, report_type)
    elif format == 'csv':
        return generate_csv_report(report_content, report_type)
    elif format == 'excel':
        return generate_excel_report(report_content, report_type)
    elif format == 'json':
        return report_content  # Déjà au format JSON
    else:
        raise ValueError(f"Format de rapport non supporté: {format}")
```

### Programmation et automatisation

Les rapports sont générés automatiquement selon un calendrier configurable:

```python
# Exemple de configuration de la programmation des rapports
REPORT_SCHEDULE = {
    'daily': {
        'frequency': 'daily',
        'time': '23:30',
        'recipients': ['manager@levieuxmoulin.fr'],
        'formats': ['pdf', 'excel']
    },
    'weekly': {
        'frequency': 'weekly',
        'day': 'monday',  # Pour la semaine précédente
        'time': '09:00',
        'recipients': ['manager@levieuxmoulin.fr', 'owner@levieuxmoulin.fr'],
        'formats': ['pdf', 'excel']
    },
    'monthly': {
        'frequency': 'monthly',
        'day': 5,  # Le 5 du mois pour le mois précédent
        'time': '10:00',
        'recipients': ['manager@levieuxmoulin.fr', 'owner@levieuxmoulin.fr', 'accountant@levieuxmoulin.fr'],
        'formats': ['pdf', 'excel', 'csv']
    },
    'quarterly': {
        'frequency': 'quarterly',
        'month_day': (4, 15),  # Le 15 du mois suivant la fin du trimestre
        'time': '10:00',
        'recipients': ['manager@levieuxmoulin.fr', 'owner@levieuxmoulin.fr', 'accountant@levieuxmoulin.fr'],
        'formats': ['pdf', 'excel']
    },
    'annual': {
        'frequency': 'yearly',
        'month_day': (1, 31),  # Le 31 janvier pour l'année précédente
        'time': '10:00',
        'recipients': ['manager@levieuxmoulin.fr', 'owner@levieuxmoulin.fr', 'accountant@levieuxmoulin.fr'],
        'formats': ['pdf', 'excel', 'csv']
    }
}
```

### Notifications et distribution

Les rapports sont automatiquement envoyés par email aux destinataires configurés:

```python
# Exemple d'envoi de rapport par email
async def send_report_email(report_type, period_start, period_end, recipients, formats):
    """Envoie les rapports par email aux destinataires."""
    # Générer les rapports dans tous les formats demandés
    report_files = []
    
    for format in formats:
        report_content = await generate_report(report_type, period_start, period_end, format)
        
        # Déterminer le nom du fichier
        if report_type == 'daily':
            filename = f"rapport_journalier_{period_start.strftime('%Y-%m-%d')}.{format}"
        elif report_type == 'weekly':
            filename = f"rapport_hebdomadaire_{period_start.strftime('%Y-%m-%d')}_au_{period_end.strftime('%Y-%m-%d')}.{format}"
        elif report_type == 'monthly':
            filename = f"rapport_mensuel_{period_start.strftime('%Y-%m')}.{format}"
        elif report_type == 'quarterly':
            quarter = (period_start.month - 1) // 3 + 1
            filename = f"rapport_trimestriel_{period_start.year}_Q{quarter}.{format}"
        elif report_type == 'annual':
            filename = f"rapport_annuel_{period_start.year}.{format}"
        
        # Sauvegarder le rapport dans un fichier temporaire
        with tempfile.NamedTemporaryFile(suffix=f".{format}", delete=False) as temp_file:
            if format in ['pdf', 'excel']:
                temp_file.write(report_content)
            else:  # CSV ou JSON
                temp_file.write(json.dumps(report_content).encode('utf-8') if format == 'json' else report_content.encode('utf-8'))
            
            report_files.append((temp_file.name, filename))
    
    # Préparer l'email
    email_subject = f"Rapport {get_report_type_name(report_type)} - {get_period_description(report_type, period_start, period_end)}"
    
    email_body = f"""
    Bonjour,

    Veuillez trouver ci-joint le rapport {get_report_type_name(report_type)} pour la période du {period_start.strftime('%d/%m/%Y')} au {period_end.strftime('%d/%m/%Y')}.

    Ce rapport a été généré automatiquement par le système de gestion du Vieux Moulin.

    Cordialement,
    Le système de gestion du Vieux Moulin
    """
    
    # Envoyer l'email avec les pièces jointes
    email_connector = email_connectors.get_connector()
    await email_connector.send_email(
        subject=email_subject,
        body=email_body,
        recipients=recipients,
        attachments=report_files
    )
    
    # Nettoyer les fichiers temporaires
    for temp_file, _ in report_files:
        os.unlink(temp_file)
```

## Vérification d'intégrité des données

### Contrôles automatiques

Des contrôles automatiques sont effectués pour garantir l'intégrité des données financières:

```python
# Exemple de contrôles d'intégrité des données
def validate_financial_data(financial_data, period_start, period_end):
    """Exécute une série de contrôles d'intégrité sur les données financières."""
    validation_results = {}
    
    # 1. Vérifier la cohérence des dates
    date_errors = []
    for entry_type, entries in financial_data.items():
        for entry in entries:
            entry_date = parse_date(entry["date"])
            if entry_date < period_start or entry_date > period_end:
                date_errors.append({
                    'type': entry_type,
                    'id': entry.get('id', 'unknown'),
                    'date': entry["date"],
                    'error': 'Date hors période'
                })
    
    validation_results['date_errors'] = date_errors
    
    # 2. Vérifier la balance des transactions
    sales_total = sum(entry['amount'] for entry in financial_data.get('sales', []))
    sales_items_total = sum(
        sum(item.get('amount', 0) for item in entry.get('items', []))
        for entry in financial_data.get('sales', [])
    )
    
    validation_results['sales_balance_error'] = abs(sales_total - sales_items_total) > 0.01
    
    # 3. Vérifier la cohérence des taxes
    tax_errors = []
    for entry in financial_data.get('sales', []):
        declared_tax = sum(tax_item['amount'] for tax_item in entry.get('tax_details', []))
        calculated_tax = calculate_expected_tax(entry)
        
        if abs(declared_tax - calculated_tax) > 0.01:
            tax_errors.append({
                'id': entry.get('id', 'unknown'),
                'date': entry["date"],
                'declared_tax': declared_tax,
                'calculated_tax': calculated_tax,
                'difference': declared_tax - calculated_tax
            })
    
    validation_results['tax_errors'] = tax_errors
    
    # 4. Vérifier la cohérence des stocks
    stock_errors = []
    for movement in financial_data.get('inventory_movements', []):
        if movement['movement_type'] == 'OUT' and movement['quantity'] > 0:
            stock_errors.append({
                'id': movement.get('id', 'unknown'),
                'item_id': movement['item_id'],
                'error': 'Quantité positive pour un mouvement de sortie'
            })
    
    validation_results['stock_errors'] = stock_errors
    
    # 5. Vérifier l'exhaustivité des données
    completeness_errors = []
    
    # Vérifier si tous les jours de la période ont des ventes
    sales_dates = set(parse_date(entry["date"]).strftime('%Y-%m-%d') for entry in financial_data.get('sales', []))
    current_date = period_start
    while current_date <= period_end:
        date_str = current_date.strftime('%Y-%m-%d')
        if date_str not in sales_dates:
            completeness_errors.append({
                'date': date_str,
                'error': 'Aucune vente enregistrée pour cette date'
            })
        current_date += timedelta(days=1)
    
    validation_results['completeness_errors'] = completeness_errors
    
    return validation_results
```

### Détection d'anomalies

Le système utilise des algorithmes de détection d'anomalies pour identifier les valeurs inhabituelles:

```python
# Exemple de détection d'anomalies
async def detect_anomalies(financial_data, period_start, period_end):
    """Détecte les anomalies dans les données financières."""
    # Utiliser le module ML pour la détection d'anomalies
    ml_connector = api_connectors.get_connector("ml")
    
    # Préparer les données pour l'analyse
    daily_sales = calculate_revenue(
        financial_data.get('sales', []), 
        period_start, 
        period_end, 
        group_by='day'
    )
    
    # Transformer en série temporelle
    time_series_data = [
        {
            'date': key,
            'value': data['total']
        }
        for key, data in daily_sales.items()
    ]
    
    # Détecter les anomalies
    anomalies = await ml_connector.detect_anomalies(
        time_series_data=time_series_data,
        method='isolation_forest',
        contamination=0.05  # 5% des points sont considérés comme anormaux
    )
    
    # Détecter les anomalies dans les coûts
    daily_costs = calculate_operating_costs(
        financial_data.get('costs', []),
        period_start,
        period_end,
        group_by='day'
    )
    
    # Transformer en liste de points
    cost_series_data = [
        {
            'date': day,
            'value': sum(costs.values()) if isinstance(costs, dict) else costs
        }
        for day, costs in daily_costs.items()
    ]
    
    cost_anomalies = await ml_connector.detect_anomalies(
        time_series_data=cost_series_data,
        method='isolation_forest',
        contamination=0.05
    )
    
    # Combiner les résultats
    all_anomalies = {
        'sales_anomalies': anomalies,
        'cost_anomalies': cost_anomalies
    }
    
    return all_anomalies
```

### Réconciliation des données

La réconciliation permet de vérifier la cohérence entre différentes sources:

```python
# Exemple de réconciliation des données
def reconcile_data_sources(financial_data):
    """Réconcilie les données entre différentes sources."""
    reconciliation_results = {}
    
    # 1. Réconcilier les ventes POS avec les mouvements de stock
    pos_sales = {}
    for sale in financial_data.get('sales', []):
        sale_date = parse_date(sale["date"]).strftime('%Y-%m-%d')
        
        if sale_date not in pos_sales:
            pos_sales[sale_date] = {}
        
        for item in sale.get('items', []):
            item_id = item.get('item_id')
            if not item_id:
                continue
                
            if item_id not in pos_sales[sale_date]:
                pos_sales[sale_date][item_id] = 0
            
            pos_sales[sale_date][item_id] += item.get('quantity', 0)
    
    # Mouvements de stock "OUT" de type "SALE"
    inventory_outs = {}
    for movement in financial_data.get('inventory_movements', []):
        if movement['movement_type'] != 'OUT' or movement.get('reason') != 'SALE':
            continue
            
        movement_date = parse_date(movement["date"]).strftime('%Y-%m-%d')
        item_id = movement['item_id']
        
        if movement_date not in inventory_outs:
            inventory_outs[movement_date] = {}
        
        if item_id not in inventory_outs[movement_date]:
            inventory_outs[movement_date][item_id] = 0
        
        inventory_outs[movement_date][item_id] += abs(movement['quantity'])
    
    # Comparer les quantités
    sales_inventory_discrepancies = []
    
    for date in set(pos_sales.keys()) | set(inventory_outs.keys()):
        for item_id in set(pos_sales.get(date, {}).keys()) | set(inventory_outs.get(date, {}).keys()):
            pos_qty = pos_sales.get(date, {}).get(item_id, 0)
            inventory_qty = inventory_outs.get(date, {}).get(item_id, 0)
            
            if abs(pos_qty - inventory_qty) > 0.01:
                sales_inventory_discrepancies.append({
                    'date': date,
                    'item_id': item_id,
                    'pos_quantity': pos_qty,
                    'inventory_quantity': inventory_qty,
                    'difference': pos_qty - inventory_qty
                })
    
    reconciliation_results['sales_inventory_discrepancies'] = sales_inventory_discrepancies
    
    # 2. Réconcilier les factures fournisseurs avec les mouvements de stock "IN"
    # [...code similar to above for purchase reconciliation...]
    
    return reconciliation_results
```

## Exemples de rapports financiers

### Rapport journalier

Le rapport journalier fournit un aperçu des performances du jour:

```
RAPPORT JOURNALIER - LE VIEUX MOULIN
Date: 15/04/2025

SYNTHÈSE DES VENTES
-------------------
Chiffre d'affaires total: 2,345.00 €
Nombre de transactions: 87
Panier moyen: 26.95 €
Taux de TVA collectée: 231.23 €

VENTES PAR CATÉGORIE
-------------------
Pizzas: 1,205.50 € (51.4%)
Plats: 523.75 € (22.3%)
Boissons: 425.25 € (18.1%)
Desserts: 190.50 € (8.1%)

TOP 5 PRODUITS
-------------
1. Pizza Reine: 345.00 € (23 vendues)
2. Pizza 4 Fromages: 289.50 € (17 vendues)
3. Tiramisu: 136.00 € (17 vendus)
4. Magret de Canard: 126.00 € (6 vendus)
5. Vin Rouge Bordeaux: 112.50 € (15 vendus)

COMPARAISON AVEC LA SEMAINE DERNIÈRE
----------------------------------
CA du jour précédent (08/04/2025): 2,187.25 €
Évolution: +157.75 € (+7.2%)

COMPARAISON AVEC LES OBJECTIFS
----------------------------
Objectif journalier: 2,200.00 €
Performance: +145.00 € (+6.6%)

MARGE BRUTE ESTIMÉE
------------------
Coût des marchandises vendues: 703.50 €
Marge brute: 1,641.50 € (70.0%)
```

### Rapport hebdomadaire

Le rapport hebdomadaire présente une analyse plus détaillée sur la semaine:

```
RAPPORT HEBDOMADAIRE - LE VIEUX MOULIN
Semaine 16 (du 07/04/2025 au 13/04/2025)

SYNTHÈSE FINANCIÈRE
------------------
Chiffre d'affaires total: 15,780.25 €
Coût des marchandises vendues: 4,734.08 €
Marge brute: 11,046.17 € (70.0%)
Charges d'exploitation: 7,102.11 €
Résultat net provisoire: 3,944.06 € (25.0%)

ANALYSE DES VENTES
----------------
Nombre total de transactions: 576
Panier moyen: 27.40 €
Répartition par jour:
- Lundi: 1,678.50 € (10.6%)
- Mardi: 1,897.25 € (12.0%)
- Mercredi: 2,043.00 € (12.9%)
- Jeudi: 2,187.25 € (13.9%)
- Vendredi: 2,456.75 € (15.6%)
- Samedi: 3,067.00 € (19.4%)
- Dimanche: 2,450.50 € (15.5%)

ANALYSE DES COÛTS
---------------
Répartition par catégorie:
- Matières premières: 4,734.08 € (40.1%)
- Personnel: 5,047.28 € (42.7%)
- Marketing: 473.41 € (4.0%)
- Charges fixes: 1,578.03 € (13.3%)

INDICATEURS DE PERFORMANCE
------------------------
Taux d'occupation moyen: 72%
Rotation moyenne des tables: 2.3 par service
Ventes moyennes par couvert: 23.85 €

COMPARAISON AVEC LA SEMAINE PRÉCÉDENTE
------------------------------------
CA semaine précédente: 14,987.50 €
Évolution: +792.75 € (+5.3%)
Marge brute précédente: 10,491.25 € (70.0%)
Évolution marge: +554.92 € (+5.3%)

TENDANCES ET RECOMMANDATIONS
--------------------------
- Forte augmentation des ventes de pizzas (+8.7%)
- Légère baisse des desserts (-2.3%)
- Recommandation: Mettre en avant les desserts en promotion
```

### Rapport mensuel

Le rapport mensuel offre une vision complète des résultats du mois:

```
RAPPORT MENSUEL - LE VIEUX MOULIN
Avril 2025

COMPTE DE RÉSULTAT SIMPLIFIÉ
---------------------------
Chiffre d'affaires HT: 67,820.00 €
TVA collectée: 6,782.00 €
Chiffre d'affaires TTC: 74,602.00 €

Achats marchandises: 20,346.00 €
Variation de stock: -1,250.00 €
Coût des marchandises vendues: 19,096.00 €

MARGE BRUTE: 48,724.00 € (71.8%)

Charges d'exploitation:
- Salaires bruts: 18,939.60 € (27.9%)
- Charges sociales: 9,469.80 € (14.0%)
- Loyer et charges: 4,747.40 € (7.0%)
- Énergie et fluides: 2,712.80 € (4.0%)
- Marketing et communication: 2,034.60 € (3.0%)
- Entretien et réparations: 1,356.40 € (2.0%)
- Assurances: 678.20 € (1.0%)
- Honoraires: 1,356.40 € (2.0%)
- Autres charges: 2,034.60 € (3.0%)
Total charges d'exploitation: 43,329.80 € (63.9%)

RÉSULTAT D'EXPLOITATION: 5,394.20 € (8.0%)

ANALYSE DES VENTES
----------------
Répartition par catégorie:
- Pizzas: 33,910.00 € (50.0%)
- Plats: 13,564.00 € (20.0%)
- Entrées: 6,782.00 € (10.0%)
- Desserts: 6,782.00 € (10.0%)
- Boissons: 6,782.00 € (10.0%)

Ventes par mode de paiement:
- Carte bancaire: 50,865.00 € (75.0%)
- Espèces: 13,564.00 € (20.0%)
- Tickets restaurant: 3,391.00 € (5.0%)

ÉVOLUTION MENSUELLE
-----------------
Comparaison avec mars 2025:
- CA mars 2025: 62,450.00 €
- Évolution: +5,370.00 € (+8.6%)
- Marge brute mars: 43,715.00 € (70.0%)
- Évolution marge: +5,009.00 € (+11.5%)

Comparaison avec avril 2024:
- CA avril 2024: 58,750.00 €
- Évolution annuelle: +9,070.00 € (+15.4%)

INDICATEURS DE PERFORMANCE
------------------------
Nombre de couverts: 2,845
CA moyen par couvert: 23.84 €
Taux d'occupation moyen: 68%
Taux de retour clients: 35%

SITUATION DE TRÉSORERIE
---------------------
Solde bancaire au 30/04/2025: 28,463.25 €
Encaissements du mois: 74,602.00 €
Décaissements du mois: 70,125.35 €
Variation de trésorerie: +4,476.65 €

PRÉVISIONS POUR MAI 2025
----------------------
CA prévisionnel: 71,211.00 € (+5.0%)
Marge brute prévisionnelle: 51,160.20 € (71.8%)
Résultat d'exploitation prévisionnel: 5,696.88 € (8.0%)
```

## Intégration avec d'autres modules

### Interface avec le serveur central

Le module de comptabilité s'intègre avec le serveur central via une API REST complète:

```python
# Exemple d'interface avec le serveur central
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

app = FastAPI(title="Module Comptabilité API", version="1.0.0")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Modèles Pydantic pour l'API
class DateRange(BaseModel):
    start_date: datetime
    end_date: datetime

class ReportRequest(BaseModel):
    report_type: str
    date_range: DateRange
    format: str = "pdf"
    sections: Optional[List[str]] = None

class DataQueryRequest(BaseModel):
    data_type: str
    date_range: DateRange
    filters: Optional[Dict[str, Any]] = None
    group_by: Optional[str] = None

# Routes API
@app.post("/reports/generate")
async def generate_report_endpoint(request: ReportRequest, token: str = Depends(oauth2_scheme)):
    """Génère un rapport financier selon les paramètres demandés."""
    try:
        report = await generate_report(
            report_type=request.report_type,
            period_start=request.date_range.start_date,
            period_end=request.date_range.end_date,
            format=request.format
        )
        
        # Format de la réponse selon le type de rapport
        if request.format == "json":
            return {"status": "success", "report": report}
        else:
            # Pour les formats binaires (PDF, Excel)
            return Response(
                content=report,
                media_type=get_media_type(request.format),
                headers={
                    "Content-Disposition": f"attachment; filename=report_{request.report_type}_{request.date_range.start_date.strftime('%Y%m%d')}.{request.format}"
                }
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/data/query")
async def query_financial_data(request: DataQueryRequest, token: str = Depends(oauth2_scheme)):
    """Interroge les données financières selon les critères spécifiés."""
    try:
        # Collecter les données demandées
        if request.data_type == "sales":
            data = await collect_sales_data(
                start_date=request.date_range.start_date,
                end_date=request.date_range.end_date,
                filters=request.filters
            )
            
            # Grouper si nécessaire
            if request.group_by:
                data = group_sales_data(data, request.group_by)
        
        elif request.data_type == "costs":
            data = await collect_costs_data(
                start_date=request.date_range.start_date,
                end_date=request.date_range.end_date,
                filters=request.filters
            )
            
            # Grouper si nécessaire
            if request.group_by:
                data = group_costs_data(data, request.group_by)
        
        elif request.data_type == "margins":
            sales_data = await collect_sales_data(
                start_date=request.date_range.start_date,
                end_date=request.date_range.end_date,
                filters=request.filters
            )
            
            costs_data = await collect_costs_data(
                start_date=request.date_range.start_date,
                end_date=request.date_range.end_date,
                filters=request.filters
            )
            
            data = calculate_margins(
                sales_data=sales_data,
                cost_data=costs_data,
                period_start=request.date_range.start_date,
                period_end=request.date_range.end_date
            )
            
            # Grouper si nécessaire
            if request.group_by:
                data = group_margin_data(data, request.group_by)
        
        else:
            raise HTTPException(status_code=400, detail=f"Type de données non supporté: {request.data_type}")
        
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/data/validate")
async def validate_data_endpoint(request: DateRange, token: str = Depends(oauth2_scheme)):
    """Valide l'intégrité des données financières sur la période spécifiée."""
    try:
        # Collecter les données financières
        financial_data = await collect_financial_data(
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        # Exécuter les validations
        validation_results = validate_financial_data(
            financial_data=financial_data,
            period_start=request.start_date,
            period_end=request.end_date
        )
        
        # Exécuter la détection d'anomalies
        anomalies = await detect_anomalies(
            financial_data=financial_data,
            period_start=request.start_date,
            period_end=request.end_date
        )
        
        # Exécuter la réconciliation des données
        reconciliation_results = reconcile_data_sources(financial_data)
        
        return {
            "status": "success",
            "validation": validation_results,
            "anomalies": anomalies,
            "reconciliation": reconciliation_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### API REST

L'API REST expose les fonctionnalités du module aux autres composants:

| Endpoint | Méthode | Description | Paramètres | Réponse |
|----------|---------|-------------|------------|---------|
| `/reports/generate` | POST | Génère un rapport financier | report_type, date_range, format | Rapport au format demandé |
| `/reports/schedule` | POST | Programme un rapport récurrent | report_type, schedule, recipients | ID de programmation |
| `/data/query` | POST | Interroge les données financières | data_type, date_range, filters, group_by | Données demandées |
| `/data/validate` | POST | Valide les données financières | date_range | Résultats de validation |
| `/data/import` | POST | Importe des données externes | source, data | Statut d'importation |
| `/data/export` | POST | Exporte des données financières | data_type, date_range, format | Données exportées |

### Webhooks

Des webhooks sont implémentés pour notifier les événements importants:

```python
# Configuration des webhooks
WEBHOOK_CONFIG = {
    'anomaly_detection': {
        'url': 'https://server.levieuxmoulin.fr/api/events/accounting/anomaly',
        'secret': 'b8f7a3e5d2c1',
        'events': ['ANOMALY_DETECTED', 'DATA_VALIDATION_FAILED']
    },
    'report_generation': {
        'url': 'https://server.levieuxmoulin.fr/api/events/accounting/report',
        'secret': '3a9c7e2b5d1f',
        'events': ['REPORT_GENERATED', 'REPORT_FAILED']
    },
    'data_integration': {
        'url': 'https://server.levieuxmoulin.fr/api/events/accounting/data',
        'secret': '6d4f2e8a1c7b',
        'events': ['DATA_IMPORTED', 'DATA_RECONCILIATION_FAILED']
    }
}

# Exemple d'envoi de notification webhook
async def send_webhook_notification(event_type, payload):
    """Envoie une notification webhook aux endpoints configurés."""
    # Trouver les configurations concernées par cet événement
    matching_configs = [
        config for config in WEBHOOK_CONFIG.values()
        if event_type in config['events']
    ]
    
    if not matching_configs:
        return
    
    # Préparer la notification
    notification = {
        'event': event_type,
        'timestamp': datetime.now().isoformat(),
        'data': payload
    }
    
    # Envoyer aux endpoints configurés
    async with aiohttp.ClientSession() as session:
        for config in matching_configs:
            # Signer la requête
            signature = hmac.new(
                config['secret'].encode('utf-8'),
                json.dumps(notification).encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            headers = {
                'Content-Type': 'application/json',
                'X-Webhook-Signature': signature
            }
            
            try:
                async with session.post(
                    config['url'],
                    json=notification,
                    headers=headers
                ) as response:
                    if response.status != 200:
                        logger.warning(f"Échec d'envoi du webhook {event_type} à {config['url']}: {response.status}")
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi du webhook {event_type} à {config['url']}: {str(e)}")
```

### Format des données échangées

Les données sont échangées dans un format JSON standardisé:

```json
{
  "sales_entry": {
    "id": "sale_20250415_123",
    "date": "2025-04-15T19:45:23Z",
    "type": "SALE",
    "amount": 45.50,
    "tax_details": [
      {
        "rate": 10.0,
        "base": 41.36,
        "amount": 4.14
      }
    ],
    "payment_method": "CARD",
    "items": [
      {
        "id": "prod_123",
        "name": "Pizza Reine",
        "category": "Pizzas",
        "quantity": 1,
        "unit_price": 15.00,
        "amount": 15.00
      },
      {
        "id": "prod_456",
        "name": "Tiramisu",
        "category": "Desserts",
        "quantity": 2,
        "unit_price": 6.00,
        "amount": 12.00
      },
      {
        "id": "prod_789",
        "name": "Coca-Cola",
        "category": "Boissons",
        "quantity": 3,
        "unit_price": 3.50,
        "amount": 10.50
      }
    ],
    "source_id": "pos_transaction_456",
    "source": "POS"
  }
}
```

## Sécurité des données

### Chiffrement

Les données sensibles sont chiffrées en transit et au repos:

```python
# Exemple de chiffrement des données
from cryptography.fernet import Fernet
import os
import json

class SecureDataStore:
    """Stockage sécurisé pour les données financières sensibles."""
    
    def __init__(self, encryption_key=None):
        # Utiliser une clé fournie ou générer/charger une nouvelle clé
        if encryption_key:
            self.key = encryption_key
        else:
            key_path = os.environ.get("ACCOUNTING_DATA_KEY", ".accounting.key")
            if os.path.exists(key_path):
                with open(key_path, "rb") as f:
                    self.key = f.read()
            else:
                self.key = Fernet.generate_key()
                with open(key_path, "wb") as f:
                    f.write(self.key)
                os.chmod(key_path, 0o600)  # Permissions restrictives
        
        self.cipher = Fernet(self.key)
    
    def encrypt_data(self, data):
        """Chiffre des données sensibles."""
        if isinstance(data, dict) or isinstance(data, list):
            serialized = json.dumps(data).encode('utf-8')
        elif isinstance(data, str):
            serialized = data.encode('utf-8')
        else:
            serialized = str(data).encode('utf-8')
        
        return self.cipher.encrypt(serialized)
    
    def decrypt_data(self, encrypted_data):
        """Déchiffre des données sensibles."""
        decrypted = self.cipher.decrypt(encrypted_data)
        
        try:
            # Tenter de désérialiser comme JSON
            return json.loads(decrypted.decode('utf-8'))
        except json.JSONDecodeError:
            # Sinon, retourner comme chaîne
            return decrypted.decode('utf-8')
    
    def store_encrypted_file(self, data, filename):
        """Stocke des données chiffrées dans un fichier."""
        encrypted = self.encrypt_data(data)
        
        with open(filename, "wb") as f:
            f.write(encrypted)
        
        # Permissions restrictives
        os.chmod(filename, 0o600)
    
    def load_encrypted_file(self, filename):
        """Charge et déchiffre des données depuis un fichier."""
        if not os.path.exists(filename):
            return None
        
        with open(filename, "rb") as f:
            encrypted = f.read()
        
        return self.decrypt_data(encrypted)
```

### Contrôle d'accès

Un système de contrôle d'accès basé sur les rôles est implémenté:

```python
# Exemple de système de contrôle d'accès
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from datetime import datetime, timedelta
from typing import Optional, List

# Configuration
SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Modèle de données utilisateur
class User:
    def __init__(self, username: str, roles: List[str]):
        self.username = username
        self.roles = roles

# Mapping des rôles et permissions
ROLE_PERMISSIONS = {
    "admin": ["read", "write", "delete", "configure"],
    "accountant": ["read", "write"],
    "manager": ["read"],
    "viewer": ["read"]
}

# Niveaux d'accès aux données
DATA_ACCESS_LEVELS = {
    "admin": ["sales", "costs", "margins", "inventory", "payroll", "banking"],
    "accountant": ["sales", "costs", "margins", "inventory", "payroll", "banking"],
    "manager": ["sales", "costs", "margins", "inventory"],
    "viewer": ["sales", "margins"]
}

# Création d'un token d'accès
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

# Vérification du token et des permissions
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        roles: List[str] = payload.get("roles", [])
        
        if username is None:
            raise credentials_exception
        
        return User(username=username, roles=roles)
    except jwt.PyJWTError:
        raise credentials_exception

# Vérification des permissions pour une action spécifique
def has_permission(user: User, required_permission: str, data_type: Optional[str] = None):
    # Vérifier si l'utilisateur a la permission requise via ses rôles
    for role in user.roles:
        if role not in ROLE_PERMISSIONS:
            continue
            
        if required_permission in ROLE_PERMISSIONS[role]:
            # Si un type de données est spécifié, vérifier aussi l'accès à ce type
            if data_type and role in DATA_ACCESS_LEVELS:
                if data_type in DATA_ACCESS_LEVELS[role]:
                    return True
            elif not data_type:
                return True
    
    return False

# Dépendance pour vérifier les permissions
def require_permission(permission: str, data_type: Optional[str] = None):
    async def permission_dependency(user: User = Depends(get_current_user)):
        if not has_permission(user, permission, data_type):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return user
    
    return permission_dependency

# Exemple d'utilisation dans les routes API
@app.get("/reports/sales", dependencies=[Depends(require_permission("read", "sales"))])
async def get_sales_report():
    # Implémentation
    pass

@app.post("/data/configure", dependencies=[Depends(require_permission("configure"))])
async def configure_accounting_settings():
    # Implémentation
    pass
```

### Traçabilité

Toutes les actions sont journalisées pour assurer la traçabilité:

```python
# Exemple de système de journalisation d'audit
import logging
import structlog
from datetime import datetime
import uuid

# Configuration du logger d'audit
audit_logger = structlog.get_logger("accounting.audit")

class AuditLogger:
    """Système de journalisation pour l'audit des opérations comptables."""
    
    @staticmethod
    async def log_action(user, action, resource_type, resource_id=None, details=None):
        """Enregistre une action dans le journal d'audit."""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "audit_id": str(uuid.uuid4()),
            "user": user.username,
            "roles": user.roles,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details,
            "ip_address": get_request_ip()
        }
        
        # Journaliser localement
        audit_logger.info(
            "audit_event",
            **audit_entry
        )
        
        # Stocker dans la base de données d'audit
        await store_audit_entry(audit_entry)
        
        # Si action critique, notifier les administrateurs
        if action in ["DELETE", "MODIFY_CRITICAL", "EXPORT_ALL"]:
            await notify_admins_of_critical_action(audit_entry)
    
    @staticmethod
    async def search_audit_logs(filters=None, start_date=None, end_date=None, limit=100):
        """Recherche dans les journaux d'audit selon des critères."""
        query = {}
        
        if filters:
            query.update(filters)
        
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date.isoformat()
            if end_date:
                date_query["$lte"] = end_date.isoformat()
            
            query["timestamp"] = date_query
        
        # Exécuter la requête sur la base de données d'audit
        audit_entries = await retrieve_audit_entries(query, limit)
        
        return audit_entries
```

## Annexes

### Plan comptable

Le module utilise le plan comptable français standard, adapté aux besoins de la restauration:

```json
{
  "chart_of_accounts": {
    "class_1": {
      "name": "Comptes de capitaux",
      "accounts": {
        "101": {"name": "Capital"},
        "106": {"name": "Réserves"},
        "120": {"name": "Résultat de l'exercice"}
      }
    },
    "class_2": {
      "name": "Comptes d'immobilisations",
      "accounts": {
        "211": {"name": "Terrains"},
        "213": {"name": "Constructions"},
        "215": {"name": "Installations techniques, matériel et outillage"},
        "218": {"name": "Autres immobilisations corporelles"}
      }
    },
    "class_3": {
      "name": "Comptes de stocks",
      "accounts": {
        "31": {"name": "Matières premières"},
        "32": {"name": "Autres approvisionnements"},
        "37": {"name": "Stocks de marchandises"}
      }
    },
    "class_4": {
      "name": "Comptes de tiers",
      "accounts": {
        "401": {"name": "Fournisseurs"},
        "411": {"name": "Clients"},
        "421": {"name": "Personnel - rémunérations dues"},
        "431": {"name": "Sécurité sociale"},
        "445": {"name": "État - Taxes sur le chiffre d'affaires"}
      }
    },
    "class_5": {
      "name": "Comptes financiers",
      "accounts": {
        "512": {"name": "Banques"},
        "53": {"name": "Caisse"}
      }
    },
    "class_6": {
      "name": "Comptes de charges",
      "accounts": {
        "601": {"name": "Achats de matières premières"},
        "607": {"name": "Achats de marchandises"},
        "611": {"name": "Sous-traitance générale"},
        "613": {"name": "Locations"},
        "615": {"name": "Entretien et réparations"},
        "616": {"name": "Primes d'assurances"},
        "622": {"name": "Rémunérations d'intermédiaires et honoraires"},
        "623": {"name": "Publicité, publications, relations publiques"},
        "625": {"name": "Déplacements, missions et réceptions"},
        "626": {"name": "Frais postaux et de télécommunications"},
        "628": {"name": "Divers services extérieurs"},
        "631": {"name": "Impôts, taxes et versements assimilés sur rémunérations"},
        "635": {"name": "Autres impôts, taxes et versements assimilés"},
        "641": {"name": "Rémunérations du personnel"},
        "645": {"name": "Charges de sécurité sociale et de prévoyance"},
        "651": {"name": "Redevances pour concessions, brevets, licences, etc."},
        "661": {"name": "Charges d'intérêts"},
        "681": {"name": "Dotations aux amortissements et aux provisions"}
      }
    },
    "class_7": {
      "name": "Comptes de produits",
      "accounts": {
        "701": {"name": "Ventes de produits finis"},
        "706": {"name": "Prestations de services"},
        "707": {"name": "Ventes de marchandises"},
        "708": {"name": "Produits des activités annexes"},
        "709": {"name": "Rabais, remises et ristournes accordés"},
        "76": {"name": "Produits financiers"},
        "77": {"name": "Produits exceptionnels"}
      }
    }
  }
}
```

### Codes TVA

Configuration des taux de TVA pour la restauration en France:

```json
{
  "vat_rates": {
    "standard": {
      "rate": 20.0,
      "code": "S",
      "description": "Taux normal",
      "applicable_to": ["services", "boissons_alcoolisees"]
    },
    "reduced": {
      "rate": 10.0,
      "code": "R",
      "description": "Taux réduit",
      "applicable_to": ["restauration_sur_place", "hebergement"]
    },
    "special_reduced": {
      "rate": 5.5,
      "code": "SR",
      "description": "Taux réduit spécial",
      "applicable_to": ["alimentaire_a_emporter", "boissons_non_alcoolisees"]
    },
    "super_reduced": {
      "rate": 2.1,
      "code": "SPR",
      "description": "Taux super réduit",
      "applicable_to": ["produits_specifiques"]
    }
  },
  "product_categories": {
    "Pizzas": {
      "on_premises": {"vat_rate": "reduced"},
      "takeaway": {"vat_rate": "special_reduced"}
    },
    "Plats": {
      "on_premises": {"vat_rate": "reduced"},
      "takeaway": {"vat_rate": "special_reduced"}
    },
    "Desserts": {
      "on_premises": {"vat_rate": "reduced"},
      "takeaway": {"vat_rate": "special_reduced"}
    },
    "Boissons_Alcoolisees": {
      "on_premises": {"vat_rate": "standard"},
      "takeaway": {"vat_rate": "standard"}
    },
    "Boissons_Non_Alcoolisees": {
      "on_premises": {"vat_rate": "reduced"},
      "takeaway": {"vat_rate": "special_reduced"}
    }
  }
}
```

### Formules de calcul détaillées

Les formules utilisées pour les calculs financiers sont documentées:

```
# Marge brute
Marge Brute = Chiffre d'Affaires HT - Coût des Marchandises Vendues

# Pourcentage de marge brute
Pourcentage de Marge Brute = (Marge Brute / Chiffre d'Affaires HT) * 100

# Coûts directs
Coûts Directs = Coût des Marchandises Vendues + Main d'Œuvre Directe

# Marge sur coûts directs
Marge sur Coûts Directs = Chiffre d'Affaires HT - Coûts Directs

# Coûts d'exploitation
Coûts d'Exploitation = Coûts Directs + Frais Généraux + Loyer + Marketing + Impôts et Taxes

# Résultat d'exploitation
Résultat d'Exploitation = Chiffre d'Affaires HT - Coûts d'Exploitation

# Taux de marge nette
Taux de Marge Nette = (Résultat d'Exploitation / Chiffre d'Affaires HT) * 100

# Point mort
Point Mort = Charges Fixes / (1 - (Charges Variables / Chiffre d'Affaires HT))

# Ratio de rentabilité sur investissement
ROI = (Résultat Net / Investissement Total) * 100

# Ratio du coût alimentaire
Food Cost Ratio = (Coût des Ingrédients / Chiffre d'Affaires Nourriture) * 100

# Chiffre d'affaires moyen par couvert
CA Moyen par Couvert = Chiffre d'Affaires Total / Nombre de Couverts

# Coût moyen par couvert
Coût Moyen par Couvert = Coûts Directs / Nombre de Couverts

# Bénéfice par couvert
Bénéfice par Couvert = (Chiffre d'Affaires Total - Coûts d'Exploitation) / Nombre de Couverts

# Taux de rotation des stocks
Taux de Rotation des Stocks = Coût des Marchandises Vendues / ((Stock Début + Stock Fin) / 2)

# Délai moyen de paiement fournisseurs
Délai Moyen de Paiement = (Dettes Fournisseurs / Achats) * 365

# Taux d'occupation
Taux d'Occupation = (Nombre de Couverts / Capacité Totale) * 100
```

---

© 2025 Le Vieux Moulin - Tous droits réservés
