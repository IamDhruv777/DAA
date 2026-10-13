import React, { useState, useEffect } from 'react';
import './AlgorithmBattleModal.css';

const PRESET_CORRIDORS = [
  {
    id: 'fc_viman',
    name: 'FC Road (Shivajinagar) ➔ Viman Nagar',
    desc: 'Dense arterial corridor through central Pune to airport district',
    from: { lat: 18.5314, lng: 73.8446 },
    to: { lat: 18.5679, lng: 73.9143 }
  },
  {
    id: 'kothrud_station',
    name: 'Kothrud (Chandani Chowk) ➔ Pune Junction',
    desc: 'West-to-East transit route connecting residential hills to rail hub',
    from: { lat: 18.5074, lng: 73.8077 },
    to: { lat: 18.5289, lng: 73.8744 }
  },
  {
    id: 'kalyani_koregaon',
    name: 'Kalyani Nagar ➔ Koregaon Park (Lane 7)',
    desc: 'Mula-Mutha river crossing between commercial tech park & lifestyle hub',
    from: { lat: 18.5463, lng: 73.9033 },
    to: { lat: 18.5362, lng: 73.8940 }
  },
  {
    id: 'baner_swargate',
    name: 'Baner Expressway ➔ Swargate ST Bus Stand',
    desc: 'Long-distance cross-city delivery route',
    from: { lat: 18.5590, lng: 73.7868 },
    to: { lat: 18.5018, lng: 73.8636 }
  }
];

const ALGO_METADATA = {
  astar: {
    displayName: 'A* Heuristic Search',
    badge: '🚀 Most Efficient',
    badgeColor: '#34c759',
    timeComplexity: 'O(E + V log V)',
    spaceComplexity: 'O(V)',
    heuristic: 'Haversine Great-Circle h(n)',
    guarantee: 'Optimal & Complete',
    vivaNote: 'Prunes search space toward target using admissible Euclidean heuristic. Explores drastically fewer nodes than Dijkstra while guaranteeing shortest path.'
  },
  dijkstra: {
    displayName: "Dijkstra's Algorithm",
    badge: '🎯 Ground Truth Baseline',
    badgeColor: '#0a84ff',
    timeComplexity: 'O((V + E) log V)',
    spaceComplexity: 'O(V)',
    heuristic: 'None (Uniform Cost g(n))',
    guarantee: 'Optimal & Complete',
    vivaNote: 'Explores radially in all directions with a Min-Priority Queue. Computes mathematically optimal shortest paths but wastes time exploring opposite directions.'
  },
  bellman_ford: {
    displayName: 'Bellman-Ford Algorithm',
    badge: '🛡️ Dynamic Programming',
    badgeColor: '#ff9500',
    timeComplexity: 'O(V × E)',
    spaceComplexity: 'O(V)',
    heuristic: 'None (Edge Relaxation)',
    guarantee: 'Detects Negative Cycles',
    vivaNote: 'Relaxes all graph edges |V| - 1 times. Essential when negative edge weights can occur, but significantly slower than Dijkstra on large OSM road networks.'
  },
  bfs: {
    displayName: 'Breadth-First Search (BFS)',
    badge: '⚠️ Hop-Count Only',
    badgeColor: '#af52de',
    timeComplexity: 'O(V + E)',
    spaceComplexity: 'O(V)',
    heuristic: 'Unweighted Queue (FIFO)',
    guarantee: 'Suboptimal for Metres',
    vivaNote: 'Finds fewest turns/intersections (minimum edge hops), NOT minimum distance in metres. Demonstrates why unweighted algorithms fail in physical road maps.'
  },
  greedy: {
    displayName: 'Greedy Best-First',
    badge: '⚡ Ultra Fast (Suboptimal)',
    badgeColor: '#ff3b30',
    timeComplexity: 'O(b^m)',
    spaceComplexity: 'O(b^m)',
    heuristic: 'Pure h(n) without g(n)',
    guarantee: 'Inadmissible / Suboptimal',
    vivaNote: 'Charges headlong toward the goal based purely on remaining straight-line distance. Very fast, but frequently gets trapped by river loops or dead ends.'
  }
};

