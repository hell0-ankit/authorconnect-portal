import { useEffect, useRef, useState } from 'react';
import { ticketWebSocketUrl } from '../services/websocket';

const MAX_RETRIES = 6;

export default function useTicketWebSocket(path, onEvent, enabled = true) {
  const [status, setStatus] = useState('disconnected');
  const [retryNumber, setRetryNumber] = useState(0);
  const onEventRef = useRef(onEvent);
  const token = typeof window === 'undefined'
    ? null
    : window.localStorage.getItem('access_token');

  useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  useEffect(() => {
    if (!enabled || !path || !token) return undefined;

    let active = true;
    let socket;
    let retryTimer;
    let retryCount = 0;
    let stableConnectionTimer;

    const connect = () => {
      if (!active) return;
      setStatus(retryCount ? 'reconnecting' : 'connecting');

      try {
        socket = new WebSocket(ticketWebSocketUrl(path));
      } catch {
        setStatus('disconnected');
        return;
      }

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === 'auth_required') {
            if (socket.readyState === WebSocket.OPEN) {
              socket.send(JSON.stringify({ type: 'authenticate', token }));
            }
            return;
          }
          if (payload.type === 'connection') {
            setStatus('connected');
            stableConnectionTimer = window.setTimeout(() => {
              retryCount = 0;
            }, 10000);
            return;
          }
          if (!active) return;
          onEventRef.current(payload);
        } catch {
          console.warn('Received an invalid ticket WebSocket event.');
        }
      };

      socket.onerror = () => {
        if (active) setStatus('reconnecting');
      };

      socket.onclose = () => {
        window.clearTimeout(stableConnectionTimer);
        if (!active) return;
        retryCount += 1;
        if (retryCount > MAX_RETRIES) {
          setStatus('disconnected');
          return;
        }

        setStatus('reconnecting');
        const delay = Math.min(1000 * (2 ** (retryCount - 1)), 10000);
        retryTimer = window.setTimeout(connect, delay);
      };
    };

    connect();
    return () => {
      active = false;
      window.clearTimeout(retryTimer);
      window.clearTimeout(stableConnectionTimer);
      if (socket) {
        socket.onclose = null;
        socket.close();
      }
    };
  }, [enabled, path, retryNumber, token]);

  const retry = () => {
    setRetryNumber((value) => value + 1);
  };

  return {
    status: enabled && path && token ? status : 'disconnected',
    retry,
  };
}
