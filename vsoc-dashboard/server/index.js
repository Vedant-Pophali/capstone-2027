const express = require('express');
const cors = require('cors');
const fleetService = require('./services/FleetService');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Routes
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
    res.status(201).json({ success: true, data: vehicle });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

app.delete('/api/fleet/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const result = await fleetService.removeVehicle(id);
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`VSOC Admin Dashboard API running on http://localhost:${PORT}`);
});
