const User = require('../models/usermodel');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const generateToken = require('../utils/generateToken');

const loginUser = async (req, res, next) => {
    const { email, password } = req.body;
    try{
        const user = await User.findOne({ email });

        if (user && (await bcrypt.compare(password, user.password))) {
            res.json({
                _id: user.id,
                name: user.name,
                email: user.email,
                token: generateToken(user._id)
            })
        } else {
            res.status(401).json({ message: 'Invalid email or password' });
        }
    }   catch (error) {
        res.status(400).json({ message: error.message });
    }
};

module.exports = { loginUser };