import { useState, useEffect, useRef, useCallback } from 'react';
import Dashboard from './components/Dashboard';
import DualDashboard from './components/DualDashboard';
import AlgorithmChart from './components/AlgorithmChart';
import './App.css';

const WS_URL = 'ws://localhost:8000/ws';
const API_URL = 'http://localhost:8000';

function App() {
  const [viewMode, setViewMode] = useState('single'); // 'single' or 'dual'
  const [simState, setSimState] = useState(null);
  const [dualState, setDualState] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [isDualRunning, setIsDualRunning] = useState(false);
  const [error, setError] = useState(null);
  const [simSetupConfig, setSimSetupConfig] = useState({
    num_drivers: 5,
    num_orders: 15,
    city: "Pune, India",
    routing_mode: "dynamic",
    manual_algorithm: "dijkstra",
    speed: 1
  });
  const [debugRouteData, setDebugRouteData] = useState(null);
  const [debugLoading, setDebugLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(false);

  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);

  const connectWebSocket = useCallback(() => {
    // Prevent multiple simultaneous connection attempts
    if (
      wsRef.current && 
      (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }

    try {
      console.log('[WS] Connecting to:', WS_URL);
      const ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        setIsConnected(true);
        setError(null);
        console.log('[WS] Connected');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type !== 'pong') {
            if (data.mode === 'dual') {
              setDualState(data);
              setIsDualRunning(data.is_running);
            } else {
              setSimState(data);
              setIsRunning(data.is_running);
              setIsInitializing(false);
            }
          }
        } catch (e) {
          console.error('[WS] Parse error:', e);
        }
      };

      ws.onclose = (event) => {
        setIsConnected(false);
        wsRef.current = null;
        
        // Only reconnect if the closure wasn't intentional (clean-up)
        if (!event.wasClean) {
          console.log('[WS] Disconnected, attempting reconnect in 3s...');
          reconnectTimer.current = setTimeout(connectWebSocket, 3000);
        } else {
          console.log('[WS] Disconnected (Clean)');
        }
      };

      ws.onerror = (e) => {
        // Only log error if not in middle of closing
        if (ws.readyState !== WebSocket.CLOSED) {
          console.error('[WS] Error:', e);
          setError('WebSocket connection failed. Is the backend running?');
        }
      };

      wsRef.current = ws;
    } catch (e) {
      setError('Cannot connect to backend server');
    }
  }, []);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        // Clear handlers before closing to prevent post-unmount state updates
        wsRef.current.onclose = null;
        wsRef.current.onerror = null;
        wsRef.current.onmessage = null;
        wsRef.current.onopen = null;
        wsRef.current.close();
        wsRef.current = null;
      }
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
    };
  }, [connectWebSocket]);

  useEffect(() => {
    const interval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const startSimulation = async () => {
    try {
      setIsInitializing(true);
      setError(null);
      
      const configWithDelay = {
        ...simSetupConfig,
        tick_delay: 0.8 / (simSetupConfig.speed || 1)
      };

      const res = await fetch(`${API_URL}/api/simulation/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(configWithDelay)
      });
      const data = await res.json();
      if (data.status === 'started' || data.status === 'already_running') {
        setIsRunning(true);
      } else {
        setIsInitializing(false);
        setError(data.message || 'Failed to start simulation.');
      }
    } catch (e) {
      setError('Failed to start simulation. Check backend connection.');
      setIsInitializing(false);
    }
  };

  const resetSimulation = async () => {
    try {
      setIsInitializing(true);
      await fetch(`${API_URL}/api/simulation/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...simSetupConfig,
          tick_delay: 0.8 / (simSetupConfig.speed || 1)
        })
      });
      setIsRunning(false);
      setSimState(null);
      setIsInitializing(false);
    } catch (e) {
      setError('Failed to reset simulation.');
      setIsInitializing(false);
    }
  };

  const stopSimulation = async () => {
    try {
      await fetch(`${API_URL}/api/simulation/stop`, { method: 'POST' });
      setIsRunning(false);
    } catch (e) {
      setError('Failed to stop simulation.');
    }
  };

  const updateConfig = async (newConfig) => {
    try {
      // If only certain fields changed, merge them
      const updatedConfig = { ...simSetupConfig, ...newConfig };
      setSimSetupConfig(updatedConfig);
      
      const backendConfig = {
        ...updatedConfig,
        tick_delay: 0.8 / (updatedConfig.speed || 1)
      };

      await fetch(`${API_URL}/api/simulation/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(backendConfig)
      });
      
      if (simState) {
        setSimState({ ...simState, config: backendConfig });
      }
    } catch (e) {
      console.error('Failed to update config', e);
    }
  };


  const startDualSimulation = async () => {
    try {
      setError(null);
      const res = await fetch(`${API_URL}/api/simulation/dual/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          num_orders: simSetupConfig.num_orders || 15,
          num_drivers: simSetupConfig.num_drivers || 5,
          city: simSetupConfig.city || "Pune, India",
          tick_delay: 0.8 / (simSetupConfig.speed || 1)
        })
      });
      const data = await res.json();
      if (data.status === 'started' || data.status === 'already_running') {
        setIsDualRunning(true);
      } else {
        setError(data.message || 'Failed to start dual simulation.');
      }
    } catch (e) {
      setError('Failed to start dual simulation. Ensure backend is restarted with the latest code.');
    }
  };

  const stopDualSimulation = async () => {
    try {
      await fetch(`${API_URL}/api/simulation/dual/stop`, { method: 'POST' });
      setIsDualRunning(false);
    } catch (e) {
      setError('Failed to stop dual simulation.');
    }
  };

  const resetDualSimulation = async () => {
    try {
      await fetch(`${API_URL}/api/simulation/dual/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          num_orders: simSetupConfig.num_orders || 15,
          num_drivers: simSetupConfig.num_drivers || 5,
          city: simSetupConfig.city || "Pune, India",
          tick_delay: 0.8 / (simSetupConfig.speed || 1)
        })
      });
      setIsDualRunning(false);
      setDualState(null);
    } catch (e) {
      setError('Failed to reset dual simulation.');
    }
  };

  const triggerDualRoadClosure = async () => {
    try {
      const res = await fetch(`${API_URL}/api/simulation/dual/road-closure`, { method: 'POST' });
      return await res.json();
    } catch (e) {
      setError('Failed to trigger road closure.');
    }
  };

  const triggerDualTrafficSurge = async () => {
    try {
      const res = await fetch(`${API_URL}/api/simulation/dual/traffic-surge`, { method: 'POST' });
      return await res.json();
    } catch (e) {
      setError('Failed to trigger traffic surge.');
    }
  };

  const injectDualOrder = async () => {
    try {
      const res = await fetch(`${API_URL}/api/simulation/dual/inject-order`, { method: 'POST' });
      return await res.json();
    } catch (e) {
      setError('Failed to inject order.');
    }
  };

  const triggerSingleRoadClosure = async () => {
    try {
      const res = await fetch(`${API_URL}/api/simulation/road-closure`, { method: 'POST' });
      return await res.json();
    } catch (e) {
      setError('Failed to trigger road closure.');
    }
  };

  const triggerSingleTrafficSurge = async () => {
    try {
      const res = await fetch(`${API_URL}/api/simulation/traffic-surge`, { method: 'POST' });
      return await res.json();
    } catch (e) {
      setError('Failed to trigger traffic surge.');
    }
  };

  const injectSingleOrder = async () => {
    try {
      const res = await fetch(`${API_URL}/api/simulation/inject-order`, { method: 'POST' });
      return await res.json();
    } catch (e) {
      setError('Failed to inject order.');
    }
  };

  const fetchDebugRoute = async () => {
    if (!simState || !simState.orders || simState.orders.length === 0) return;
    setDebugLoading(true);
    try {
      const order = simState.orders.find(o => o.status === 'pending') || simState.orders[0];
      const res = await fetch(`${API_URL}/api/algorithms/compare?from_lat=${order.restaurant_lat}&from_lng=${order.restaurant_lng}&to_lat=${order.customer_lat}&to_lng=${order.customer_lng}`);
      const data = await res.json();
      setDebugRouteData(data);
    } catch (e) {
      console.error(e);
    } finally {
      setDebugLoading(false);
    }
  };

  return (
    <>
      {error && (
        <div className="error-banner">
          <span>⚠️</span> {error}
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      {viewMode === 'dual' ? (
        <DualDashboard
          dualState={dualState}
          isConnected={isConnected}
          isDualRunning={isDualRunning}
          onStartDual={startDualSimulation}
          onStopDual={stopDualSimulation}
          onResetDual={resetDualSimulation}
          onTriggerRoadClosure={triggerDualRoadClosure}
          onTriggerTrafficSurge={triggerDualTrafficSurge}
          onInjectOrder={injectDualOrder}
          config={simSetupConfig}
          onConfigChange={setSimSetupConfig}
          onSwitchToSingleView={() => setViewMode('single')}
        />
      ) : (
        <Dashboard
          simState={simState}
          isConnected={isConnected}
          isRunning={isRunning}
          config={simState?.config || { routing_mode: simSetupConfig.routing_mode, manual_algorithm: simSetupConfig.manual_algorithm }}
          onUpdateConfig={updateConfig}
          simSetupConfig={simSetupConfig}
          setSimSetupConfig={setSimSetupConfig}
          onStart={startSimulation}
          onStop={stopSimulation}
          onReset={resetSimulation}
          onCompare={fetchDebugRoute}
          onSwitchToDualView={() => setViewMode('dual')}
          onTriggerRoadClosure={triggerSingleRoadClosure}
          onTriggerTrafficSurge={triggerSingleTrafficSurge}
          onInjectOrder={injectSingleOrder}
        >
          <AlgorithmChart comparisonData={debugRouteData} isLoading={debugLoading} />
        </Dashboard>
      )}
    </>
  );
}

export default App;