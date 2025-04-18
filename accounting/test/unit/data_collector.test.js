/**
 * Tests unitaires pour le module DataCollector
 */

const { DataCollector } = require('../../common/data_collector');
const { ConfigManager } = require('../../common/config_manager');

// Mock des dépendances
jest.mock('../../common/config_manager', () => ({
  ConfigManager: {
    getConfigManager: jest.fn().mockReturnValue({
      getConfig: jest.fn().mockReturnValue({})
    })
  }
}));

jest.mock('../../integration/api_connectors/api_client', () => ({
  ApiClient: jest.fn().mockImplementation(() => ({
    get: jest.fn().mockResolvedValue({ data: {} }),
    post: jest.fn().mockResolvedValue({ data: {} })
  }))
}));

jest.mock('../../common/connection_pool', () => ({
  ConnectionPool: jest.fn().mockImplementation(() => ({
    getConnection: jest.fn().mockResolvedValue({
      query: jest.fn().mockResolvedValue({ rows: [] }),
      release: jest.fn()
    })
  }))
}));

describe('DataCollector', () => {
  let dataCollector;
  
  beforeEach(() => {
    // Réinitialiser les mocks
    jest.clearAllMocks();
    
    // Créer une instance du DataCollector avec la configuration de test
    dataCollector = new DataCollector({
      apiConfig: {
        endpoints: {
          pos: {
            baseUrl: 'http://api.local/pos',
            auth: { type: 'bearer', token: 'test-token' }
          }
        }
      },
      dbConfig: {
        connections: {
          sales: {
            host: 'localhost',
            port: 5432,
            database: 'test_db',
            user: 'test_user',
            password: 'test_password'
          }
        }
      },
      cachingConfig: { enabled: true, ttl: 60 }
    });
  });
  
  describe('constructor', () => {
    it('should initialize with default values when no options are provided', () => {
      const defaultCollector = new DataCollector();
      expect(defaultCollector).toBeInstanceOf(DataCollector);
      expect(defaultCollector.apiConfig).toEqual({});
      expect(defaultCollector.dbConfig).toEqual({});
      expect(defaultCollector.cachingConfig).toEqual({ enabled: true, ttl: 300 });
    });
    
    it('should initialize with provided options', () => {
      expect(dataCollector.apiConfig.endpoints.pos.baseUrl).toBe('http://api.local/pos');
      expect(dataCollector.dbConfig.connections.sales.host).toBe('localhost');
      expect(dataCollector.cachingConfig.ttl).toBe(60);
    });
  });
  
  describe('getSalesData', () => {
    it('should return cached data if available', async () => {
      // Préparer les données de cache
      const cachedData = { transactions: [{ id: 'test1' }] };
      const cacheKey = 'sales_{"startDate":"2025-04-01","endDate":"2025-04-15"}';
      
      // Simuler des données en cache
      dataCollector.cache.set(cacheKey, {
        data: cachedData,
        expiresAt: Date.now() + 1000 * 60 // 1 minute dans le futur
      });
      
      // Appeler la méthode avec les mêmes paramètres
      const result = await dataCollector.getSalesData({
        startDate: '2025-04-01',
        endDate: '2025-04-15'
      });
      
      // Vérifier que les données en cache sont retournées
      expect(result).toEqual(cachedData);
    });
    
    it('should fetch data from API when no cache is available', async () => {
      // Mock de réponse API
      const apiResponse = {
        transactions: [{ id: 'test2' }],
        total: 1
      };
      
      // Configurer le mock pour retourner cette réponse
      dataCollector._clients = {
        pos: {
          get: jest.fn().mockResolvedValue({ data: apiResponse })
        }
      };
      
      // Appeler la méthode
      const result = await dataCollector.getSalesData({
        startDate: '2025-04-01',
        endDate: '2025-04-15'
      });
      
      // Vérifier que l'API a été appelée correctement
      expect(dataCollector._clients.pos.get).toHaveBeenCalledWith('/sales', {
        params: expect.objectContaining({
          startDate: expect.any(String),
          endDate: expect.any(String)
        })
      });
      
      // Vérifier que les données retournées sont correctes
      expect(result).toEqual(apiResponse);
    });
    
    it('should handle errors properly', async () => {
      // Configurer le mock pour lancer une erreur
      dataCollector._clients = {
        pos: {
          get: jest.fn().mockRejectedValue(new Error('API Error'))
        }
      };
      
      // Vérifier que l'erreur est propagée
      await expect(dataCollector.getSalesData({
        startDate: '2025-04-01',
        endDate: '2025-04-15'
      })).rejects.toThrow('Échec de récupération des données de ventes: API Error');
    });
  });
  
  describe('getExpensesData', () => {
    it('should fetch and format expenses data correctly', async () => {
      // Mock de réponse API
      const apiResponse = {
        purchases: [
          { 
            id: 'exp1', 
            invoice_date: '2025-04-10',
            supplier: 'Fournisseur Test',
            total_amount: 150.00,
            items: [
              { id: 'item1', description: 'Produit 1', amount: 100.00 },
              { id: 'item2', description: 'Produit 2', amount: 50.00 }
            ]
          }
        ],
        total: 1
      };
      
      // Configurer le mock pour retourner cette réponse
      dataCollector._clients = {
        expenses: {
          get: jest.fn().mockResolvedValue({ data: apiResponse })
        }
      };
      
      // Appeler la méthode
      const result = await dataCollector.getExpensesData({
        startDate: '2025-04-01',
        endDate: '2025-04-15'
      });
      
      // Vérifier que l'API a été appelée correctement
      expect(dataCollector._clients.expenses.get).toHaveBeenCalledWith('/expenses', {
        params: expect.objectContaining({
          startDate: expect.any(String),
          endDate: expect.any(String)
        })
      });
      
      // Vérifier que les données retournées sont correctes
      expect(result).toEqual(apiResponse);
    });
  });
  
  describe('getInventoryData', () => {
    it('should fetch inventory data with correct parameters', async () => {
      // Mock de réponse API
      const apiResponse = {
        timestamp: new Date().toISOString(),
        totalValue: 5000.00,
        items: [
          { productId: 'prod1', name: 'Farine', quantity: 50, unit: 'kg', unitCost: 2.5, totalValue: 125.00 },
          { productId: 'prod2', name: 'Huile', quantity: 20, unit: 'l', unitCost: 3.75, totalValue: 75.00 }
        ]
      };
      
      // Configurer le mock pour retourner cette réponse
      dataCollector._clients = {
        inventory: {
          get: jest.fn().mockResolvedValue({ data: apiResponse })
        }
      };
      
      // Appeler la méthode
      const result = await dataCollector.getInventoryData({
        currentOnly: true,
        categories: ['ingrédients']
      });
      
      // Vérifier que l'API a été appelée correctement
      expect(dataCollector._clients.inventory.get).toHaveBeenCalledWith('/inventory/valuation', {
        params: expect.objectContaining({
          currentOnly: true,
          categories: 'ingrédients'
        })
      });
      
      // Vérifier que les données retournées sont correctes
      expect(result).toEqual(apiResponse);
    });
  });
  
  describe('cache management', () => {
    it('should cache data with correct TTL', async () => {
      // Espionner la méthode _setCachedData
      const spy = jest.spyOn(dataCollector, '_setCachedData');
      
      // Mock de réponse API
      const apiResponse = { data: [{ id: 'test3' }] };
      
      // Configurer le mock pour retourner cette réponse
      dataCollector._clients = {
        pos: {
          get: jest.fn().mockResolvedValue({ data: apiResponse })
        }
      };
      
      // Appeler la méthode
      await dataCollector.getSalesData({ startDate: '2025-04-01', endDate: '2025-04-15' });
      
      // Vérifier que _setCachedData a été appelée avec les bons paramètres
      expect(spy).toHaveBeenCalledWith(
        expect.any(String),
        apiResponse,
        dataCollector.cachingConfig.ttl
      );
      
      // Restaurer le spy
      spy.mockRestore();
    });
    
    it('should not use cache when caching is disabled', async () => {
      // Créer une instance avec caching désactivé
      const noCacheCollector = new DataCollector({
        cachingConfig: { enabled: false }
      });
      
      // Espionner les méthodes de cache
      const getCache = jest.spyOn(noCacheCollector, '_getCachedData');
      const setCache = jest.spyOn(noCacheCollector, '_setCachedData');
      
      // Mock de réponse API
      noCacheCollector._clients = {
        pos: {
          get: jest.fn().mockResolvedValue({ data: { transactions: [] } })
        }
      };
      
      // Appeler la méthode
      await noCacheCollector.getSalesData({ startDate: '2025-04-01', endDate: '2025-04-15' });
      
      // Vérifier que les méthodes de cache n'ont pas été utilisées
      expect(getCache).not.toHaveBeenCalled();
      expect(setCache).not.toHaveBeenCalled();
      
      // Restaurer les spies
      getCache.mockRestore();
      setCache.mockRestore();
    });
  });
});
