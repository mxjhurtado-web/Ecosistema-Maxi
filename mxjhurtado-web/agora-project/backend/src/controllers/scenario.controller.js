const Scenario = require('../models/scenario.model');

// @desc    Get all scenarios
// @route   GET /api/scenarios
// @access  Private
exports.getScenarios = async (req, res) => {
    try {
        const scenarios = await Scenario.find();
        res.status(200).json(scenarios);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};

// @desc    Get single scenario
// @route   GET /api/scenarios/:id
// @access  Private
exports.getScenario = async (req, res) => {
    try {
        const scenario = await Scenario.findById(req.params.id);

        if (!scenario) {
            return res.status(404).json({ message: 'Scenario not found' });
        }

        res.status(200).json(scenario);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};

// @desc    Create new scenario
// @route   POST /api/scenarios
// @access  Private/Admin
exports.createScenario = async (req, res) => {
    try {
        const scenario = await Scenario.create(req.body);
        res.status(201).json(scenario);
    } catch (error) {
        res.status(400).json({ message: error.message });
    }
};

// @desc    Update scenario
// @route   PUT /api/scenarios/:id
// @access  Private/Admin
exports.updateScenario = async (req, res) => {
    try {
        const scenario = await Scenario.findById(req.params.id);

        if (!scenario) {
            return res.status(404).json({ message: 'Scenario not found' });
        }

        const updatedScenario = await Scenario.findByIdAndUpdate(
            req.params.id,
            req.body,
            {
                new: true,
                runValidators: true,
            }
        );

        res.status(200).json(updatedScenario);
    } catch (error) {
        res.status(400).json({ message: error.message });
    }
};

// @desc    Delete scenario
// @route   DELETE /api/scenarios/:id
// @access  Private/Admin
exports.deleteScenario = async (req, res) => {
    try {
        const scenario = await Scenario.findById(req.params.id);

        if (!scenario) {
            return res.status(404).json({ message: 'Scenario not found' });
        }

        await scenario.deleteOne();

        res.status(200).json({ id: req.params.id });
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};
