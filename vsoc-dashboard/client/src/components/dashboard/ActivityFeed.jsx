import React from 'react';
import { Clock } from 'lucide-react';

const eventLabels = {
  CREATED: 'Vehicle added to fleet',
  DELETED: 'Vehicle removed from fleet',
  STATUS_CHANGED: 'Vehicle status changed',
};

const eventDotClass = {
  CREATED: 'created',
  DELETED: 'deleted',
  STATUS_CHANGED: 'changed',
};

const ActivityFeed = ({ events }) => {
  const formatTime = (timestamp) => {
    if (!timestamp) return 'just now';
    try {
      return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return 'just now';
    }
  };

  return (
    <div className="activity-feed">
      <div className="feed-header">
        <h2>Live Activity</h2>
        <Clock size={16} style={{ color: 'var(--color-text-tertiary)' }} />
      </div>
      <div className="feed-list">
        {events.length === 0 ? (
          <div className="feed-item" style={{ justifyContent: 'center', color: 'var(--color-text-tertiary)' }}>
            No activity yet — events will appear here in real time.
          </div>
        ) : (
          events.map(event => (
            <div className="feed-item" key={event.id}>
              <span className={`feed-dot ${eventDotClass[event.type] || ''}`} />
              <span className="feed-text">
                {eventLabels[event.type] || event.type}{' '}
                <strong>#{event.vehicleId}</strong>
              </span>
              <span className="feed-time">{formatTime(event.timestamp)}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ActivityFeed;
