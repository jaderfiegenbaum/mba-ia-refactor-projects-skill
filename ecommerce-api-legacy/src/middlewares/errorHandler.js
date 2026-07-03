const logger = require('../config/logger');

function errorHandler(err, req, res, next) {
    if (err.statusCode) {
        return res.status(err.statusCode).json({ error: err.message });
    }

    logger.error('unhandled_error', { message: err.message });
    res.status(500).json({ error: 'internal server error' });
}

module.exports = errorHandler;
