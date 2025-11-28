const express = require('express');
const router = express.Router();
const { protect } = require('../middleware/auth.middleware');

// Placeholder for future REST endpoints related to simulation history
// e.g., GET /api/simulation/history

router.get('/history', protect, (req, res) => {
    res.json({ message: "Simulation history endpoint" });
});

module.exports = router;
