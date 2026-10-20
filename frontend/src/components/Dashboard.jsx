import { useState, useEffect } from 'react';
import MapView from './MapView';
import MetricsPanel from './MetricsPanel';
import AlgorithmSelector from './AlgorithmSelector';
import SimControls from './SimControls';
import AlgorithmBattleModal from './AlgorithmBattleModal';
import TSPBattleModal from './TSPBattleModal';
import './Dashboard.css';

function Dashboard({
  simState,
  isConnected,
  isRunning,
  isInitializing,
  config = { routing_mode: 'dynamic', manual_algorithm: 'dijkstra' },
  onUpdateConfig,
  simSetupConfig,
  setSimSetupConfig,
  onStart,
  onStop,
  onReset,
  onCompare,
  onSwitchToDualView,
  onTriggerRoadClosure,
  onTriggerTrafficSurge,
  onInjectOrder,
  children,
}) {
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [darkMode, setDarkMode] = useState(true);
  const [activeBannerMessage, setActiveBannerMessage] = useState(null);
  const [isInjectingOrder, setIsInjectingOrder] = useState(false);
  const [showBattleModal, setShowBattleModal] = useState(false);
  const [showTSPModal, setShowTSPModal] = useState(false);

  useEffect(() => {
    if (simState?.reroute_event?.message) {
      setActiveBannerMessage(simState.reroute_event.message);
      const timer = setTimeout(() => setActiveBannerMessage(null), 6000);
      return () => clearTimeout(timer);
    }
  }, [simState?.reroute_event?.id]);

  const handleInjectOrder = async () => {
    setIsInjectingOrder(true);
    try {
      const result = await onInjectOrder();
      setActiveBannerMessage(result?.message || 'VIP order injection failed.');
      setTimeout(() => setActiveBannerMessage(null), 6000);
    } catch (error) {
      setActiveBannerMessage('VIP order injection failed.');
      setTimeout(() => setActiveBannerMessage(null), 6000);
    } finally {
      setIsInjectingOrder(false);
    }
  };

  return (
    <div className={`app ${darkMode ? 'dark' : 'light'}`}>
      <header className="app-header">
        <div className="header-left">
          <div className="logo">
            <span className="logo-icon">🚴</span>
            <h1>DeliveryOS</h1>
          </div>
          <span className="subtitle">{simSetupConfig.city.split(',')[0]} Operations</span>
        </div>

        <div className="header-right">
          <button
            className="btn btn-dual-toggle"
            style={{
              background: 'linear-gradient(135deg, #ff7b00, #ff4500)',
              border: 'none',
              color: '#fff',
              fontWeight: '700',
              padding: '6px 13px',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '12px',
              boxShadow: '0 2px 10px rgba(255, 123, 0, 0.35)'
            }}
            onClick={() => setShowTSPModal(true)}
            title="Level-2 Delivery Sequencing: Held-Karp Dynamic Programming vs Greedy TSP"
          >
            🎒 Multi-Stop TSP
          </button>

          <button
            className="btn btn-dual-toggle"
            style={{
              background: 'linear-gradient(135deg, #10b981, #06b6d4)',
              border: 'none',
              color: '#fff',
              fontWeight: '700',
              padding: '6px 13px',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '12px',
              boxShadow: '0 2px 10px rgba(16, 185, 129, 0.3)'
            }}
            onClick={() => setShowBattleModal(true)}
            title="Empirical head-to-head race between A*, Dijkstra, Bellman-Ford, and BFS"
          >
            🏆 Algorithm Race
          </button>

          <button
            className="btn btn-dual-toggle"
            style={{
              background: 'linear-gradient(135deg, #ff3b30, #007aff)',
              border: 'none',
              color: '#fff',
              fontWeight: '700',
              padding: '6px 13px',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '12px',
              boxShadow: '0 2px 10px rgba(0, 122, 255, 0.3)'
            }}
            onClick={onSwitchToDualView}
          >
            ⚔️ Side-by-Side Benchmark
          </button>

          <div className="segmented-control">
            <button
              className={`segment-btn ${config.routing_mode === 'dynamic' ? 'active' : ''}`}
              onClick={() => onUpdateConfig({ routing_mode: 'dynamic' })}
            >
              🤖 Auto
            </button>
            <button
              className={`segment-btn ${config.routing_mode === 'manual' ? 'active' : ''}`}
              onClick={() => onUpdateConfig({ routing_mode: 'manual' })}
            >
              🎯 Manual
            </button>
          </div>

          <label className="heatmap-toggle">
            <input
              type="checkbox"
              checked={showHeatmap}
              onChange={(e) => setShowHeatmap(e.target.checked)}
              style={{ display: 'none' }}
            />
            <span className={`btn btn-secondary ${showHeatmap ? 'active' : ''}`} style={{ borderColor: showHeatmap ? 'var(--accent-primary)' : '' }}>
              {showHeatmap ? '🔥 Heatmap On' : '🔥 Heatmap'}
            </span>
          </label>

          <div className={`connection-badge ${isConnected ? 'connected' : ''}`}>
            <span className="connection-dot"></span>
            {isConnected ? 'Live' : 'Offline'}
          </div>

          <button className="theme-toggle" onClick={() => setDarkMode(!darkMode)} style={{ background: 'transparent', border: 'none', cursor: 'pointer', fontSize: '20px' }}>
            {darkMode ? '☀️' : '🌙'}
          </button>
        </div>
      </header>

      <main className="app-main">
        <section className="map-container" style={{ position: 'relative' }}>
          {activeBannerMessage && (
            <div style={{
              position: 'absolute',
              top: '12px',
              left: '50%',
              transform: 'translateX(-50%)',
              zIndex: 1000,
              background: 'rgba(20, 20, 20, 0.92)',
              border: '1px solid #ff9f0a',
              borderRadius: '8px',
              padding: '10px 20px',
              color: '#ffffff',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.5)',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              fontSize: '13px',
              fontWeight: 600,
              backdropFilter: 'blur(10px)',
              animation: 'fadeIn 0.3s ease'
            }}>
              <span>{activeBannerMessage}</span>
            </div>
          )}
          <MapView
            drivers={simState?.drivers || []}
            orders={simState?.orders || []}
            closedRoads={simState?.closed_roads || []}
            speed={simSetupConfig.speed || 1}
            isRunning={isRunning}
            showHeatmap={showHeatmap}
            city={simSetupConfig.city}
          />
        </section>

        <aside className="metrics-panel">
          <div className="panel-section">
            <h3 className="panel-title">🕹️ Simulation Control</h3>
            <SimControls
              isRunning={isRunning}
              isInitializing={isInitializing}
              onStart={onStart}
              onStop={onStop}
              onReset={onReset}
              config={simSetupConfig}
              onConfigChange={setSimSetupConfig}
              onTriggerRoadClosure={onTriggerRoadClosure}
              onTriggerTrafficSurge={onTriggerTrafficSurge}
              onInjectOrder={handleInjectOrder}
              isInjectingOrder={isInjectingOrder}
            />
          </div>

          <div className="panel-section">
            <h3 className="panel-title">🧠 Routing Strategy</h3>
            <AlgorithmSelector
              config={config}
              onUpdateConfig={onUpdateConfig}
            />
          </div>

          <div className="panel-section">
            <h3 className="panel-title">📊 Live Telemetry</h3>
            <MetricsPanel
              metrics={simState?.metrics || {}}
              isRunning={isRunning}
            />
          </div>

          {onCompare && (
            <button
              className="btn btn-start"
              id="btn-compare-algorithms"
              onClick={onCompare}
              disabled={!simState?.orders?.length}
              style={{ width: '100%', marginTop: 'auto' }}
            >
              🚀 Run Algorithm Benchmark
            </button>
          )}
          {children}
        </aside>
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

export default Dashboard;
