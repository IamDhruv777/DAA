import React from 'react';
import './RiderFlightDeck.css';

function RiderFlightDeck({ driver, driverColor, isFollowing, onToggleFollow, onClose }) {
  if (!driver) return null;

  const statusColors = {
    idle: '#34c759',
    picking: '#ff9500',
    delivering: '#0a84ff',
    returning: '#30d158'
  };

  const statusLabels = {
    idle: '🟢 Available & Waiting for Batch',
    picking: '🏬 En Route to Restaurant (Pickup)',
    delivering: '🚴 Delivering to Customer',
    returning: '🔄 Depot Return'
  };

  const color = driverColor || statusColors[driver.status] || '#94a3b8';
  const order = driver.current_orders && driver.current_orders.length > 0 ? driver.current_orders[0] : null;

  return (
    <aside className="rider-flight-deck">
      {/* Header */}
      <div className="deck-header">
        <div className="deck-title-group">
          <div className="rider-avatar" style={{ borderColor: color, boxShadow: `0 0 12px ${color}40` }}>
            🏍️
          </div>
          <div>
            <h3 className="rider-name">{driver.name || `Rider ${driver.driver_id}`}</h3>
            <span className="rider-id-tag">ID: {driver.driver_id}</span>
          </div>
        </div>
        <button className="deck-close-btn" onClick={onClose} title="Close HUD">✕</button>
      </div>

      {/* Live Status Pill */}
      <div className="deck-status-bar" style={{ background: `${color}18`, borderColor: `${color}40` }}>
        <span className="status-dot" style={{ background: color, boxShadow: `0 0 8px ${color}` }}></span>
        <span className="status-text" style={{ color: color }}>
          {statusLabels[driver.status] || driver.status.toUpperCase()}
        </span>
      </div>

      {/* Telemetry Gauge Grid */}
      <div className="telemetry-grid">
        <div className="telemetry-card">
          <span className="telem-label">⚡ Speed</span>
          <span className="telem-val">{driver.speed_kmh || (driver.status !== 'idle' ? 38 : 0)} <span className="telem-unit">km/h</span></span>
        </div>

        <div className="telemetry-card">
          <span className="telem-label">🔋 Battery / Fuel</span>
          <span className="telem-val">{driver.battery_pct || 90}<span className="telem-unit">%</span></span>
        </div>

        <div className="telemetry-card">
          <span className="telem-label">📦 Delivered</span>
          <span className="telem-val">{driver.deliveries || 0} <span className="telem-unit">orders</span></span>
        </div>

        <div className="telemetry-card">
          <span className="telem-label">📏 Total Distance</span>
          <span className="telem-val">{driver.total_dist_km || 0} <span className="telem-unit">km</span></span>
        </div>
      </div>

      {/* Active Order Card */}
      {order ? (
        <div className="deck-order-card">
          <div className="order-card-header">
            <span className="order-id-badge">Order #{order.order_id}</span>
            {order.is_priority && <span className="priority-badge">⭐ VIP Priority</span>}
          </div>
          
          <div className="order-details-body">
            <div className="order-detail-row">
              <span className="detail-icon">🏬</span>
              <div>
                <strong>{order.restaurant_name}</strong>
                <span className="detail-sub">{order.restaurant_zone}</span>
              </div>
            </div>

            <div className="order-detail-row">
              <span className="detail-icon">🍲</span>
              <div>
                <span className="detail-items">{(order.items || ['Biryani', 'Roti']).join(', ')}</span>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="deck-idle-card">
          <span>💤 No active food order assigned. Ready for next Hungarian bipartite batch.</span>
        </div>
      )}

      {/* Routing Algorithm Badge */}
      <div className="deck-routing-info">
        <div className="routing-badge">
          <span className="routing-icon">🧠</span>
          <div>
            <strong>Level-1: Dynamic A* Navigation</strong>
            <span className="routing-sub">Haversine Euclidean distance heuristic &middot; Pune OSM Graph</span>
          </div>
        </div>
      </div>

      {/* Action Controls */}
      <div className="deck-actions">
        <button 
          className={`btn-follow ${isFollowing ? 'following' : ''}`}
          onClick={onToggleFollow}
          title="Locks map camera to automatically track this rider's movements"
        >
          {isFollowing ? '🎥 Unfollow Rider' : '🎥 Follow Rider (Camera Lock)'}
        </button>
      </div>
    </aside>
  );
}

export default RiderFlightDeck;
