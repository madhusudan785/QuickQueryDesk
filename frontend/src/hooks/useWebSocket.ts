/* Hook: subscribes to a WebSocket endpoint and dispatches events to a handler.
 *
 * Wraps WebSocketService (see services/websocket.ts) with the JWT from
 * localStorage and proper connect/cleanup tied to the component lifecycle.
 * REST endpoints remain the source of truth — this only triggers a
 * re-fetch or local update when a live event arrives; it never replaces
 * the initial load.
 */

import { useEffect, useRef } from 'react';
import { WebSocketService } from '../services/websocket';

type MessageHandler = (event: string, data: unknown) => void;

export function useWebSocket(path: '/ws/agent' | '/ws/employee', onMessage: MessageHandler) {
  const handlerRef = useRef(onMessage);
  handlerRef.current = onMessage;

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    const service = new WebSocketService(`${path}?token=${encodeURIComponent(token)}`);
    const handler: MessageHandler = (event, data) => handlerRef.current(event, data);

    service.onMessage(handler);
    service.connect();

    return () => {
      service.removeHandler(handler);
      service.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path]);
}
