import React from 'react';

const StatusBadge = ({ status }) => {
  const normalized = (status || 'unknown').toLowerCase();

  let className = 'status-badge ';
  if (normalized === 'healthy') className += 'healthy';
  else if (normalized === 'compromised') className += 'compromised';
  else className += 'unknown';

  return (
    <span className={className}>
      <span className="status-dot" />
      {status || 'Unknown'}
    </span>
  );
};

export default StatusBadge;
