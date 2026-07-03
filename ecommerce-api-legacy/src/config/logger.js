function log(level, message, meta = {}) {
    console.log(JSON.stringify({ level, message, ...meta, timestamp: new Date().toISOString() }));
}

module.exports = {
    info: (message, meta) => log('info', message, meta),
    error: (message, meta) => log('error', message, meta),
};
