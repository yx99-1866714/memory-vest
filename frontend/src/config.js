// Central API base URL — reads VITE_API_URL in production, falls back to localhost for dev
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default API_BASE;
