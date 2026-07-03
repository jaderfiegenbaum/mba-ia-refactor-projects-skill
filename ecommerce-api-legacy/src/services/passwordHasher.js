const bcrypt = require('bcryptjs');

const SALT_ROUNDS = 12;

function hash(password) {
    return bcrypt.hash(password, SALT_ROUNDS);
}

function verify(password, passwordHash) {
    return bcrypt.compare(password, passwordHash);
}

module.exports = { hash, verify };
