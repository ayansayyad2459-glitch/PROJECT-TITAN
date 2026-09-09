const mongoose = require('mongoose');
const { ResilientTicket } = require('../config/resilientStore');

const ticketSchema = new mongoose.Schema({
    user: {
        type: mongoose.Schema.Types.ObjectId,
        required: false, 
        ref: 'User'
    },
    title: {
        type: String,
        required: [true, 'Please add a title for the issue']
    },
    description: {
        type: String,
        required: [true, 'Please describe the issue']
    },
    source: {
        type: String,
        enum: ['Manual', 'Automated'],
        default: 'Manual'
    },
    status: {
        type: String,
        enum: ['Open', 'In Progress', 'Resolved'],
        default: 'Open'
    },
    charDiff: {
        type: Number,
        default: 0
    }
}, {
    timestamps: true
});

const MongoTicket = mongoose.models.Ticket || mongoose.model('Ticket', ticketSchema);

// Smart Dual-Mode Handler: delegates to ResilientTicket if MongoDB is offline
const TicketProxy = new Proxy(MongoTicket, {
    get(target, prop) {
        if (mongoose.connection.readyState === 1) {
            return target[prop];
        }
        if (prop in ResilientTicket) {
            return ResilientTicket[prop];
        }
        return target[prop];
    }
});

module.exports = TicketProxy;