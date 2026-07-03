const { db } = require('../db/connection');

function completeCheckout({ userId, courseId, amount, status, auditAction }) {
    return new Promise((resolve, reject) => {
        db.serialize(() => {
            db.run('BEGIN TRANSACTION');

            db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId], function (err) {
                if (err) {
                    db.run('ROLLBACK');
                    return reject(err);
                }
                const enrollmentId = this.lastID;

                db.run(
                    'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
                    [enrollmentId, amount, status],
                    (err) => {
                        if (err) {
                            db.run('ROLLBACK');
                            return reject(err);
                        }

                        db.run(
                            "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
                            [auditAction],
                            (err) => {
                                if (err) {
                                    db.run('ROLLBACK');
                                    return reject(err);
                                }

                                db.run('COMMIT', (err) => {
                                    if (err) return reject(err);
                                    resolve(enrollmentId);
                                });
                            }
                        );
                    }
                );
            });
        });
    });
}

module.exports = { completeCheckout };
