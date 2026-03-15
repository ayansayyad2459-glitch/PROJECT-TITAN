const Ticket = require('../models/ticketModel');

// @desc    Create a new manual crash ticket
// @route   POST /api/tickets
// @access  Private (Only logged-in engineers)
const createTicket = async (req, res, next) => {
    try {
        // 1. Get the data the engineer typed into the frontend/Postman
        const { title, description } = req.body;

        // 2. Validation: Make sure they didn't leave it blank
        if (!title || !description) {
            return res.status(400).json({ message: "Please add a title and description for the crash" });
        }

        // 3. Create the ticket in the database!
        const ticket = await Ticket.create({
            title,
            description,
            user: req.user.id,     // <-- THIS IS THE MAGIC! We tie it to the logged-in engineer
            source: 'Manual',      // Hardcoded because this is the Front Door
            status: 'Open'
        });

        // 4. Send the new ticket back as proof it worked
        res.status(201).json(ticket);

    } catch (error) {
        next(error);
    }
};

// @desc    Get all tickets for the logged-in engineer
// @route   GET /api/tickets
// @access  Private
const getTickets = async (req, res, next) => {
    try {
        // Find ALL tickets where the 'user' matches the currently logged-in engineer
        const tickets = await Ticket.find({ user: req.user.id });
        
        res.status(200).json(tickets);
    } catch (error) {
        next(error);
    }
};

const updateTicket = async (req, res, next) => {
    try{
        const ticketID = await Ticket.findById(req.params.id);
        if(!ticketID){
            return res.status(404).json({message: "Ticket not found"});
        }
        const updatedTicket = await Ticket.findByIdAndUpdate(
            req.params.id,
            req.body,
            {new: true}
        );
        res.status(200).json(updatedTicket);
    }catch(error){        next(error
        )
    }
};

const deleteTicket = async (req, res, next) => {
    try{
        const ticketID = await Ticket.findById(req.params.id);
        if(!ticketID){
            return res.status(404).json({message: "Ticket not found"});
        }
        const deletedTicket = await Ticket.findByIdAndDelete(req.params.id);
        res.status(200).json({message: "Ticket deleted successfully"});
    }catch(error){next(error)
    }
};
module.exports = { createTicket, getTickets, updateTicket, deleteTicket };