/**
 * Module de calcul de valorisation des stocks pour Le Vieux Moulin
 * Ce module fournit les fonctionnalités pour valoriser les stocks d'ingrédients
 * selon différentes méthodes comptables et calculer les coûts des plats.
 */

'use strict';

const { DataCollector } = require('../common/data_collector');
const { ConfigManager } = require('../common/config_manager');

/**
 * Classe principale pour les calculs de valorisation d'inventaire
 */
class InventoryCalculator {
  /**
   * Crée une nouvelle instance du calculateur d'inventaire
   * @param {Object} options - Options de configuration
   * @param {string} options.valuationMethod - Méthode de valorisation (weighted_average, fifo, lifo)
   * @param {Object} options.costConfiguration - Configuration des coûts spécifiques
   * @param {DataCollector} options.dataCollector - Instance du collecteur de données
   * @param {ConfigManager} options.configManager - Instance du gestionnaire de configuration
   */
  constructor(options = {}) {
    this.valuationMethod = options.valuationMethod || 'weighted_average';
    this.costConfiguration = options.costConfiguration || {};
    this.dataCollector = options.dataCollector || null;
    this.configManager = options.configManager || 
      (ConfigManager.getConfigManager ? ConfigManager.getConfigManager() : null);
    
    // Charger la configuration depuis le gestionnaire si disponible
    if (this.configManager) {
      const inventoryConfig = this.configManager.getConfig('inventory', {});
      
      if (inventoryConfig.valuationMethod) {
        this.valuationMethod = inventoryConfig.valuationMethod;
      }
      
      if (inventoryConfig.costConfiguration) {
        this.costConfiguration = { ...this.costConfiguration, ...inventoryConfig.costConfiguration };
      }
    }
    
    // Méthodes de valorisation disponibles
    this.valuationMethods = {
      weighted_average: this._calculateWeightedAverage.bind(this),
      fifo: this._calculateFIFO.bind(this),
      lifo: this._calculateLIFO.bind(this),
      specific_identification: this._calculateSpecificIdentification.bind(this)
    };
    
    // Vérifier que la méthode spécifiée existe
    if (!this.valuationMethods[this.valuationMethod]) {
      throw new Error(`Méthode de valorisation non supportée: ${this.valuationMethod}`);
    }
  }
  
  /**
   * Calcule la valeur actuelle du stock
   * @param {Object} options - Options de calcul
   * @param {Date} options.date - Date à laquelle calculer la valeur (par défaut: maintenant)
   * @param {string[]} options.categories - Catégories à inclure dans le calcul
   * @returns {Promise<Object>} - Résultat de la valorisation
   */
  async calculateInventoryValue(options = {}) {
    try {
      // Récupérer les données d'inventaire
      const inventoryData = await this._getInventoryData(options);
      
      // Calculer la valeur selon la méthode configurée
      const valuationMethod = this.valuationMethods[this.valuationMethod];
      const valuationResult = await valuationMethod(inventoryData, options);
      
      // Ajouter les métadonnées
      valuationResult.metadata = {
        calculatedAt: new Date(),
        method: this.valuationMethod,
        parameters: options
      };
      
      return valuationResult;
    } catch (error) {
      console.error('Erreur lors du calcul de la valeur d\'inventaire:', error);
      throw new Error(`Échec du calcul de la valeur d'inventaire: ${error.message}`);
    }
  }
  
