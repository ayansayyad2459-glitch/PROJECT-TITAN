// 1. Create an async function called 'protectAPI' taking (req, res, next).
// 2. Grab the API key the robot sent. Robots usually send this in a header called 'x-api-key'.
//    (Assign req.headers['x-api-key'] to a variable called 'apiKey').
// 3. IF the 'apiKey' exists AND it strictly equals (===) process.env.API_KEY:
//      - Call next() to let the robot through!
// 4. ELSE (If it's missing or wrong):
//      - Send a 401 status and a JSON message: "Not authorized, invalid API Key".
// 5. Export the 'protectAPI' function.


const protectAPI = async (req, res, next) => {
    const apiKey = req.headers['x-api-key'];

    if (!apiKey || apiKey !== process.env.API_KEY) {
        return res.status(401).json({ error: "Not authorized, invalid API Key" });
    }

    next();
};

module.exports = { protectAPI };