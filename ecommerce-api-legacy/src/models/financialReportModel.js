const { db } = require('../db/connection');

function getReportRows() {
    return new Promise((resolve, reject) => {
        const query = `
            SELECT
                c.id AS course_id,
                c.title AS course_title,
                e.id AS enrollment_id,
                u.name AS student_name,
                p.amount AS payment_amount,
                p.status AS payment_status
            FROM courses c
            LEFT JOIN enrollments e ON e.course_id = c.id
            LEFT JOIN users u ON u.id = e.user_id
            LEFT JOIN payments p ON p.enrollment_id = e.id
            ORDER BY c.id
        `;
        db.all(query, [], (err, rows) => {
            if (err) return reject(err);
            resolve(rows);
        });
    });
}

module.exports = { getReportRows };
