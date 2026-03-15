const jwt = require('jsonwebtoken');
const User = require('../models/usermodel');
const bcrypt = require('bcryptjs');
const generateToken = require('../utils/generateToken');

// @desc    Register a new user
// @route   POST /api/users
const registerUser = async (req, res, next) => {
    const { name, email, password } = req.body;

    try {
        // 1. Validation: Check if data exists
        if (!name || !email || !password) {
            res.status(400);
            throw new Error('Please add all fields');
        }

        // 2. Check if user already exists
        const userExists = await User.findOne({ email });
        if (userExists) {
            res.status(400);
            throw new Error('User already exists');
        }

        // 3. Hash the password
        const salt = await bcrypt.genSalt(10);
        const hashedPassword = await bcrypt.hash(password, salt);

        // 4. Create a new user
        const user = await User.create({
            name,
            email,
            password: hashedPassword, 
        });

        // 5. Send Response
        if (user) {
            res.status(201).json({
                _id: user.id,
                name: user.name,
                email: user.email,
                token: generateToken(user._id)
            });
        } else {
            res.status(400);
            throw new Error('Invalid user data');
        }
    } catch (error) {
        // If status wasn't set, default to 400
        if (res.statusCode === 200) res.status(400);
        res.json({ message: error.message });
    }
};


module.exports = { registerUser };