const mongoose = require('mongoose');
const { ResilientUser } = require('../config/resilientStore');

const userschema = mongoose.Schema(
    {
        name: {
            type: String,
            required: true,
        },
        email: {
            type: String,
            required: true,
            unique: true,
        },
        password: {
            type: String,
            required: true,
        },
        isAdmin: {
            type: Boolean,
            required: true,
            default: false,
        },
        encryptedKey: {
            type: String,  
            default: null,
        },
        hasValidKey: {
            type: Boolean,
            default: false,
        },
    },   
    {
        timestamps: true,
    }
);

const MongoUser = mongoose.models.User || mongoose.model('User', userschema);

// Smart Dual-Mode Handler: delegates to ResilientUser if MongoDB is offline
const UserProxy = new Proxy(MongoUser, {
    get(target, prop) {
        if (mongoose.connection.readyState === 1) {
            return target[prop];
        }
        if (prop in ResilientUser) {
            return ResilientUser[prop];
        }
        return target[prop];
    }
});

module.exports = UserProxy;