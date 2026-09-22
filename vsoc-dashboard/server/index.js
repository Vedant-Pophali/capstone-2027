const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const fleetService = require('./services/FleetService');

const app = express();
const server = http.createServer(app);

// Setup Socket.IO for real-time updates
const io = new Server(server, {
  cors: {
    origin: '*',
    methods: ['GET', 'POST']
  }
});

const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Socket.IO connection handling
io.on('connection', (socket) => {
  console.log(`Client connected: ${socket.id}`);
  
  socket.on('disconnect', () => {
    console.log(`Client disconnected: ${socket.id}`);
  });
});

// REST Routes
app.get('/api/fleet', async (req, res) => {
  try {
    const fleet = await fleetService.getFleetStatus();
    res.json({ success: true, data: fleet });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

app.post('/api/fleet/add', async (req, res) => {
  try {
    const { vehicleId } = req.body;
    if (!vehicleId) {
      return res.status(400).json({ success: false, message: 'vehicleId is required' });
    }
    const vehicle = await fleetService.addVehicle(vehicleId);
    
    // Broadcast the new vehicle to all connected clients
    io.emit('fleet_update', { type: 'ADDED', vehicle });
    
    res.status(201).json({ success: true, data: vehicle });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

app.delete('/api/fleet/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const result = await fleetService.removeVehicle(id);
    
    // Broadcast the removed vehicle ID to all connected clients
    io.emit('fleet_update', { type: 'REMOVED', vehicleId: id });
    
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// --- NEW WEBHOOK ENDPOINT FOR THE GO GATEWAY ---
app.post('/api/webhook/status-update', (req, res) => {
  try {
    const { vehicleId, status, details } = req.body;
    
    if (!vehicleId || !status) {
      return res.status(400).json({ success: false, message: 'vehicleId and status are required' });
    }

    // In a real database, we would update the vehicle's status in SQLite here.
    // For now, we update our memory map
    if (fleetService.vehicles.has(vehicleId.toString())) {
      const vehicle = fleetService.vehicles.get(vehicleId.toString());
      vehicle.status = status;
      vehicle.details = details || '';
      
      // Emit the real-time update to the React dashboard
      io.emit('fleet_update', { type: 'STATUS_CHANGED', vehicle });
      
      return res.json({ success: true, message: 'Status updated and broadcasted' });
    } else {
      return res.status(404).json({ success: false, message: 'Vehicle not found in fleet' });
    }
  } catch (error) {
    console.error('Webhook error:', error);
    res.status(500).json({ success: false, message: 'Internal Server Error' });
  }
});

server.listen(PORT, () => {
  console.log(`VSOC Admin Dashboard API & WebSocket running on http://localhost:${PORT}`);
});
