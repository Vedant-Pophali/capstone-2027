import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import ToastContainer from '../ui/ToastContainer';

const Layout = ({ connected }) => {
  return (
    <div className="app-layout">
      <Sidebar connected={connected} />
      <main className="main-content">
        <Outlet />
      </main>
      <ToastContainer />
    </div>
  );
};

export default Layout;
