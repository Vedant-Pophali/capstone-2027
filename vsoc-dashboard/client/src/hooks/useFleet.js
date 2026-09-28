import { useState, useEffect, useCallback, useRef } from 'react';
import { Client } from '@stomp/stompjs';
import SockJS from 'sockjs-client/dist/sockjs';
import { apiService } from '../services/api';

const WS_URL = import.meta.env.VITE_WS_URL || 'http://localhost:8085/ws';

/**
 * Custom hook that manages fleet data fetching + STOMP WebSocket subscription.
 * Decoupled from any UI component — returns pure data and actions.
 */
export function useFleet() {
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [connected, setConnected] = useState(false);
  const [events, setEvents] = useState([]); // activity feed
  const clientRef = useRef(null);

  // --- Fetch fleet data ---
  const fetchVehicles = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiService.fetchVehicles();
      setVehicles(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // --- Add event to activity feed ---
  const addEvent = useCallback((type, vehicleId, timestamp) => {
    setEvents(prev => {
      const newEvent = { id: Date.now(), type, vehicleId, timestamp };
      return [newEvent, ...prev].slice(0, 50); // keep last 50
    });
  }, []);

  // --- WebSocket connection ---
  useEffect(() => {
    const client = new Client({
      webSocketFactory: () => new SockJS(WS_URL),
      reconnectDelay: 5000,
      heartbeatIncoming: 10000,
      heartbeatOutgoing: 10000,
      onConnect: () => {
        setConnected(true);
        client.subscribe('/topic/fleet', (message) => {
          try {
            const event = JSON.parse(message.body);
            handleWebSocketEvent(event);
          } catch (e) {
            console.error('Failed to parse WebSocket message:', e);
          }
        });
      },
      onDisconnect: () => setConnected(false),
      onStompError: (frame) => {
        console.error('STOMP error:', frame.headers?.message);
        setConnected(false);
      },
    });

    clientRef.current = client;
    client.activate();

    return () => {
      client.deactivate();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleWebSocketEvent = useCallback((event) => {
    const { type, vehicle, vehicleId, timestamp } = event;

    setVehicles(prev => {
      switch (type) {
        case 'CREATED':
          if (vehicle && !prev.find(v => v.id === vehicle.id)) {
            return [...prev, vehicle];
          }
          return prev;

        case 'DELETED':
          return prev.filter(v => v.id !== vehicleId);

        case 'STATUS_CHANGED':
          return prev.map(v => v.id === vehicle?.id ? vehicle : v);

        default:
          return prev;
      }
    });

    addEvent(type, vehicleId || vehicle?.id, timestamp);
  }, [addEvent]);

  // Initial fetch
  useEffect(() => {
    fetchVehicles();
  }, [fetchVehicles]);

  return {
    vehicles,
    loading,
    error,
    connected,
    events,
    refetch: fetchVehicles,
  };
}
