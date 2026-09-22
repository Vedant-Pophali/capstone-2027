# VSOC Admin Dashboard

This directory contains the frontend (React/Vite) and backend (Node/Express) for the Vehicle Security Operations Center (VSOC) Admin Dashboard.

## Prerequisites
- Node.js installed
- Docker Desktop installed and running (required to successfully add vehicle containers to the fleet)

## How to Start

You will need to open two separate PowerShell terminal windows to run both the backend API and the frontend UI concurrently.

### 1. Start the Backend Server

Open your first PowerShell window, navigate to the backend directory, install dependencies, and start the server:

```powershell
# Navigate into the server directory
cd server

# Install the necessary dependencies (only required the first time)
npm install

# Start the Express API server
node index.js
```

The backend API will start running on `http://localhost:3001`.

### 2. Start the Frontend Client

Open your second PowerShell window, navigate to the frontend directory, install dependencies, and start the development server:

```powershell
# Navigate into the client directory
cd client

# Install the necessary dependencies (only required the first time)
npm install

# Start the Vite development server
npm run dev
```

The frontend UI will become available at `http://localhost:5173`. Open this URL in your web browser to access the dashboard.
