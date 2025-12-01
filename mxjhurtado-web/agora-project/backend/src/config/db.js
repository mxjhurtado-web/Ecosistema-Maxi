const mongoose = require('mongoose');
const { MongoMemoryServer } = require('mongodb-memory-server');

const connectDB = async () => {
    try {
        console.log("Starting MongoDB Memory Server... (this may take a moment the first time)");
        const mongod = await MongoMemoryServer.create();
        const uri = mongod.getUri();

        console.log(`MongoDB Memory Server started at ${uri}`);

        const conn = await mongoose.connect(uri, {
            useNewUrlParser: true,
            useUnifiedTopology: true,
        });

        console.log(`MongoDB Connected: ${conn.connection.host}`);
    } catch (error) {
        console.error(`Error: ${error.message}`);
        process.exit(1);
    }
};

module.exports = connectDB;
