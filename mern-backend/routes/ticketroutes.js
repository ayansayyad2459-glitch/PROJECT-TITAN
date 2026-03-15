const express = require('express');
const router = express.Router();

// 1. Import the Human functions
const { createTicket, getTickets } = require('../controllers/ticketcontroller');
// 2. Import the Robot function from your NEW file
const { recieveautomatedcrash } = require('../controllers/apiticketcontroller'); 
// 3. Import the update function
const { updateTicket } = require('../controllers/ticketcontroller');

// 3. Import both Bouncers
const { protect } = require('../middlewares/authmiddleware');
const { protectAPI } = require('../middlewares/apimiddleware');

// import delete function
const { deleteTicket } = require('../controllers/ticketcontroller');


// Human Doors
router.post('/', protect, createTicket);
router.get('/', protect, getTickets);

// Robot Door
router.post('/webhook', protectAPI, recieveautomatedcrash);

// update ticket
router.put('/:id', protect, updateTicket);

// delete ticket
router.delete('/:id', protect, deleteTicket);


module.exports = router;