import './EventHistory.css';

function EventHistory({ events }) {
  return (
    <section className="event-history-panel" aria-label="Recent simulation events">
      <div className="event-history-heading">
        <h3>🧾 Recent Events</h3>
        <span>{events.length}</span>
      </div>
      {events.length === 0 ? (
        <p className="event-history-empty">Reroutes and VIP dispatches will appear here.</p>
      ) : (
        <ol className="event-history-list">
          {events.slice(0, 8).map((event) => {
            const rerouted = event.rerouted_drivers || event.drivers || [];
            const dispatched = event.dispatched_drivers || [];
            return (
              <li className="event-history-item" key={event.id}>
                <time>
                  {event.timestamp ? new Date(event.timestamp * 1000).toLocaleTimeString() : 'Just now'}
                </time>
                <p>{event.message}</p>
                {rerouted.length > 0 && (
                  <div><strong>Routes recalculated:</strong> {rerouted.join(', ')}</div>
                )}
                {dispatched.length > 0 && (
                  <div><strong>New dispatch:</strong> {dispatched.join(', ')}</div>
                )}
                {event.status === 'queued' && <div className="event-history-muted">No active route needed a change.</div>}
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}

export default EventHistory;
