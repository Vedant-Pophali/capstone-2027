import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Car, Wifi, WifiOff } from 'lucide-react';

const Sidebar = ({ connected }) => {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <h1>VSOC Dashboard</h1>
        <span>Fleet Management</span>
      </div>

      <nav className="sidebar-nav">
        <NavLink
          to="/"
          end
          className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
        >
          <LayoutDashboard />
          <span>Dashboard</span>
        </NavLink>

        <NavLink
          to="/fleet"
          className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
        >
          <Car />
          <span>Fleet</span>
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        <div className="connection-indicator">
          <span className={`connection-dot ${connected ? 'connected' : ''}`} />
          <span>{connected ? 'Connected' : 'Disconnected'}</span>
          {connected ? <Wifi size={14} /> : <WifiOff size={14} />}
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
