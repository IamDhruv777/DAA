function SimControls({ 
  isRunning, 
  isInitializing, 
  onStart, 
  onStop, 
  onReset, 
  config, 
  onConfigChange,
  onTriggerRoadClosure,
  onTriggerTrafficSurge,
  onInjectOrder,
  isInjectingOrder = false
}) {
  return (
    <div className="glass-panel">
      <div className="control-buttons" style={{ display: 'flex', gap: '10px', marginBottom: '16px' }}>
        {!isRunning ? (
          <button className="btn btn-start" style={{ flex: 1 }} onClick={onStart} disabled={isInitializing}>
            {isInitializing ? '⏳ Initializing...' : '▶ Start'}
          </button>
        ) : (
          <button className="btn btn-stop" style={{ flex: 1 }} onClick={onStop}>
            ⏹ Stop
          </button>
        )}
        <button className="btn btn-secondary" onClick={onReset}>
          ↺ Reset
        </button>
      </div>

      {isRunning && (
        <div className="dynamic-events-group" style={{ marginBottom: '16px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <span className="input-label" style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#a1a1a6' }}>
            ⚡ Dynamic Re-routing Triggers:
          </span>
          <div style={{ display: 'flex', gap: '6px' }}>
            <button 
              className="btn btn-secondary" 
              style={{ flex: 1, fontSize: '11px', padding: '6px 4px', background: 'rgba(255, 69, 58, 0.15)', borderColor: '#ff453a', color: '#ff453a' }}
              onClick={onTriggerRoadClosure}
              title="Close roads and force active drivers to re-route via A*"
            >
              💥 Roadblock
            </button>
            <button 
              className="btn btn-secondary" 
              style={{ flex: 1, fontSize: '11px', padding: '6px 4px', background: 'rgba(255, 159, 10, 0.15)', borderColor: '#ff9f0a', color: '#ff9f0a' }}
              onClick={onTriggerTrafficSurge}
              title="Spike traffic to trigger congestion-aware re-routing"
            >
              🚦 Traffic Spike
            </button>
            <button 
              className="btn btn-secondary" 
              style={{ flex: 1, fontSize: '11px', padding: '6px 4px', background: 'rgba(0, 122, 255, 0.15)', borderColor: '#0a84ff', color: '#0a84ff' }}
              onClick={onInjectOrder}
              disabled={isInjectingOrder}
              title="Inject a new VIP order and recalculate stop sequence"
            >
              {isInjectingOrder ? '📦 Adding VIP...' : '📦 VIP Order'}
            </button>
          </div>
        </div>
      )}

      <div className="input-group" style={{ marginBottom: '10px' }}>
        <span className="input-label">Drivers</span>
        <input
          className="glass-input"
          type="number"
          min="1"
          max="200"
          value={config.num_drivers}
          onChange={(e) => onConfigChange({...config, num_drivers: parseInt(e.target.value) || 1})}
        />
      </div>

      <div className="input-group" style={{ marginBottom: '10px' }}>
        <span className="input-label">Orders</span>
        <input
          className="glass-input"
          type="number"
          min="5"
          max="100"
          value={config.num_orders}
          onChange={(e) => onConfigChange({...config, num_orders: Math.min(100, Math.max(5, parseInt(e.target.value) || 5))})}
        />
      </div>

      <div className="input-group" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', marginBottom: '4px' }}>
          <span className="input-label">Speed</span>
          <span className="input-label" style={{ opacity: 0.8 }}>{config.speed || 1}x</span>
        </div>
        <input
          type="range"
          min="0.5"
          max="5"
          step="0.5"
          value={config.speed || 1}
          onChange={(e) => onConfigChange({...config, speed: parseFloat(e.target.value)})}
          style={{ width: '100%', accentColor: '#0a84ff' }}
        />
      </div>
      
      <div className="info-text">
        {isRunning ? "Adjusting speed updates in real-time." : "Adjust parameters before starting a new simulation run."}
      </div>
    </div>
  );
}

export default SimControls;