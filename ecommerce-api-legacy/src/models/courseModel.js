const { db } = require('../db/connection');

function findActiveById(id) {
    return new Promise((resolve, reject) => {
        db.get('SELECT * FROM courses WHERE id = ? AND active = 1', [id], (err, row) => {
            if (err) return reject(err);
            resolve(row);
        });
    });
}

module.exports = { findActiveById };
