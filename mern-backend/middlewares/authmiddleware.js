// 1. Import 'jsonwebtoken' and your 'User' database model.

// 2. Create an async function called 'protect' taking (req, res, next).
// 3. Declare an empty 'token' variable.

// 4. IF req.headers.authorization exists AND starts with 'Bearer':
    // 5. Open a try...catch block inside this IF statement.
    // 6. TRY: Split the header string by space and grab the token (index 1).
    // 7. TRY: Verify the token using jwt.verify() and your JWT_SECRET.
    // 8. TRY: Find the user by ID (from the decoded token). Chain .select('-password') and assign it to req.user.
    // 9. TRY: Call next() to let them pass.
    // 10. CATCH: Send a 401 status and "Not authorized, token failed" message.

// 11. At the bottom, IF 'token' is still empty, send 401 status and "Not authorized, no token" message.

// 12. Export the 'protect' function using module.exports.


const jwt = require('jsonwebtoken');
const User = require('../models/usermodel');
const protect = async (req, res, next) => {
    let token;  
    if (req.headers.authorization && req.headers.authorization.startsWith('Bearer')) {
        try {
            token = req.headers.authorization.split(' ')[1];    

            const decoded = jwt.verify(token, process.env.JWT_SECRET);

            req.user = await User.findById(decoded.id).select('-password');
            next();
        } catch (error) {
            res.status(401).json({ message: 'Not authorized, token failed' });
        }
    }

    if (!token) {
        res.status(401).json({ message: 'Not authorized, no token' });
    }           

};

module.exports = { protect };