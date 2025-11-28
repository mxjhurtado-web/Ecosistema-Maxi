const express = require('express');
const router = express.Router();
const { evaluateSimulation } = require('../controllers/evaluation.controller');
const { protect } = require('../middleware/auth.middleware');

router.post('/', protect, evaluateSimulation);

module.exports = router;
