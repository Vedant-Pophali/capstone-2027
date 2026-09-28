import React from 'react';
import { RefreshCw } from 'lucide-react';

const TopBar = ({ title, actions }) => {
  return (
    <header className="topbar">
      <h2 className="topbar-title">{title}</h2>
      <div className="topbar-actions">
        {actions}
      </div>
    </header>
  );
};

export default TopBar;
