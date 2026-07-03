const logger = require('../config/logger');

const store = new Map();

function set(key, value) {
    logger.info('cache_set', { key });
    store.set(key, value);
}

function get(key) {
    return store.get(key);
}

module.exports = { set, get };
