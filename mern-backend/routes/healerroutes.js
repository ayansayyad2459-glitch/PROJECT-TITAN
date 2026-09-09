const express = require('express');
const router = express.Router();

// 1. Import functions from your controller
const { 
    startHealing, 
    getSystemStats, 
    triggerCrash,
    getJobStatus
} = require('../controllers/healercontroller');

const { protect } = require('../middlewares/authmiddleware');

// GET /api/healer/stats - Live Telemetry
router.get('/stats', protect, getSystemStats);

// GET /api/healer/status/:repoName - Live Job Telemetry & Logs
router.get('/status/:repoName', protect, getJobStatus);

// POST /api/healer/start - Manual AI Trigger
router.post('/start', protect, startHealing);

// POST /api/healer/crash - The Chaos Monkey Trigger
// 2. Point this directly to the controller function we just wrote
router.post('/crash', protect, triggerCrash);

module.exports = router;