const { db } = require('../db/connection');

function findByEmail(email) {
    return new Promise((resolve, reject) => {
        db.get('SELECT id, name, email, pass FROM users WHERE email = ?', [email], (err, row) => {
            if (err) return reject(err);
            resolve(row);
        });
    });
}

function create({ name, email, passwordHash }) {
    return new Promise((resolve, reject) => {
        db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, passwordHash], function (err) {
            if (err) return reject(err);
            resolve(this.lastID);
        });
    });
}

function removeCascade(id) {
    return new Promise((resolve, reject) => {
        db.serialize(() => {
            db.run('BEGIN TRANSACTION');

            db.run(
                'DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)',
                [id],
                (err) => {
                    if (err) {
                        db.run('ROLLBACK');
                        return reject(err);
                    }

                    db.run('DELETE FROM enrollments WHERE user_id = ?', [id], (err) => {
                        if (err) {
                            db.run('ROLLBACK');
                            return reject(err);
                        }

                        db.run('DELETE FROM users WHERE id = ?', [id], function (err) {
                            if (err) {
                                db.run('ROLLBACK');
                                return reject(err);
                            }

                            const changes = this.changes;
                            db.run('COMMIT', (err) => {
                                if (err) return reject(err);
                                resolve(changes);
                            });
                        });
                    });
                }
            );
        });
    });
}

module.exports = { findByEmail, create, removeCascade };
