const express = require('express');
const config = require('./config');
const { initSchema } = require('./db/connection');
const routes = require('./routes');
const errorHandler = require('./middlewares/errorHandler');

const app = express();
app.use(express.json());

initSchema();

app.use(routes);
app.use(errorHandler);

app.listen(config.port, () => {
    console.log(`Frankenstein LMS rodando na porta ${config.port}...`);
});

module.exports = app;
