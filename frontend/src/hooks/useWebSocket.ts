import { useState, useEffect, useCallback, useRef } from 'react';
import type { ExecutionMessage } from '@/types';

interface UseWebSocketOptions {
  onMessage?: (message: ExecutionMessage) => void;
  onError?: (error: Event) => void;
  onClose?: () => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<ExecutionMessage[]>([]);
  const socketRef = useRef<WebSocket | null>(null);

  const connect = useCallback((sessionId: string) => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const socket = new WebSocket(`${protocol}//${host}/ws/execute/${sessionId}`);

    socket.onopen = () => {
      setConnected(true);
    };

    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as ExecutionMessage;
        setMessages((prev) => [...prev, message]);
        options.onMessage?.(message);
      } catch {
        console.error('Failed to parse WebSocket message:', event.data);
      }
    };

    socket.onerror = (error) => {
      options.onError?.(error);
    };

    socket.onclose = () => {
      setConnected(false);
      options.onClose?.();
    };

    socketRef.current = socket;
  }, [options]);

  const disconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
    setConnected(false);
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  useEffect(() => {
    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, []);

  return {
    connected,
    messages,
    connect,
    disconnect,
    clearMessages,
  };
}
