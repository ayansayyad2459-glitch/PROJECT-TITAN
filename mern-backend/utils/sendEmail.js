const nodemailer = require('nodemailer');

const sendEmail = async (options) => {
    // 1. Create the transporter connecting to Gmail
    const transporter = nodemailer.createTransport({
        service: 'Gmail',
        auth: {
            user: process.env.EMAIL_USER,
            pass: process.env.EMAIL_PASS,
        },
    });

    // 2. Define the email contents
    const mailOptions = {
        from: `TITAN NEURAL CORE <${process.env.EMAIL_USER}>`,
        to: options.email,
        subject: options.subject,
        text: options.message,
    };

    // 3. Send the email
    await transporter.sendMail(mailOptions);
};

module.exports = sendEmail;