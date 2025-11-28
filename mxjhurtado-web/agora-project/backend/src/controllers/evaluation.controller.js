const evaluationService = require('../services/evaluation.service');
const Scenario = require('../models/scenario.model');

// @desc    Evaluate a completed simulation
// @route   POST /api/evaluation
// @access  Private
exports.evaluateSimulation = async (req, res) => {
    try {
        const { history, scenarioId } = req.body;

        const scenario = await Scenario.findById(scenarioId);
        if (!scenario) {
            return res.status(404).json({ message: 'Scenario not found' });
        }

        const result = await evaluationService.evaluateSimulation(history, scenario);
        res.status(200).json(result);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};
