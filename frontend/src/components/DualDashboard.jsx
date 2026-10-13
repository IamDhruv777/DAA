import React, { useState } from 'react';
import MapView from './MapView';
import AlgorithmBattleModal from './AlgorithmBattleModal';
import TSPBattleModal from './TSPBattleModal';
import './DualDashboard.css';

function DualDashboard({
  dualState,
  isConnected,
  isDualRunning,
  onStartDual,
  onStopDual,
  onResetDual,
  onTriggerRoadClosure,
  onTriggerTrafficSurge,
  onInjectOrder,
  config,
  onConfigChange,
  onSwitchToSingleView
}) {
  const [closureLoading, setClosureLoading] = useState(false);
  const [trafficLoading, setTrafficLoading] = useState(false);
  const [orderLoading, setOrderLoading] = useState(false);
  const [activeBannerMessage, setActiveBannerMessage] = useState(null);
  const [showBattleModal, setShowBattleModal] = useState(false);
  const [showTSPModal, setShowTSPModal] = useState(false);

  // Auto-listen to dynamic re-route events from backend WebSocket
  React.useEffect(() => {
    const event = dualState?.reroute_event || dualState?.optimized?.reroute_event;
    if (event && event.message) {
      setActiveBannerMessage(event.message);
      const timer = setTimeout(() => setActiveBannerMessage(null), 6000);
      return () => clearTimeout(timer);
    }
  }, [dualState?.reroute_event?.id, dualState?.optimized?.reroute_event?.id]);

  const baseline = dualState?.baseline || {};
  const optimized = dualState?.optimized || {};
  const delta = dualState?.delta || {
    dist_saved_km: 0,
    dist_saved_pct: 0,
    time_saved_min: 0,
    base_dist_km: 0,
    opt_dist_km: 0,
    delivered_base: 0,
    delivered_opt: 0
  };

  const handleClosureClick = async () => {
    setClosureLoading(true);
    try {
      const res = await onTriggerRoadClosure();
      if (res && res.message) {
        setActiveBannerMessage(res.message);
        setTimeout(() => setActiveBannerMessage(null), 6000);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setClosureLoading(false);
    }
  };

  const handleTrafficClick = async () => {
    setTrafficLoading(true);
    try {
      const res = await onTriggerTrafficSurge();
      if (res && res.message) {
        setActiveBannerMessage(res.message);
        setTimeout(() => setActiveBannerMessage(null), 6000);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setTrafficLoading(false);
    }
  };

  const handleOrderClick = async () => {
    setOrderLoading(true);
    try {
      const res = await onInjectOrder();
      if (res && res.message) {
        setActiveBannerMessage(res.message);
        setTimeout(() => setActiveBannerMessage(null), 6000);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setOrderLoading(false);
    }
  };

  return (
    <div className="dual-dashboard">
      {/* Top Header & Comparison Scoreboard */}
      <header className="dual-header">
        <div className="dual-header-left">
          <div className="logo-badge">
            <span className="logo-icon">⚔️</span>
            <div>
              <h2>A/B Benchmark: Baseline vs SmartRoute</h2>
              <span className="subtitle">Synchronized Multi-Agent Simulation on Real Pune Road Graph</span>
            </div>
          </div>
        </div>

        {/* Live Delta Scoreboard Bar */}
        <div className="delta-scoreboard">
          <div className="score-card">
            <span className="score-label">📏 Distance Saved</span>
            <div className={`score-value ${delta.dist_saved_pct > 0 ? 'positive' : ''}`}>
              {delta.dist_saved_pct > 0 ? `-${delta.dist_saved_pct}%` : `${delta.dist_saved_pct}%`}
              <span className="score-unit">({Math.abs(delta.dist_saved_km)} km)</span>
            </div>
          </div>

          <div className="score-card">
            <span className="score-label">⏱️ Avg Delivery Time</span>
            <div className={`score-value ${delta.time_saved_min > 0 ? 'positive' : ''}`}>
              {delta.time_saved_min > 0 ? `-${delta.time_saved_min}m` : `${delta.time_saved_min}m`}
              <span className="score-unit">faster</span>
            </div>
          </div>

          <div className="score-card">
            <span className="score-label">📦 Delivered</span>
            <div className="score-value neutral">
              <span>{delta.delivered_base}</span>
              <span className="vs-divider">vs</span>
              <span className="opt-highlight">{delta.delivered_opt}</span>
            </div>
          </div>

          <div className="score-card">
            <span className="score-label">⚡ Status</span>
            <div className="score-badge">
              <span className={`status-indicator ${isConnected ? 'live' : 'offline'}`}></span>
              {isConnected ? (isDualRunning ? 'Running' : 'Ready') : 'Offline'}
            </div>
          </div>
        </div>

        {/* Global Controls */}
        <div className="dual-header-right">
          {!isDualRunning ? (
            <button className="btn btn-start" onClick={onStartDual}>
              ▶ Run Dual Test
            </button>
          ) : (
            <button className="btn btn-stop" onClick={onStopDual}>
              ⏹ Stop
            </button>
          )}

          <button className="btn btn-secondary" onClick={onResetDual}>
            ↺ Reset
          </button>

          <button 
            className="btn btn-closure" 
            onClick={handleClosureClick}
            disabled={!isDualRunning || closureLoading}
            title="Inject sudden road closure in Pune to test dynamic re-routing"
          >
            {closureLoading ? '💥 Closing...' : '💥 Block Roads'}
          </button>

          <button 
            className="btn btn-closure" 
            onClick={handleTrafficClick}
            disabled={!isDualRunning || trafficLoading}
            style={{ background: 'rgba(255, 159, 10, 0.2)', borderColor: '#ff9f0a', color: '#ff9f0a' }}
            title="Spike traffic congestion to prompt real-time detour calculation"
          >
            {trafficLoading ? '🚦 Spiking...' : '🚦 Traffic Spike'}
          </button>

          <button 
            className="btn btn-closure" 
            onClick={handleOrderClick}
            disabled={!isDualRunning || orderLoading}
            style={{ background: 'rgba(0, 122, 255, 0.2)', borderColor: '#0a84ff', color: '#0a84ff' }}
            title="Inject a high-priority order mid-simulation to re-evaluate delivery sequence"
          >
            {orderLoading ? '📦 Injecting...' : '📦 VIP Order'}
          </button>

          <button 
            className="btn btn-closure" 
            onClick={() => setShowTSPModal(true)}
            style={{ 
              background: 'linear-gradient(135deg, #ff7b00, #ff4500)', 
              borderColor: '#ff7b00', 
              color: '#ffffff', 
              fontWeight: '700' 
            }}
            title="Level-2 Delivery Sequencing: Held-Karp Dynamic Programming vs Greedy TSP"
          >
            🎒 Multi-Stop TSP
          </button>

          <button 
            className="btn btn-closure" 
            onClick={() => setShowBattleModal(true)}
            style={{ 
              background: 'linear-gradient(135deg, #10b981, #06b6d4)', 
              borderColor: '#10b981', 
              color: '#ffffff', 
              fontWeight: '700' 
            }}
            title="Empirical head-to-head race between A*, Dijkstra, Bellman-Ford, and BFS"
          >
            🏆 Algorithm Race
          </button>

          <button className="btn btn-switch" onClick={onSwitchToSingleView}>
            🚴 Single View
          </button>
        </div>
      </header>

      {/* Parameters & Quick Control Toolbar */}
      <div className="dual-toolbar">
        <div className="toolbar-left">
          <div className="toolbar-item">
            <span className="toolbar-label">🏍️ Drivers:</span>
            <input
              type="number"
              min="1"
              max="50"
              value={config?.num_drivers || 5}
              disabled={isDualRunning}
              onChange={(e) => onConfigChange({ ...config, num_drivers: parseInt(e.target.value) || 1 })}
              className="dual-input"
            />
          </div>

          <div className="toolbar-item">
            <span className="toolbar-label">📦 Orders:</span>
            <input
              type="number"
              min="2"
              max="200"
              value={config?.num_orders || 15}
              disabled={isDualRunning}
              onChange={(e) => onConfigChange({ ...config, num_orders: parseInt(e.target.value) || 2 })}
              className="dual-input"
            />
          </div>

          <div className="toolbar-item">
            <span className="toolbar-label">⚡ Speed:</span>
            <span className="speed-val">{config?.speed || 1}x</span>
            <input
              type="range"
              min="0.5"
              max="5"
              step="0.5"
              value={config?.speed || 1}
              onChange={(e) => onConfigChange({ ...config, speed: parseFloat(e.target.value) })}
              className="dual-slider"
            />
          </div>
        </div>

        <div className="toolbar-right">
          <span className="toolbar-hint">
            {isDualRunning ? "🚀 Running live comparison. Watch drivers diverge on both maps." : "💡 Set parameters, then click 'Run Dual Test'."}
          </span>
        </div>
      </div>

      {/* Dynamic Re-Route Incident Banner */}
      {activeBannerMessage && (
        <div className="closure-alert-banner">
          <span>{activeBannerMessage}</span>
          <span className="alert-sub">Observe: Right map (SmartRoute) recomputes via dynamic A*; Left map (Baseline) remains static!</span>
        </div>
      )}

      {/* Side-by-Side Dual Map Panels */}
      <main className="dual-maps-container">
        {/* LEFT PANEL: Traditional Baseline (Greedy) */}
        <section className="dual-panel baseline-panel">
          <div className="panel-banner baseline-banner">
            <div className="panel-title-group">
              <span className="badge-pill badge-baseline">🔴 TRADITIONAL BASELINE</span>
              <h3>Greedy First-Come Heuristic</h3>
            </div>
            <div className="panel-specs">
              <span>• Assignment: <strong>Greedy Nearest ($O(N)$)</strong></span>
              <span>• Batching: <strong>K-Means Spatial</strong></span>
              <span>• Routing: <strong>Static Heuristic</strong></span>
            </div>
            <div className="panel-quick-metric">
              Total Distance: <strong>{delta.base_dist_km} km</strong>
            </div>
          </div>

          <div className="map-wrapper">
            <MapView
              drivers={baseline.drivers || []}
              orders={baseline.orders || []}
              closedRoads={baseline.closed_roads || []}
              speed={config?.speed || 1}
              isRunning={isDualRunning}
              showHeatmap={false}
              city="Pune, India"
            />
          </div>
        </section>

        {/* RIGHT PANEL: SmartRoute Optimized */}
        <section className="dual-panel optimized-panel">
          <div className="panel-banner optimized-banner">
            <div className="panel-title-group">
              <span className="badge-pill badge-optimized">🟢 SMARTROUTE OPTIMIZED</span>
              <h3>Global Research Engine</h3>
            </div>
            <div className="panel-specs">
              <span>• Assignment: <strong>Hungarian Bipartite ($O(V^3)$)</strong></span>
              <span>• Batching: <strong>FoodMatch Compatibility</strong></span>
              <span>• Routing: <strong>Dynamic A* Re-routing</strong></span>
            </div>
            <div className="panel-quick-metric highlight">
              Total Distance: <strong>{delta.opt_dist_km} km</strong> 
              {delta.dist_saved_pct > 0 && <span className="saved-tag">(-{delta.dist_saved_pct}%)</span>}
            </div>
          </div>

          <div className="map-wrapper">
            <MapView
              drivers={optimized.drivers || []}
              orders={optimized.orders || []}
              closedRoads={optimized.closed_roads || []}
              speed={config?.speed || 1}
              isRunning={isDualRunning}
              showHeatmap={false}
              city="Pune, India"
            />
          </div>
        </section>
      </main>

      <AlgorithmBattleModal 
        isOpen={showBattleModal} 
        onClose={() => setShowBattleModal(false)} 
      />

      <TSPBattleModal 
        isOpen={showTSPModal} 
        onClose={() => setShowTSPModal(false)} 
      />
    </div>
  );
}

export default DualDashboard;
