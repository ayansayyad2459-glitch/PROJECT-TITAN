const Ticket = require('../models/ticketModel');
const { triggerAIHealer } = require('../utils/services/aiServices'); 

const recieveautomatedcrash = async (req,res ,next) => {
    try{
        const { title, description} = req.body;
        if (!title || !description) return res.status(400).json({message: "Please add a title and description for the crash"});
        
        const ticket = await Ticket.create({
            title, description, source: 'Automated', status: 'Open'
        });

        //   WAKE UP THE AI BRAIN TO FIX THE CRASH
        triggerAIHealer("CRASH", description);

        res.status(201).json(ticket);
    } catch (error) { next(error); }
};
module.exports = { recieveautomatedcrash };