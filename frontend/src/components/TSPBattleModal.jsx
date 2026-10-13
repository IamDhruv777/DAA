import React, { useState, useEffect } from 'react';
import './TSPBattleModal.css';

function TSPBattleModal({ isOpen, onClose }) {
  const [numStops, setNumStops] = useState(5);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const runTSP = async (stops = numStops) => {
    setLoading(true);
    setError(null);
    try {
      const apiBase = window.location.port === '5173' ? 'http://localhost:8000' : '';
      const url = `${apiBase}/api/tsp/compare?num_stops=${stops}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();
      setResults(data);
    } catch (err) {
      console.error('Failed to run TSP sequencer:', err);
      setError('Could not connect to /api/tsp/compare. Ensure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && !results) {
      runTSP(5);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const hk = results?.held_karp;
  const greedy = results?.greedy;
  const bf = results?.brute_force;
  const savings = results?.held_karp_savings_pct || 0;

  return (
    <div className="tsp-modal-backdrop" onClick={onClose}>
      <div className="tsp-modal-container" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="tsp-modal-header">
          <div className="header-title-wrap">
            <span className="tsp-badge">LEVEL-2 MULTI-STOP SEQUENCING &middot; DAA ARENA</span>
            <h2>🎒 Multi-Stop Delivery Sequencer (TSP Optimization)</h2>
            <p className="tsp-subtitle">
              Comparing Held-Karp Dynamic Programming vs Greedy Heuristics vs Brute Force Permutations
            </p>
          </div>
          <button className="tsp-close-btn" onClick={onClose} title="Close Modal (Esc)">✕</button>
        </div>

        {/* Controls Toolbar */}
        <div className="tsp-toolbar">
          <div className="toolbar-item">
            <label className="toolbar-label">📦 Number of Stops in Batch:</label>
            <div className="stop-selector-pills">
              {[3, 4, 5, 6, 7].map((count) => (
                <button
                  key={count}
                  className={`stop-pill ${numStops === count ? 'active' : ''}`}
                  onClick={() => {
                    setNumStops(count);
                    runTSP(count);
                  }}
                >
                  {count} Stops ({count * 2} Pickup/Drop points)
                </button>
              ))}
            </div>
          </div>
          <button 
            className="btn-rerun-tsp" 
            onClick={() => runTSP(numStops)} 
            disabled={loading}
          >
            {loading ? '⏳ Solving...' : '⚡ Re-Sequence Batch'}
          </button>
        </div>

        {/* DP Advantage Banner */}
        <div className="tsp-insight-banner">
          <div className="insight-icon">🏆</div>
          <div className="insight-text">
            <strong>Two-Level Optimization Model:</strong> While Dijkstra/A* solve <em>Level-1 (point-to-point road travel)</em>, 
            <strong> Held-Karp Bitmask DP</strong> solves <em>Level-2 (what order to visit multiple customers)</em> with strict 
            Pickup-before-Delivery precedence constraints.
            {savings > 0 && (
              <div style={{ marginTop: '4px', color: '#34c759', fontWeight: 700 }}>
                🎯 Dynamic Programming Advantage: Held-Karp saved {savings}% detour distance over Greedy nearest neighbor!
              </div>
            )}
          </div>
        </div>

        {error && <div className="tsp-error-bar">{error}</div>}

        {/* Comparison Cards Grid */}
        <div className="tsp-grid">
          {/* Held-Karp DP Card */}
          <div className="tsp-card winner-card">
            <div className="card-top">
              <div>
                <h3 className="tsp-card-title">Held-Karp Dynamic Programming</h3>
                <span className="tsp-tag tag-dp">👑 MATHEMATICALLY OPTIMAL</span>
              </div>
              <span className="winner-crown">BEST TOUR</span>
            </div>

            <div className="card-metrics-section">
              <div className="metric-row">
                <span className="m-label">⏱️ Compute Time:</span>
                <span className="m-val highlight">{loading ? '...' : hk ? `${hk.time_ms} ms` : '—'}</span>
              </div>
              <div className="metric-row">
                <span className="m-label">📏 Tour Distance:</span>
                <span className="m-val">{loading ? '...' : hk ? `${(hk.cost_distance_m / 1000).toFixed(2)} km` : '—'}</span>
              </div>
              <div className="metric-row">
                <span className="m-label">🧠 DP States Checked:</span>
                <span className="m-val">{loading ? '...' : hk ? `${hk.states_explored.toLocaleString()} states` : '—'}</span>
              </div>
              <div className="metric-row">
                <span className="m-label">🎯 Solution Guarantee:</span>
                <span className="m-val" style={{ color: '#34c759' }}>Guaranteed Optimal</span>
              </div>
            </div>

            <div className="card-complexity-box">
              <div className="complexity-item">
                <span className="c-label">Time Complexity:</span>
                <code className="c-code">O(N² &middot; 2ᴺ)</code>
              </div>
              <div className="complexity-item">
                <span className="c-label">Space Complexity:</span>
                <code className="c-code">O(N &middot; 2ᴺ) Bitmask</code>
              </div>
            </div>

            <div className="card-viva-box">
              <span className="viva-title">🎓 DAA Bitmask Recurrence:</span>
              <p className="viva-desc">
                Uses <code>memo[(mask, last_node)] = min(cost + dist)</code> where bitmask represents visited nodes. 
                Reduces exponential search from N! down to 2ᴺ while guaranteeing global optimality.
              </p>
            </div>
          </div>

          {/* Greedy Nearest Neighbor Card */}
          <div className="tsp-card">
            <div className="card-top">
              <div>
                <h3 className="tsp-card-title">Greedy Nearest Neighbor</h3>
                <span className="tsp-tag tag-greedy">⚡ HEURISTIC APPROXIMATION</span>
              </div>
            </div>

            <div className="card-metrics-section">
              <div className="metric-row">
                <span className="m-label">⏱️ Compute Time:</span>
                <span className="m-val highlight">{loading ? '...' : greedy ? `${greedy.time_ms} ms` : '—'}</span>
              </div>
              <div className="metric-row">
                <span className="m-label">📏 Tour Distance:</span>
                <span className="m-val">{loading ? '...' : greedy ? `${(greedy.cost_distance_m / 1000).toFixed(2)} km` : '—'}</span>
              </div>
              <div className="metric-row">
                <span className="m-label">🔍 Decisions Evaluated:</span>
                <span className="m-val">{loading ? '...' : greedy ? `${greedy.states_explored} steps` : '—'}</span>
              </div>
              <div className="metric-row">
                <span className="m-label">⚠️ Suboptimal Penalty:</span>
                <span className="m-val" style={{ color: savings > 0 ? '#ff453a' : '#34c759' }}>
                  {savings > 0 ? `+${savings}% Extra Detour` : 'Optimal in this batch'}
                </span>
              </div>
            </div>

            <div className="card-complexity-box">
              <div className="complexity-item">
                <span className="c-label">Time Complexity:</span>
                <code className="c-code">O(N²)</code>
              </div>
              <div className="complexity-item">
                <span className="c-label">Space Complexity:</span>
                <code className="c-code">O(N) Array</code>
              </div>
            </div>

            <div className="card-viva-box">
              <span className="viva-title">🎓 DAA Heuristic Flaw:</span>
              <p className="viva-desc">
                Myopic local choice: Always visits the nearest available pickup/drop. Often forces the driver into costly long-distance backtracks toward the end of the shift.
              </p>
            </div>
          </div>

          {/* Brute Force Permutations Card */}
          <div className="tsp-card">
            <div className="card-top">
              <div>
                <h3 className="tsp-card-title">Brute Force Permutations</h3>
                <span className="tsp-tag tag-bf">🛑 INTRACTABLE FACTORIAL</span>
              </div>
            </div>

            <div className="card-metrics-section">
              <div className="metric-row">
                <span className="m-label">⏱️ Permutation Time:</span>
                <span className="m-val highlight">{loading ? '...' : bf ? `${bf.time_ms} ms` : '—'}</span>
              </div>
              <div className="metric-row">
                <span className="m-label">📏 Tour Distance:</span>
                <span className="m-val">{loading ? '...' : bf ? `${(bf.cost_distance_m / 1000).toFixed(2)} km` : '—'}</span>
              </div>
              <div className="metric-row">
                <span className="m-label">💥 Total Paths Checked:</span>
                <span className="m-val" style={{ color: '#ff9500' }}>
                  {loading ? '...' : bf ? `${bf.states_explored.toLocaleString()} permutations!` : '—'}
                </span>
              </div>
              <div className="metric-row">
                <span className="m-label">📈 Scalability:</span>
                <span className="m-val" style={{ color: '#ff453a' }}>Explodes at N &gt; 10</span>
              </div>
            </div>

            <div className="card-complexity-box">
              <div className="complexity-item">
                <span className="c-label">Time Complexity:</span>
                <code className="c-code">O(N!)</code>
              </div>
              <div className="complexity-item">
                <span className="c-label">Space Complexity:</span>
                <code className="c-code">O(N) Recursion Depth</code>
              </div>
            </div>

            <div className="card-viva-box">
              <span className="viva-title">🎓 Why DP is Essential:</span>
              <p className="viva-desc">
                For N=10 stops, Brute Force must check 3.6 million permutations. For N=15, it requires 1.3 trillion permutations (impossible in real time). Held-Karp solves it in milliseconds.
              </p>
            </div>
          </div>
        </div>

        {/* Step-by-Step Stop Sequencer Walkthrough */}
        {results?.stops && (
          <div className="tsp-sequence-section">
            <h4 className="sequence-section-title">📍 Optimal Held-Karp Multi-Stop Visiting Order</h4>
            <div className="sequence-steps-container">
              {results.stops
                .slice()
                .sort((a, b) => a.hk_step - b.hk_step)
                .map((stop, i) => (
                  <div key={stop.index} className="step-badge">
                    <span className="step-number">{i + 1}</span>
                    <div className="step-info">
                      <span className="step-role">{stop.role}</span>
                      <span className="step-coord">[{stop.lat.toFixed(4)}, {stop.lng.toFixed(4)}]</span>
                    </div>
                    {i < results.stops.length - 1 && <span className="step-arrow">➔</span>}
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="tsp-modal-footer">
          <div className="footer-legend">
            <span>Level-1 Routing: <strong>A* Shortest Path (Road Segments)</strong></span>
            <span>Level-2 Sequencing: <strong>Held-Karp Dynamic Programming (Stop Precedence)</strong></span>
          </div>
          <button className="btn-close-tsp" onClick={onClose}>Done</button>
        </div>
      </div>
    </div>
  );
}

export default TSPBattleModal;
