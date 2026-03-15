const express = require('express');
const router = express.Router();

// 1. Import all three functions from your controller
const { 
    startHealing, 
    getSystemStats, 
    triggerCrash 
} = require('../controllers/healercontroller');

const { protect } = require('../middlewares/authmiddleware');

// GET /api/healer/stats - Live Telemetry
router.get('/stats', protect, getSystemStats);

// POST /api/healer/start - Manual AI Trigger
router.post('/start', protect, startHealing);

// POST /api/healer/crash - The Chaos Monkey Trigger
// 2. Point this directly to the controller function we just wrote
router.post('/crash', protect, triggerCrash);

module.exports = router;