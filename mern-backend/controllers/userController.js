const User = require('../models/usermodel');

// @desc    Get all users
// @route   GET /api/users
const getUser = async (req, res, next) => {
    try {
        // FIX: Added 'await' so we wait for the database.
        // SECURITY: Added .select('-password') so we don't leak password hashes!
        const users = await User.find().select('-password'); 

        // If no users are found for some reason, return an empty array
        if (!users || users.length === 0) {
            return res.status(404).json({ message: "No users found" });
        }

        // Send the users back to Thunder Client / Postman
        res.status(200).json(users);
    } catch (error) {
        next(error);
    }
};

const getUserById = async(req, res, next) => {
    try{
        res.status(200).json({ message: "Get user by ID route" });
    }
    catch (error) {
        next(error);
    }
}

module.exports = { getUser, getUserById };
