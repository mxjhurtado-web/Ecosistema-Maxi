const express = require('express');
const router = express.Router();
const {
    getScenarios,
    getScenario,
    createScenario,
    updateScenario,
    deleteScenario,
} = require('../controllers/scenario.controller');
const { protect } = require('../middleware/auth.middleware');

// All routes are protected
router.use(protect);

router.route('/').get(getScenarios).post(createScenario);
router.route('/:id').get(getScenario).put(updateScenario).delete(deleteScenario);

module.exports = router;
