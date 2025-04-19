const { login, refreshToken, logout, getCurrentUser } = require('../../controllers/authController');
const { client } = require('../../utils/apiClient');

// Mock des modules externes
jest.mock('../../utils/apiClient', () => ({
  client: {
    post: jest.fn(),
    get: jest.fn(),
  },
  callApi: jest.fn((fn) => fn()),
}));

jest.mock('jsonwebtoken', () => ({
  sign: jest.fn(() => 'mock-token'),
}));

jest.mock('../../utils/logger', () => ({
  setupLogger: jest.fn(() => ({
    info: jest.fn(),
    error: jest.fn(),
    debug: jest.fn(),
  })),
}));

// Préparation des objets request, response et next pour les tests
const mockRequest = (body = {}, user = null) => ({
  body,
  user,
});

const mockResponse = () => {
  const res = {};
  res.status = jest.fn().mockReturnValue(res);
  res.json = jest.fn().mockReturnValue(res);
  return res;
};

const mockNext = jest.fn();

describe('AuthController', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('login', () => {
    it('should return 400 if email or password is missing', async () => {
      const req = mockRequest({ email: 'test@example.com' }); // Pas de mot de passe
      const res = mockResponse();
      
      await login(req, res, mockNext);
      
      expect(res.status).toHaveBeenCalledWith(400);
      expect(res.json).toHaveBeenCalledWith(
        expect.objectContaining({
          success: false,
          message: expect.any(String),
        })
      );
    });

    it('should return 200 with token on successful login', async () => {
      const req = mockRequest({ email: 'test@example.com', password: 'password' });
      const res = mockResponse();
      
      const userData = {
        user: {
          id: '123',
          name: 'Test User',
          email: 'test@example.com',
          role: 'admin',
        },
      };
      
      client.post.mockResolvedValue({ data: userData });
      
      await login(req, res, mockNext);
      
      expect(client.post).toHaveBeenCalledWith('/auth/login', { email: 'test@example.com', password: 'password' });
      expect(res.status).toHaveBeenCalledWith(200);
      expect(res.json).toHaveBeenCalledWith(
        expect.objectContaining({
          success: true,
          token: 'mock-token',
          user: expect.objectContaining({
            id: '123',
            name: 'Test User',
            email: 'test@example.com',
            role: 'admin',
          }),
        })
      );
    });

    it('should handle authentication errors', async () => {
      const req = mockRequest({ email: 'test@example.com', password: 'wrong-password' });
      const res = mockResponse();
      
      const error = new Error('Invalid credentials');
      error.statusCode = 401;
      client.post.mockRejectedValue(error);
      
      await login(req, res, mockNext);
      
      expect(res.status).toHaveBeenCalledWith(401);
      expect(res.json).toHaveBeenCalledWith(
        expect.objectContaining({
          success: false,
          message: 'Email ou mot de passe invalide',
        })
      );
    });
  });

  // Tests supplémentaires pour refreshToken, logout, getCurrentUser...
});