function AlgorithmBattleModal({ isOpen, onClose }) {
  const [selectedCorridor, setSelectedCorridor] = useState(PRESET_CORRIDORS[0]);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const runRace = async (corridor = selectedCorridor) => {
    setLoading(true);
    setError(null);
    try {
      const url = `/api/algorithms/compare?from_lat=${corridor.from.lat}&from_lng=${corridor.from.lng}&to_lat=${corridor.to.lat}&to_lng=${corridor.to.lng}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();
      setResults(data);
    } catch (err) {
      console.error('Failed to run algorithm race:', err);
      setError('Could not connect to /api/algorithms/compare. Ensure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && !results) {
      runRace(PRESET_CORRIDORS[0]);
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

  // Compute Search Space Reduction % (A* vs Dijkstra)
  let astarNodes = results?.astar?.nodes_explored || 0;
  let dijkstraNodes = results?.dijkstra?.nodes_explored || 0;
  let reductionPct = dijkstraNodes > 0 && astarNodes > 0
    ? (((dijkstraNodes - astarNodes) / dijkstraNodes) * 100).toFixed(1)
    : null;

  return (
    <div className="battle-modal-backdrop" onClick={onClose}>
      <div className="battle-modal-container" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="battle-modal-header">
          <div className="header-title-wrap">
            <span className="battle-badge">DAA ALGORITHM BENCHMARK ARENA</span>
            <h2>⚔️ Routing Algorithm Battle Royale</h2>
            <p className="battle-subtitle">
              Head-to-head empirical comparison across Pune's OpenStreetMap road graph
            </p>
          </div>
          <button className="battle-close-btn" onClick={onClose} title="Close Arena (Esc)">✕</button>
        </div>

        {/* Corridor Selector Bar */}
        <div className="corridor-selector-bar">
          <label className="selector-label">📍 Select Test Corridor:</label>
          <div className="corridor-pills">
            {PRESET_CORRIDORS.map((c) => (
              <button
                key={c.id}
                className={`corridor-pill ${selectedCorridor.id === c.id ? 'active' : ''}`}
                onClick={() => {
                  setSelectedCorridor(c);
                  runRace(c);
                }}
              >
                {c.name}
              </button>
            ))}
          </div>
          <button 
            className="btn-rerun-race" 
            onClick={() => runRace(selectedCorridor)} 
            disabled={loading}
          >
            {loading ? '⏳ Computing...' : '⚡ Re-Run Race'}
          </button>
        </div>

        {/* Dynamic DAA Insight Highlight */}
        {reductionPct && parseFloat(reductionPct) > 0 && (
          <div className="battle-insight-banner">
            <div className="insight-icon">🏆</div>
            <div className="insight-text">
              <strong>DAA Heuristic Advantage:</strong> A* pruned{' '}
              <span className="highlight-stat">{reductionPct}%</span> of the search space compared to Dijkstra
              ({astarNodes.toLocaleString()} nodes vs {dijkstraNodes.toLocaleString()} nodes), while producing the exact same optimal distance ({results?.astar?.distance_m?.toFixed(0)}m)!
            </div>
          </div>
        )}

        {/* Error message */}
        {error && <div className="battle-error-bar">{error}</div>}

        {/* Comparison Cards Grid */}
        <div className="battle-grid">
          {Object.entries(ALGO_METADATA).map(([key, meta]) => {
            const data = results ? results[key] : null;
            const isWinner = key === 'astar';

            return (
              <div key={key} className={`battle-card ${isWinner ? 'winner-card' : ''}`}>
                <div className="card-top">
                  <div>
                    <h3 className="algo-card-title">{meta.displayName}</h3>
                    <span 
                      className="algo-type-tag" 
                      style={{ background: `${meta.badgeColor}20`, color: meta.badgeColor, borderColor: `${meta.badgeColor}40` }}
                    >
                      {meta.badge}
                    </span>
                  </div>
                  {isWinner && <span className="winner-crown" title="Fastest with Optimal Path">👑 BEST</span>}
                </div>

                {/* Metrics Table */}
                <div className="card-metrics-section">
                  <div className="metric-row">
                    <span className="m-label">⏱️ Calc Time:</span>
                    <span className="m-val highlight">
                      {loading ? '...' : data ? `${data.time_ms?.toFixed(2)} ms` : '—'}
                    </span>
                  </div>

                  <div className="metric-row">
                    <span className="m-label">🔍 Nodes Explored:</span>
                    <span className="m-val">
                      {loading ? '...' : data ? (data.nodes_explored?.toLocaleString() || 'N/A') : '—'}
                    </span>
                  </div>

                  <div className="metric-row">
                    <span className="m-label">📏 Route Distance:</span>
                    <span className="m-val">
                      {loading ? '...' : data ? `${(data.distance_m / 1000).toFixed(2)} km` : '—'}
                    </span>
                  </div>

                  <div className="metric-row">
                    <span className="m-label">🛣️ Path Node Hops:</span>
                    <span className="m-val">
                      {loading ? '...' : data ? `${data.path_length || 0} nodes` : '—'}
                    </span>
                  </div>
                </div>

                {/* DAA Theoretical Complexity */}
                <div className="card-complexity-box">
                  <div className="complexity-item">
                    <span className="c-label">Time Complexity:</span>
                    <code className="c-code">{meta.timeComplexity}</code>
                  </div>
                  <div className="complexity-item">
                    <span className="c-label">Space Complexity:</span>
                    <code className="c-code">{meta.spaceComplexity}</code>
                  </div>
                </div>

                {/* Viva Explanation */}
                <div className="card-viva-box">
                  <span className="viva-title">🎓 Viva Defence:</span>
                  <p className="viva-desc">{meta.vivaNote}</p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="battle-modal-footer">
          <div className="footer-legend">
            <span>Graph: <strong>Pune OSM Network (~21,000 nodes, ~52,000 directed edges)</strong></span>
            <span>Weight Metric: <strong>Haversine Distance (m) × Dynamic Traffic Congestion Index</strong></span>
          </div>
          <button className="btn-close-modal" onClick={onClose}>Done</button>
        </div>
      </div>
    </div>
  );
}

export default AlgorithmBattleModal;
