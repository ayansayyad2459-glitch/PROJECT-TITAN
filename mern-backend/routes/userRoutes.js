const express = require('express');
const router = express.Router();
const { getUser } = require('../controllers/userController');
const { registerUser } = require('../controllers/registercontroller');
const logger = require('../utils/logger');
const { loginUser } = require('../controllers/logincontroller');
const { protect } = require('../middlewares/authmiddleware');
const { getUserById } = require('../controllers/userController');

// Route: POST /api/users (for registration)
router.post('/', registerUser);
// Route: GET /api/users
router.get('/',protect, getUser);

router.post('/login', loginUser);

router.get('/me', protect, getUserById);



module.exports = router;