const mongoose = require('mongoose');
const dotenv = require('dotenv');
const connectDB = require('./config/db');
const User = require('./models/user');

dotenv.config();
connectDB();

const importData = async () => {
    try {
        await User.deleteMany();

        const users = [
            {
                name: "Admin User",
                email: "admin@example.com",
                password: "password123", // <--- ADDED THIS
                isAdmin: true
            },
            {
                name: "John Doe",
                email: "john@example.com",
                password: "password123", // <--- ADDED THIS
                isAdmin: false
            }
        ];

        await User.insertMany(users);

        console.log('✅ Data Imported Successfully!');
        process.exit();
    } catch (error) {
        console.error(`❌ Error: ${error.message}`);
        process.exit(1);
    }
};

importData();