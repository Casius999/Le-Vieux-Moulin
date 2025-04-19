const express = require('express');
const cors = require('cors');
const compression = require('compression');
const helmet = require('helmet');
const morgan = require('morgan');
const path = require('path');

const dashboardRoutes = require('./routes/dashboard');
const stocksRoutes = require('./routes/stocks');
const salesRoutes = require('./routes/sales');
const marketingRoutes = require('./routes/marketing');
const financeRoutes = require('./routes/finance');
const staffRoutes = require('./routes/staff');

const errorMiddleware = require('./middleware/error');
const logger = require('./utils/logger');

const app = express();

// Middleware
app.use(cors({
  origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
  credentials: true,
}));
app.use(helmet());
app.use(compression());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Logging HTTP requests
app.use(morgan('dev', {
  stream: { write: message => logger.http(message.trim()) },
  skip: () => process.env.NODE_ENV === 'test'
}));

// API Routes
app.use('/api/dashboard', dashboardRoutes);
app.use('/api/stocks', stocksRoutes);
app.use('/api/sales', salesRoutes);
app.use('/api/marketing', marketingRoutes);
app.use('/api/finance', financeRoutes);
app.use('/api/staff', staffRoutes);

// Serve static files in production
if (process.env.NODE_ENV === 'production') {
  app.use(express.static(path.join(__dirname, '../frontend/build')));
  
  app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, '../frontend/build', 'index.html'));
  });
}

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok' });
});

// Error handling middleware
app.use(errorMiddleware);

module.exports = app;
