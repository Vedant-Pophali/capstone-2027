import React from 'react';

const Spinner = ({ size = 'default', label = 'Loading...' }) => {
  return (
    <div className="loading-container">
      <div className={`spinner ${size === 'large' ? 'spinner-lg' : ''}`} />
      {label && <span>{label}</span>}
    </div>
  );
};

export default Spinner;
