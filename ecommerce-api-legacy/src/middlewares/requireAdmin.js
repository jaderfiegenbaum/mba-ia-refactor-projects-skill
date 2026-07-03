const config = require('../config');

function requireAdmin(req, res, next) {
    const providedKey = req.header('x-admin-key');
    if (!providedKey || providedKey !== config.adminApiKey) {
        return res.status(403).json({ error: 'forbidden' });
    }
    next();
}

module.exports = requireAdmin;
