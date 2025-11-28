const mongoose = require('mongoose');

const scenarioSchema = new mongoose.Schema({
    title: {
        type: String,
        required: [true, 'Please add a title'],
    },
    description: {
        type: String,
        required: [true, 'Please add a description'],
    },
    customerType: {
        type: String,
        required: [true, 'Please add a customer type'],
        enum: ['angry', 'confused', 'happy', 'neutral', 'nervous', 'indecisive'],
        default: 'neutral',
    },
    objective: {
        type: String,
        required: [true, 'Please add an objective for the agent'],
    },
    baseScript: {
        type: String,
        required: [true, 'Please add a base script or guidelines'],
    },
    difficulty: {
        type: String,
        enum: ['easy', 'medium', 'hard'],
        default: 'medium',
    },
    createdAt: {
        type: Date,
        default: Date.now,
    },
});

module.exports = mongoose.model('Scenario', scenarioSchema);
