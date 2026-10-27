export function ticketWebSocketUrl(path) {
  const configuredSocketUrl = import.meta.env.VITE_WS_BASE_URL;
  let baseUrl;

  if (configuredSocketUrl) {
    baseUrl = configuredSocketUrl;
  } else {
    const apiUrl = new URL(
      import.meta.env.VITE_API_BASE_URL || '/api/v1',
      window.location.origin,
    );
    const protocol = apiUrl.protocol === 'https:' ? 'wss:' : 'ws:';
    baseUrl = `${protocol}//${apiUrl.host}`;
  }

  return new URL(path, baseUrl).toString();
}
