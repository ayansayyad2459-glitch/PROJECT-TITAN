const express = require('express');
const router = express.Router();

// Existing Controllers
const { getUser, getUserById } = require('../controllers/userController');
const { registerUser } = require('../controllers/registercontroller');
const logger = require('../utils/logger');
const { loginUser } = require('../controllers/logincontroller');
const { protect } = require('../middlewares/authmiddleware');

// 🔐 TITAN BYOK IMPORTS
const User = require('../models/usermodel'); 
const { encrypt } = require('../utils/encryption');

// --- YOUR EXISTING ROUTES ---
router.post('/', registerUser);
router.get('/', protect, getUser);
router.post('/login', loginUser);
router.get('/me', protect, getUserById);

// --- 🚀 PROJECT TITAN NEW ROUTE ---
// Route: POST /api/users/save-key
router.post('/save-key', async (req, res) => {
    try {
        const { userId, apiKey } = req.body;

        if (!userId || !apiKey) {
            return res.status(400).json({ error: "Missing user ID or API key" });
        }

        // Lock it in the vault
        const scrambledKey = encrypt(apiKey);

        // Save it to MongoDB
        const updatedUser = await User.findByIdAndUpdate(
            userId,
            { 
                encryptedApiKey: scrambledKey, 
                hasValidKey: true 
            },
            { returnDocument: 'after' }
        );

        if (!updatedUser) {
            return res.status(404).json({ error: "User not found in database" });
        }

        return res.status(200).json({ 
            message: "API Key secured and saved in MongoDB.",
            hasValidKey: updatedUser.hasValidKey
        });

    } catch (error) {
        console.error("MongoDB error saving key:", error);
        return res.status(500).json({ error: "Internal server error" });
    }
});

// THIS MUST BE THE LAST LINE
module.exports = router;