  /**
   * Calcule le coût d'une recette ou d'un plat
   * @param {Object} recipe - Recette à évaluer
   * @param {Array} recipe.ingredients - Ingrédients de la recette
   * @param {Object} options - Options de calcul
   * @param {boolean} options.includeOverhead - Inclure les frais généraux
   * @param {string} options.overheadMethod - Méthode d'allocation des frais (percentage, fixed)
   * @returns {Promise<Object>} - Résultat détaillé du calcul de coût
   */
  async calculateRecipeCost(recipe, options = {}) {
    try {
      if (!recipe || !recipe.ingredients || !Array.isArray(recipe.ingredients)) {
        throw new Error('Recette invalide ou ingrédients manquants');
      }
      
      // Options par défaut
      const includeOverhead = options.includeOverhead !== undefined ? options.includeOverhead : true;
      const overheadMethod = options.overheadMethod || 'percentage';
      
      // Récupérer les coûts des ingrédients
      const ingredientCostsPromises = recipe.ingredients.map(ingredient => 
        this._getIngredientCost(ingredient.id, ingredient.quantity, options)
      );
      
      const ingredientCosts = await Promise.all(ingredientCostsPromises);
      
      // Calculer le coût total des ingrédients
      const ingredientTotalCost = ingredientCosts.reduce((sum, cost) => sum + cost.totalCost, 0);
      
      // Calculer les frais généraux si demandé
      let overheadCost = 0;
      
      if (includeOverhead) {
        overheadCost = await this._calculateOverheadCost(ingredientTotalCost, recipe, overheadMethod);
      }
      
      // Calculer le coût total
      const totalCost = ingredientTotalCost + overheadCost;
      
      // Préparer le résultat détaillé
      return {
        recipeId: recipe.id,
        recipeName: recipe.name,
        ingredients: ingredientCosts,
        ingredientTotalCost,
        overheadCost,
        totalCost,
        costPerServing: totalCost / (recipe.servings || 1),
        metadata: {
          calculatedAt: new Date(),
          method: this.valuationMethod,
          includeOverhead,
          overheadMethod
        }
      };
    } catch (error) {
      console.error('Erreur lors du calcul du coût de la recette:', error);
      throw new Error(`Échec du calcul du coût de la recette: ${error.message}`);
    }
  }
  
  /**
   * Analyse la rentabilité d'un menu ou d'une catégorie de produits
   * @param {Object} options - Options d'analyse
   * @param {string} options.menuId - Identifiant du menu
   * @param {string} options.categoryId - Identifiant de la catégorie
   * @param {Date} options.startDate - Date de début de la période d'analyse
   * @param {Date} options.endDate - Date de fin de la période d'analyse
   * @returns {Promise<Object>} - Résultat de l'analyse de rentabilité
   */
  async analyzeProfitability(options = {}) {
    try {
      // Vérifier qu'au moins un identifiant est fourni
      if (!options.menuId && !options.categoryId) {
        throw new Error('Veuillez spécifier menuId ou categoryId');
      }
      
      // Récupérer les données de vente
      const salesData = await this._getSalesData(options);
      
      // Récupérer les coûts pour chaque produit vendu
      const productProfitability = [];
      
      for (const productSale of salesData.products) {
        // Récupérer la recette
        const recipe = await this._getRecipeForProduct(productSale.productId);
        
        if (!recipe) {
          console.warn(`Recette non trouvée pour le produit ${productSale.productId}`);
          continue;
        }
        
        // Calculer le coût
        const costResult = await this.calculateRecipeCost(recipe, options);
        
        // Calculer la rentabilité
        const totalRevenue = productSale.quantity * productSale.unitPrice;
        const totalCost = productSale.quantity * costResult.totalCost;
        const grossProfit = totalRevenue - totalCost;
        const marginPercentage = (grossProfit / totalRevenue) * 100;
        
        productProfitability.push({
          productId: productSale.productId,
          productName: productSale.productName,
          quantity: productSale.quantity,
          unitPrice: productSale.unitPrice,
          totalRevenue,
          unitCost: costResult.totalCost,
          totalCost,
          grossProfit,
          marginPercentage
        });
      }
      
      // Calculer les totaux
      const totalRevenue = productProfitability.reduce((sum, item) => sum + item.totalRevenue, 0);
      const totalCost = productProfitability.reduce((sum, item) => sum + item.totalCost, 0);
      const totalGrossProfit = productProfitability.reduce((sum, item) => sum + item.grossProfit, 0);
      const averageMarginPercentage = totalRevenue > 0 ? (totalGrossProfit / totalRevenue) * 100 : 0;
      
      // Préparer le résultat
      return {
        analysisType: options.menuId ? 'menu' : 'category',
        id: options.menuId || options.categoryId,
        period: {
          start: options.startDate,
          end: options.endDate
        },
        products: productProfitability,
        summary: {
          totalRevenue,
          totalCost,
          totalGrossProfit,
          averageMarginPercentage
        },
        metadata: {
          calculatedAt: new Date(),
          method: this.valuationMethod
        }
      };
    } catch (error) {
      console.error('Erreur lors de l\'analyse de rentabilité:', error);
      throw new Error(`Échec de l'analyse de rentabilité: ${error.message}`);
    }
  }
  
