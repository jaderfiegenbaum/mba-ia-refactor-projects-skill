const userModel = require('../models/userModel');

async function remove(id) {
    const changes = await userModel.removeCascade(id);
    return { deleted: changes > 0 };
}

module.exports = { remove };
