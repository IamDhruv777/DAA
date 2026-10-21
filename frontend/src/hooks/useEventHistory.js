import { useCallback, useEffect, useState } from 'react';

const STORAGE_KEY = 'smartroute-event-history';
const MAX_EVENTS = 20;

function readSavedEvents() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    return Array.isArray(saved) ? saved.slice(0, MAX_EVENTS) : [];
  } catch {
    return [];
  }
}

export default function useEventHistory() {
  const [events, setEvents] = useState(readSavedEvents);

  const recordEvent = useCallback((event) => {
    if (!event?.id) return;
    setEvents((current) => {
      if (current.some((saved) => saved.id === event.id)) return current;
      return [event, ...current].slice(0, MAX_EVENTS);
    });
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(events));
    } catch {
      // Keep the in-memory event history available if browser storage is disabled.
    }
  }, [events]);

  return [events, recordEvent];
}
