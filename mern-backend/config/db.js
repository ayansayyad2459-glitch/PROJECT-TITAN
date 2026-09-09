const mongoose = require('mongoose');

let isConnected = false;

const connectDB = async () => {
    const mongoUri = process.env.MONGODB_URL || process.env.MONGO_URI;

    // 1. Try Primary URI from .env
    if (mongoUri && !mongoUri.includes('<your_cluster_url>')) {
        try {
            console.log(`[DATABASE] Attempting connection to MongoDB Atlas...`);
            const conn = await mongoose.connect(mongoUri, {
                serverSelectionTimeoutMS: 3000,
                connectTimeoutMS: 3000
            });
            console.log(`[DATABASE] 🟢 MongoDB Atlas Connected: ${conn.connection.host}`);
            isConnected = true;
            return;
        } catch (error) {
            console.warn(`[DATABASE] ⚠️ MongoDB Atlas connection error: ${error.message}`);
        }
    }

    // 2. Try Local MongoDB on default port
    try {
        console.log(`[DATABASE] Probing local MongoDB instance (127.0.0.1:27017)...`);
        const conn = await mongoose.connect('mongodb://127.0.0.1:27017/project-titan', {
            serverSelectionTimeoutMS: 1500,
            connectTimeoutMS: 1500
        });
        console.log(`[DATABASE] 🟢 Local MongoDB Connected: ${conn.connection.host}`);
        isConnected = true;
        return;
    } catch (localErr) {
        console.warn(`[DATABASE] ⚠️ Local MongoDB not found.`);
    }

    // 3. Resilient Fallback - NEVER CRASH THE SERVER!
    console.log(`[DATABASE] 🛡️ TITAN Autonomous Resilience Protocol ACTIVE.`);
    console.log(`[DATABASE] 💾 Using Persistent Local Store (data/titan_local_store.json). Server online.`);
    isConnected = false;
};

const getIsConnected = () => isConnected;

module.exports = connectDB;
module.exports.getIsConnected = getIsConnected;