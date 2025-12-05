const CONFIG = {
  environment: 'development',
  api: {
    development: 'http://localhost:5001/api',
    production: 'https://briefen.me/api'
  },
  web: {
    development: 'http://localhost:5001',
    production: 'https://briefen.me'
  }
};

const API_BASE = CONFIG.api[CONFIG.environment];
const WEB_BASE = CONFIG.web[CONFIG.environment];