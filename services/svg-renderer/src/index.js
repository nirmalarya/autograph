const express = require('express');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 8096;

// Middleware
app.use(cors());
app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'svg-renderer',
    version: '3.0.0',
    timestamp: new Date().toISOString()
  });
});

// SVG rendering endpoint (placeholder for now)
app.post('/render', (req, res) => {
  res.json({
    message: 'SVG rendering endpoint - to be implemented',
    status: 'not_implemented'
  });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`SVG Renderer service listening on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
});