  /**
   * Détecte les pertes d'inventaire anormales
   * @param {Object} options - Options de détection
   * @param {Date} options.startDate - Date de début de la période
   * @param {Date} options.endDate - Date de fin de la période
   * @param {number} options.thresholdPercentage - Seuil de perte anormale (%)
   * @returns {Promise<Object>} - Résultat de la détection des pertes
   */
  async detectInventoryLosses(options = {}) {
    try {
      const startDate = options.startDate || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000); // 30 jours par défaut
      const endDate = options.endDate || new Date();
      const thresholdPercentage = options.thresholdPercentage || 5; // 5% par défaut
      
      // Récupérer les mouvements d'inventaire
      const inventoryMovements = await this._getInventoryMovements(startDate, endDate);
      
      // Analyser les mouvements pour détecter les pertes
      const losses = [];
      
      for (const productId in inventoryMovements) {
        const product = inventoryMovements[productId];
        
        // Calculer la perte
        const expectedEndingQuantity = product.startingQuantity + product.received - product.consumed;
        const actualEndingQuantity = product.endingQuantity;
        const loss = expectedEndingQuantity - actualEndingQuantity;
        
        // Calculer le pourcentage de perte
        const consumptionTotal = product.consumed || 1; // Éviter division par zéro
        const lossPercentage = (loss / consumptionTotal) * 100;
        
        // Vérifier si la perte dépasse le seuil
        if (loss > 0 && lossPercentage >= thresholdPercentage) {
          // Valoriser la perte
          const unitCost = await this._getProductUnitCost(productId);
          const lossValue = loss * unitCost;
          
          losses.push({
            productId,
            productName: product.name,
            startingQuantity: product.startingQuantity,
            endingQuantity: actualEndingQuantity,
            received: product.received,
            consumed: product.consumed,
            expectedEndingQuantity,
            loss,
            lossPercentage,
            unitCost,
            lossValue
          });
        }
      }
      
      // Trier par valeur de perte décroissante
      losses.sort((a, b) => b.lossValue - a.lossValue);
      
      // Calculer la perte totale
      const totalLossValue = losses.reduce((sum, item) => sum + item.lossValue, 0);
      
      return {
        period: {
          start: startDate,
          end: endDate
        },
        threshold: thresholdPercentage,
        losses,
        totalLossValue,
        metadata: {
          calculatedAt: new Date()
        }
      };
    } catch (error) {
      console.error('Erreur lors de la détection des pertes d\'inventaire:', error);
      throw new Error(`Échec de la détection des pertes d'inventaire: ${error.message}`);
    }
  }
  
  /**
   * Récupère les données d'inventaire
   * @param {Object} options - Options de récupération
   * @returns {Promise<Object>} - Données d'inventaire
   * @private
   */
  async _getInventoryData(options = {}) {
    if (!this.dataCollector) {
      throw new Error('DataCollector non initialisé');
    }
    
    return this.dataCollector.getInventoryData({
      currentOnly: options.currentOnly !== undefined ? options.currentOnly : true,
      categories: options.categories,
      valuationMethod: this.valuationMethod
    });
  }
  
  /**
   * Récupère les données de vente
   * @param {Object} options - Options de récupération
   * @returns {Promise<Object>} - Données de vente
   * @private
   */
  async _getSalesData(options = {}) {
    if (!this.dataCollector) {
      throw new Error('DataCollector non initialisé');
    }
    
    return this.dataCollector.getSalesData({
      startDate: options.startDate,
      endDate: options.endDate,
      menuId: options.menuId,
      categoryId: options.categoryId,
      includeDetails: true
    });
  }
  
  /**
   * Récupère la recette pour un produit
   * @param {string} productId - Identifiant du produit
   * @returns {Promise<Object|null>} - Recette ou null si non trouvée
   * @private
   */
  async _getRecipeForProduct(productId) {
    // À implémenter selon l'architecture du système
    // Cette méthode devrait récupérer la recette depuis une API ou une base de données
    
    // Exemple simplifié
    if (!this.dataCollector) {
      throw new Error('DataCollector non initialisé');
    }
    
    try {
      // Construire le chemin d'API approprié
      const apiPath = `/recipes/by-product/${productId}`;
      
      // Utiliser le client API du collecteur de données
      if (this.dataCollector.apiClients && this.dataCollector.apiClients.menu) {
        return await this.dataCollector.apiClients.menu.get(apiPath);
      }
      
      return null;
    } catch (error) {
      console.error(`Erreur lors de la récupération de la recette pour le produit ${productId}:`, error);
      return null;
    }
  }
  
  /**
   * Récupère le coût d'un ingrédient
   * @param {string} ingredientId - Identifiant de l'ingrédient
   * @param {number} quantity - Quantité nécessaire
   * @param {Object} options - Options supplémentaires
   * @returns {Promise<Object>} - Informations de coût
   * @private
   */
  async _getIngredientCost(ingredientId, quantity, options = {}) {
    try {
      // Récupérer le coût unitaire
      const unitCost = await this._getIngredientUnitCost(ingredientId, options);
      
      // Calculer le coût total
      const totalCost = unitCost * quantity;
      
      return {
        ingredientId,
        quantity,
        unitCost,
        totalCost
      };
    } catch (error) {
      console.error(`Erreur lors du calcul du coût de l'ingrédient ${ingredientId}:`, error);
      
      // Renvoyer une valeur par défaut en cas d'erreur
      return {
        ingredientId,
        quantity,
        unitCost: 0,
        totalCost: 0,
        error: error.message
      };
    }
  }
  
  /**
   * Récupère le coût unitaire d'un ingrédient
   * @param {string} ingredientId - Identifiant de l'ingrédient
   * @param {Object} options - Options supplémentaires
   * @returns {Promise<number>} - Coût unitaire
   * @private
   */
  async _getIngredientUnitCost(ingredientId, options = {}) {
    // Vérifier si un coût spécifique est configuré
    if (this.costConfiguration.specificCosts && 
        this.costConfiguration.specificCosts[ingredientId] !== undefined) {
      return this.costConfiguration.specificCosts[ingredientId];
    }
    
    if (!this.dataCollector) {
      throw new Error('DataCollector non initialisé');
    }
    
    // Récupérer les données d'inventaire pour cet ingrédient
    const inventoryItem = await this.dataCollector.getInventoryItemData(ingredientId);
    
    if (!inventoryItem || inventoryItem.unitCost === undefined) {
      // Utiliser un coût par défaut ou lever une erreur
      if (this.costConfiguration.defaultCost !== undefined) {
        return this.costConfiguration.defaultCost;
      }
      
      throw new Error(`Coût unitaire non trouvé pour l'ingrédient ${ingredientId}`);
    }
    
    return inventoryItem.unitCost;
  }
  
  /**
   * Récupère le coût unitaire d'un produit
   * @param {string} productId - Identifiant du produit
   * @returns {Promise<number>} - Coût unitaire
   * @private
   */
  async _getProductUnitCost(productId) {
    // À implémenter selon l'architecture du système
    // Cette méthode peut réutiliser d'autres méthodes comme _getIngredientUnitCost
    
    // Exemple simplifié
    // Vérifier si un coût spécifique est configuré
    if (this.costConfiguration.specificCosts && 
        this.costConfiguration.specificCosts[productId] !== undefined) {
      return this.costConfiguration.specificCosts[productId];
    }
    
    // Valeur par défaut
    return this.costConfiguration.defaultCost || 1.0;
  }
  
  /**
   * Récupère les mouvements d'inventaire pour une période
   * @param {Date} startDate - Date de début
   * @param {Date} endDate - Date de fin
   * @returns {Promise<Object>} - Mouvements d'inventaire par produit
   * @private
   */
  async _getInventoryMovements(startDate, endDate) {
    if (!this.dataCollector) {
      throw new Error('DataCollector non initialisé');
    }
    
    // Récupérer les mouvements d'inventaire
    // Cette méthode dépend de l'implémentation spécifique du système
    
    // Exemple simplifié
    return {}; // Placeholder
  }
  
  /**
   * Calcule les frais généraux pour une recette
   * @param {number} baseCost - Coût de base (ingrédients)
   * @param {Object} recipe - Recette
   * @param {string} method - Méthode d'allocation (percentage, fixed)
   * @returns {Promise<number>} - Montant des frais généraux
   * @private
   */
  async _calculateOverheadCost(baseCost, recipe, method = 'percentage') {
    // Récupérer la configuration des frais généraux
    const overheadConfig = this.costConfiguration.overhead || {};
    
    switch (method) {
      case 'percentage':
        // Pourcentage du coût de base
        const percentage = overheadConfig.percentage || 15; // 15% par défaut
        return baseCost * (percentage / 100);
      
      case 'fixed':
        // Montant fixe par recette ou par catégorie
        if (recipe.category && overheadConfig.byCategory && 
            overheadConfig.byCategory[recipe.category] !== undefined) {
          return overheadConfig.byCategory[recipe.category];
        }
        
        return overheadConfig.fixedAmount || 0;
      
      case 'hybrid':
        // Combinaison de fixe et pourcentage
        const fixedComponent = overheadConfig.fixedComponent || 0;
        const percentageComponent = overheadConfig.percentageComponent || 0;
        return fixedComponent + (baseCost * (percentageComponent / 100));
      
      default:
        return 0;
    }
  }
  
  /**
   * Calcule la valorisation par méthode du coût moyen pondéré
   * @param {Object} inventoryData - Données d'inventaire
   * @param {Object} options - Options de calcul
   * @returns {Promise<Object>} - Résultat de la valorisation
   * @private
   */
  async _calculateWeightedAverage(inventoryData, options = {}) {
    // La méthode du coût moyen pondéré est la plus simple
    // Elle utilise le coût unitaire moyen déjà calculé pour chaque article
    
    let totalValue = 0;
    const items = [];
    
    // Parcourir les éléments d'inventaire
    for (const item of inventoryData.items || []) {
      const itemValue = item.quantity * item.unitCost;
      totalValue += itemValue;
      
      items.push({
        productId: item.productId,
        name: item.name,
        quantity: item.quantity,
        unit: item.unit,
        unitCost: item.unitCost,
        totalValue: itemValue
      });
    }
    
    // Regrouper par catégorie
    const categories = this._groupByCategory(items);
    
    return {
      totalValue,
      items,
      categories,
      method: 'weighted_average'
    };
  }
  
  /**
   * Calcule la valorisation par méthode FIFO (First In, First Out)
   * @param {Object} inventoryData - Données d'inventaire
   * @param {Object} options - Options de calcul
   * @returns {Promise<Object>} - Résultat de la valorisation
   * @private
   */
  async _calculateFIFO(inventoryData, options = {}) {
    // Pour FIFO, nous aurions besoin de l'historique des lots
    // Mais comme nous n'avons pas ces détails ici, nous utilisons l'approximation
    
    // Dans un système réel, cette méthode nécessiterait:
    // 1. Récupérer tous les lots d'achat encore en stock
    // 2. Valoriser les unités les plus anciennes aux prix les plus anciens
    
    // Pour l'exemple, nous simulons en réduisant légèrement le coût moyen
    const weightedAverageResult = await this._calculateWeightedAverage(inventoryData, options);
    
    const fifoAdjustment = 0.95; // Réduction de 5% par rapport au coût moyen
    const items = weightedAverageResult.items.map(item => ({
      ...item,
      unitCost: item.unitCost * fifoAdjustment,
      totalValue: item.quantity * (item.unitCost * fifoAdjustment)
    }));
    
    const totalValue = items.reduce((sum, item) => sum + item.totalValue, 0);
    const categories = this._groupByCategory(items);
    
    return {
      totalValue,
      items,
      categories,
      method: 'fifo'
    };
  }
  
  /**
   * Calcule la valorisation par méthode LIFO (Last In, First Out)
   * @param {Object} inventoryData - Données d'inventaire
   * @param {Object} options - Options de calcul
   * @returns {Promise<Object>} - Résultat de la valorisation
   * @private
   */
  async _calculateLIFO(inventoryData, options = {}) {
    // Pour LIFO, nous aurions besoin de l'historique des lots
    // Mais comme nous n'avons pas ces détails ici, nous utilisons l'approximation
    
    // Dans un système réel, cette méthode nécessiterait:
    // 1. Récupérer tous les lots d'achat encore en stock
    // 2. Valoriser les unités les plus récentes aux prix les plus récents
    
    // Pour l'exemple, nous simulons en augmentant légèrement le coût moyen
    const weightedAverageResult = await this._calculateWeightedAverage(inventoryData, options);
    
    const lifoAdjustment = 1.05; // Augmentation de 5% par rapport au coût moyen
    const items = weightedAverageResult.items.map(item => ({
      ...item,
      unitCost: item.unitCost * lifoAdjustment,
      totalValue: item.quantity * (item.unitCost * lifoAdjustment)
    }));
    
    const totalValue = items.reduce((sum, item) => sum + item.totalValue, 0);
    const categories = this._groupByCategory(items);
    
    return {
      totalValue,
      items,
      categories,
      method: 'lifo'
    };
  }
  
  /**
   * Calcule la valorisation par méthode d'identification spécifique
   * @param {Object} inventoryData - Données d'inventaire
   * @param {Object} options - Options de calcul
   * @returns {Promise<Object>} - Résultat de la valorisation
   * @private
   */
  async _calculateSpecificIdentification(inventoryData, options = {}) {
    // Cette méthode nécessiterait des identifiants uniques pour chaque lot
    // Pour l'exemple, nous utilisons simplement la même valeur que le coût moyen pondéré
    
    return this._calculateWeightedAverage(inventoryData, options);
  }
  
  /**
   * Regroupe les éléments d'inventaire par catégorie
   * @param {Array} items - Éléments d'inventaire
   * @returns {Array} - Groupes par catégorie
   * @private
   */
  _groupByCategory(items) {
    const categoryMap = {};
    
    for (const item of items) {
      const category = item.category || 'Non catégorisé';
      
      if (!categoryMap[category]) {
        categoryMap[category] = {
          category,
          totalValue: 0,
          itemCount: 0
        };
      }
      
      categoryMap[category].totalValue += item.totalValue;
      categoryMap[category].itemCount += 1;
    }
    
    return Object.values(categoryMap);
  }
}

module.exports = { InventoryCalculator };
