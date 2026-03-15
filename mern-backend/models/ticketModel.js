const mongoose = require('mongoose');

const ticketSchema = new mongoose.Schema({
    // 1. Who created it? (Optional, because a robot might create it!)
    user: {
        type: mongoose.Schema.Types.ObjectId,
        required: false, 
        ref: 'User' // This tells MongoDB to link this to the User collection
    },
    // 2. What crashed?
    title: {
        type: String,
        required: [true, 'Please add a title for the issue']
    },
    // 3. The exact error message or notes
    description: {
        type: String,
        required: [true, 'Please describe the issue']
    },
    // 4. Did a human or a robot report this?
    source: {
        type: String,
        enum: ['Manual', 'Automated'], // It MUST be one of these two words
        default: 'Manual'
    },
    // 5. Is it fixed yet?
    status: {
        type: String,
        enum: ['Open', 'In Progress', 'Resolved'],
        default: 'Open'
    }
}, {
    timestamps: true // Automatically adds 'createdAt' and 'updatedAt'
});

module.exports = mongoose.models.Ticket || mongoose.model('Ticket', ticketSchema);