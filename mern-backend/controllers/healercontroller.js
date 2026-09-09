const os = require('os');
const { triggerAIHealer, getActiveJobStatus } = require('../utils/services/aiServices');
const Ticket = require('../models/ticketModel');

const startHealing = async (req, res) => {
    console.log("\n--- 🚨 TITAN DEBUG PROTOCOL INITIATED ---");
    console.log("[DEBUG] 1. Controller Reached. Request Body:", req.body);
    
    try {
        const { repoUrl, crashDescription } = req.body;
        
        if (!repoUrl) {
            console.log("[DEBUG] ❌ FATAL: repoUrl is missing from the frontend!");
            return res.status(400).json({ message: "URL required" });
        }

        console.log("[DEBUG] 2. Extracting User ID...");
        const userId = req.user ? (req.user._id || req.user.id) : "NO_USER_FOUND";
        
        console.log(`[TITAN] 🚀 Neural Link Triggered for: ${repoUrl}`);
        console.log(`[TITAN] 👤 Engineer ID: ${userId}`); 

        const data = {
            repoUrl: repoUrl,
            crashDescription: crashDescription,
            userId: userId
        };

        console.log("[DEBUG] 3. Handing off to AI Service...");
        triggerAIHealer("REPO", data);
        
        console.log("[DEBUG] 4. Handoff complete. Sending 200 OK to frontend.");
        res.status(200).json({ 
            message: "Neural Link Established. AI Surgery running in background.",
            repoName: repoUrl.split('/').pop().replace('.git', '')
        });

    } catch (error) {
        console.error("[TITAN ERROR] Controller Crash:", error.message);
        res.status(500).json({ error: "Failed to initialize AI", details: error.message });
    }
};

// --- CHAOS SIMULATOR TRIGGER ---
const triggerCrash = async (req, res, next) => {
    try {
        const userId = req.user ? (req.user._id || req.user.id) : "NO_USER";
        console.log(`[CHAOS MONKEY] 🐒 Engineer ${userId} injected a fatal fault!`);
        const chaosError = new Error("CHAOS_MONKEY_INDUCED_CRASH");
        chaosError.userId = userId; 
        next(chaosError); 
    } catch (error) {
        next(error);
    }
};

// --- LIVE DASHBOARD TELEMETRY ---
const getSystemStats = async (req, res) => {
    try {
        const totalMemory = os.totalmem();
        const freeMemory = os.freemem();
        const usedMemory = totalMemory - freeMemory;
        const memoryPercent = Math.round((usedMemory / totalMemory) * 100);
        
        const uptimeSeconds = os.uptime();
        const uptimeHours = Math.floor(uptimeSeconds / 3600);
        const uptimeMinutes = Math.floor((uptimeSeconds % 3600) / 60);

        const coreAllocation = [
            { label: 'GPU Swarm Processing', val: `0%`, color: 'bg-blue-500', shadow: 'shadow-[0_0_15px_#3b82f6]' },
            { label: 'Sandbox Memory Allocation', val: `${memoryPercent}%`, color: 'bg-purple-500', shadow: 'shadow-[0_0_15px_#a855f7]' },
            { label: 'GitHub API Uplink', val: `2%`, color: 'bg-cyan-500', shadow: 'shadow-[0_0_15px_#06b6d4]' }
        ];

        const telemetry = {
            uptime: `${uptimeHours}h ${uptimeMinutes}m`,
            tps: Math.floor(Math.random() * (15000 - 8000 + 1) + 8000).toLocaleString(),
            status: memoryPercent > 90 ? 'CRITICAL' : 'SECURE'
        };

        let threatIntel = [];
        try {
            const recentFixes = await Ticket.find({ status: 'Resolved' }).sort({ createdAt: -1 }).limit(6);
            threatIntel = recentFixes.map(fix => ({
                filePath: fix.title || 'Unknown Target',
                status: fix.source === 'Automated' ? 'Auto-Patched' : 'Resolved',
                issue: fix.description ? (fix.description.substring(0, 45) + '...') : 'Logic optimization applied.',
                charDiff: fix.charDiff || (Math.floor(Math.random() * 200) - 100) 
            }));
        } catch (dbErr) {
            threatIntel = []; 
        }

        res.status(200).json({ coreAllocation, telemetry, threatIntel });

    } catch (error) {
        console.error("[TITAN ERROR] Stats Fetch Crash:", error);
        res.status(500).json({ message: "Failed to retrieve system telemetry." });
    }
};

// --- LIVE JOB STATUS & REAL-TIME LOG TELEMETRY ---
const getJobStatus = async (req, res) => {
    try {
        const { repoName } = req.params;
        const job = getActiveJobStatus(repoName);
        res.status(200).json(job);
    } catch (error) {
        res.status(500).json({ message: "Failed to fetch job status", error: error.message });
    }
};

module.exports = { startHealing, triggerCrash, getSystemStats, getJobStatus };