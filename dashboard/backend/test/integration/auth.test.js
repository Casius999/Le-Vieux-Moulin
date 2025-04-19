const request = require('supertest');
const { app } = require('../../app');
const jwt = require('jsonwebtoken');
const config = require('../../config');

// Mock des modules externes
jest.mock('../../utils/apiClient', () => {
  const originalModule = jest.requireActual('../../utils/apiClient');
  
  return {
    ...originalModule,
    client: {
      post: jest.fn(),
      get: jest.fn(),
    },
    callApi: jest.fn((fn) => fn()),
  };
});

const { client, callApi } = require('../../utils/apiClient');

describe('Auth API Routes', () => {
  // Fonction utilitaire pour générer un token valide pour les tests
  const generateValidToken = (user = { id: '123', email: 'test@example.com', role: 'admin' }) => {
    return jwt.sign(user, config.jwtSecret, { expiresIn: '1h' });
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('POST /api/auth/login', () => {
    it('should return 400 when email is missing', async () => {
      const response = await request(app)
        .post('/api/auth/login')
        .send({ password: 'password' });

      expect(response.statusCode).toBe(400);
      expect(response.body).toHaveProperty('success', false);
    });

    it('should return 400 when password is missing', async () => {
      const response = await request(app)
        .post('/api/auth/login')
        .send({ email: 'test@example.com' });

      expect(response.statusCode).toBe(400);
      expect(response.body).toHaveProperty('success', false);
    });

    it('should return 200 and token when login is successful', async () => {
      const mockUser = {
        id: '123',
        name: 'Test User',
        email: 'test@example.com',
        role: 'admin',
      };

      client.post.mockResolvedValueOnce({
        data: {
          user: mockUser,
        },
      });

      const response = await request(app)
        .post('/api/auth/login')
        .send({ email: 'test@example.com', password: 'password' });

      expect(response.statusCode).toBe(200);
      expect(response.body).toHaveProperty('success', true);
      expect(response.body).toHaveProperty('token');
      expect(response.body.user).toMatchObject({
        id: mockUser.id,
        name: mockUser.name,
        email: mockUser.email,
        role: mockUser.role,
      });
    });

    it('should return 401 when credentials are invalid', async () => {
      const error = new Error('Invalid credentials');
      error.response = {
        status: 401,
        data: { message: 'Invalid credentials' },
      };

      client.post.mockRejectedValueOnce(error);

      const response = await request(app)
        .post('/api/auth/login')
        .send({ email: 'test@example.com', password: 'wrong-password' });

      expect(response.statusCode).toBe(401);
      expect(response.body).toHaveProperty('success', false);
    });
  });

  // Tests pour /api/auth/me - vérification du profil utilisateur
  describe('GET /api/auth/me', () => {
    it('should return 401 if no token is provided', async () => {
      const response = await request(app).get('/api/auth/me');

      expect(response.statusCode).toBe(401);
    });

    it('should return user profile if valid token is provided', async () => {
      const mockUser = {
        id: '123',
        name: 'Test User',
        email: 'test@example.com',
        role: 'admin',
      };

      client.get.mockResolvedValueOnce({
        data: mockUser,
      });

      const token = generateValidToken(mockUser);

      const response = await request(app)
        .get('/api/auth/me')
        .set('Authorization', `Bearer ${token}`);

      expect(response.statusCode).toBe(200);
      expect(response.body).toHaveProperty('success', true);
      expect(response.body.user).toMatchObject({
        id: mockUser.id,
        name: mockUser.name,
        email: mockUser.email,
        role: mockUser.role,
      });
    });
  });

  // Autres tests pour refresh token, logout, etc.
});
