const trimTrailingSlash = (value: string) => value.replace(/\/+$/, '');

const configuredApiUrl = import.meta.env.VITE_API_URL?.trim();

export const API_BASE_URL = trimTrailingSlash(
  configuredApiUrl || 'http://localhost:8000'
);

const toWebSocketUrl = (apiUrl: string) => {
  const url = new URL(apiUrl);
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  return trimTrailingSlash(url.toString());
};

export const WS_BASE_URL = trimTrailingSlash(
  import.meta.env.VITE_WS_URL?.trim() || toWebSocketUrl(API_BASE_URL)
);

export const DEMO_MODE = ['true', '1', 'fallback'].includes(
  String(import.meta.env.VITE_DEMO_MODE || 'fallback').toLowerCase()
);
