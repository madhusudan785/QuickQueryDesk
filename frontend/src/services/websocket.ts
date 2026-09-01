/* WebSocket service with auto-reconnect */

type MessageHandler = (event: string, data: unknown) => void;

export class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private handlers: MessageHandler[] = [];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  private intentionallyClosed = false;

  constructor(url: string) {
    this.url = url;
  }

  connect(): void {
    this.intentionallyClosed = false;

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const fullUrl = `${protocol}//${window.location.host}${this.url}`;
      this.ws = new WebSocket(fullUrl);

      this.ws.onopen = () => {
        console.log(`[WS] Connected to ${this.url}`);
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          this.handlers.forEach((handler) => handler(parsed.event, parsed.data));
        } catch (err) {
          console.error('[WS] Failed to parse message:', err);
        }
      };

      this.ws.onclose = () => {
        console.log(`[WS] Disconnected from ${this.url}`);
        if (!this.intentionallyClosed) {
          this.attemptReconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error('[WS] Error:', error);
      };
    } catch (err) {
      console.error('[WS] Failed to connect:', err);
      this.attemptReconnect();
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('[WS] Max reconnect attempts reached');
      return;
    }

    // Exponential backoff: 1s, 2s, 4s, 8s, ...up to 30s
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    this.reconnectAttempts++;
    console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, delay);
  }

  onMessage(handler: MessageHandler): void {
    this.handlers.push(handler);
  }

  removeHandler(handler: MessageHandler): void {
    this.handlers = this.handlers.filter((h) => h !== handler);
  }

  disconnect(): void {
    this.intentionallyClosed = true;
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}
