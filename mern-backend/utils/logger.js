const winston = require('winston');

const Logger = winston.createLogger({
    Level: 'error',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
    ),
    transports: [
        new winston.transports.File({ filename: 'error.log', level: 'error' }),
    ],
});

module.exports = Logger;