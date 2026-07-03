const financialReportModel = require('../models/financialReportModel');

async function getFinancialReport() {
    const rows = await financialReportModel.getReportRows();

    const reportByCourse = new Map();

    for (const row of rows) {
        if (!reportByCourse.has(row.course_id)) {
            reportByCourse.set(row.course_id, { course: row.course_title, revenue: 0, students: [] });
        }
        const courseData = reportByCourse.get(row.course_id);

        if (row.enrollment_id != null) {
            courseData.students.push({
                student: row.student_name || 'Unknown',
                paid: row.payment_amount || 0,
            });

            if (row.payment_status === 'PAID') {
                courseData.revenue += row.payment_amount;
            }
        }
    }

    return Array.from(reportByCourse.values());
}

module.exports = { getFinancialReport };
