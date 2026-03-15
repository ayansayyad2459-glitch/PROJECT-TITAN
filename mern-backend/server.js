// server.js
const express = require('express');
const dotenv = require('dotenv');
const cors = require('cors');
const path = require('path');
const connectDB = require('./config/db');
const { triggerAIHealer } = require('./utils/services/aiServices'); // 👈 Import the Brain
dotenv.config();
connectDB();
const fs = require('fs');
const downloadDir = path.join(__dirname, 'public', 'downloads');
if (!fs.existsSync(downloadDir)) {
    fs.mkdirSync(downloadDir, { recursive: true });
    console.log(`[SYSTEM] Created directory: ${downloadDir}`);
}

const app = express();

app.use(cors({
  origin: "*", 
  methods: ["GET", "POST", "PUT", "DELETE"],
  credentials: true
}));
app.use(express.json());

// Add this right below app.use(express.json());
app.use((req, res, next) => {
    console.log(`[RADAR] Incoming Request: ${req.method} ${req.url}`);
    next();
});

// --- THE BULLETPROOF DOWNLOAD ROUTE ---
app.get('/downloads/:filename', (req, res) => {
    // This perfectly calculates the exact path from server.js to the file
    const filePath = path.join(__dirname, 'public', 'downloads', req.params.filename);
    
    console.log(`[DOWNLOAD INITIATED] Fetching: ${filePath}`);
    
    res.download(filePath, (err) => {
        if (err) {
            console.error(`[DOWNLOAD ERROR] File not found at: ${filePath}`);
            res.status(404).send("File not found or still generating.");
        } else {
            console.log(`[DOWNLOAD SUCCESS] File delivered: ${req.params.filename}`);
        }
    });
});

// 👉 YOUR HANDWRITTEN ROUTES
app.use('/api/users', require('./routes/userRoutes'));
app.use('/api/tickets', require('./routes/ticketroutes'));
app.use('/api/healer', require('./routes/healerroutes'));

// --- FEATURE 2: THE AUTOMATED SRE TRAP ---
// If any API route fails, it falls into this trap, and the AI takes over!
// --- FEATURE 2: THE AUTOMATED SRE TRAP ---
app.use(async (err, req, res, next) => {
    console.log(`\n[SYSTEM] 💥 CRASH DETECTED! Routing to TITAN...`);
    
    try {
        const Ticket = require('./models/ticketModel'); 
        
        // Save the ticket directly to the Ledger
        await Ticket.create({
            title: "Chaos Monkey Simulator",
            description: err.message || "Fatal runtime fault injected by engineer.",
            status: "Open",
            source: "Automated",
            user: req.user ? req.user._id : null // 👈 THIS IS THE FIX! Link it to the logged-in user
        });

        console.log(`[TITAN BRAIN] ✅ Incident logged to DB.`);

        res.status(500).json({ 
            error: "Server crashed, but Titan AI intercepted it and logged a ticket!"
        });

    } catch (dbErr) {
        console.error("[TITAN ERROR] Failed to save ticket:", dbErr.message);
        res.status(500).json({ error: "System total failure." });
    }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`🚀 TITAN MVC BACKEND ACTIVE ON PORT ${PORT}`));