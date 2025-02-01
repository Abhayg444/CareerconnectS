// server.js
const express = require('express');
const mongoose = require('mongoose');
const bodyParser = require('body-parser');
const cors = require('cors');
const bcrypt = require('bcrypt'); // Import bcrypt for password hashing
const app = express();
const port = 3000;

// Middleware
app.use(bodyParser.json());
app.use(cors());

// Connect to MongoDB
mongoose.connect('mongodb://localhost:27017/studentDB', { // Replace with your MongoDB Atlas URL if using Atlas
    useNewUrlParser: true,
    useUnifiedTopology: true,
})
    .then(() => console.log('MongoDB connected'))
    .catch((err) => console.log('MongoDB connection error:', err));

// Define the Student schema
const studentSchema = new mongoose.Schema({
    name: String,
    email: String,
    phone: String,
    dob: Date,
    college: String,
    department: String,
    username: { type: String, unique: true },
    password: String, // The password will be hashed
});

// Create the Student model
const Student = mongoose.model('Student', studentSchema);

// Registration Route
app.post('/register', async (req, res) => {
    try {
        const { name, email, phone, dob, college, department, username, password } = req.body;

        // Hash the password before saving
        const hashedPassword = await bcrypt.hash(password, 10);

        const newStudent = new Student({
            name,
            email,
            phone,
            dob,
            college,
            department,
            username,
            password: hashedPassword, // Save the hashed password
        });

        await newStudent.save();
        res.status(201).json({ message: 'Registration successful' });
    } catch (error) {
        if (error.code === 11000) {
            // Handle duplicate username
            res.status(400).json({ message: 'Username already exists' });
        } else {
            res.status(500).json({ message: 'Error during registration', error });
        }
    }
});

// Login Route
app.post('/login', async (req, res) => {
    try {
        const { username, password } = req.body;

        // Find the user by username
        const user = await Student.findOne({ username });

        if (!user) {
            return res.status(401).json({ message: 'Invalid username or password' });
        }

        // Compare the provided password with the hashed password
        const isPasswordValid = await bcrypt.compare(password, user.password);

        if (!isPasswordValid) {
            return res.status(401).json({ message: 'Invalid username or password' });
        }

        // Send user data to the frontend (excluding password)
        res.status(200).json({
            message: 'Login successful',
            user: {
                name: user.name,
                department: user.department,
            }
        });

    } catch (error) {
        res.status(500).json({ message: 'Error during login', error });
    }
});

app.listen(port, () => {
    console.log(`Server running on http://localhost:${port}`);
});
