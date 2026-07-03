const userModel = require('../models/userModel');
const courseModel = require('../models/courseModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const passwordHasher = require('../services/passwordHasher');
const cache = require('../services/cache');
const logger = require('../config/logger');
const { CourseNotFoundError, PaymentDeniedError } = require('../errors');

const DEFAULT_PASSWORD = '123456';

async function checkout({ username, email, password, courseId, cardNumber }) {
    const course = await courseModel.findActiveById(courseId);
    if (!course) throw new CourseNotFoundError();

    const existingUser = await userModel.findByEmail(email);

    let userId;
    if (existingUser) {
        userId = existingUser.id;
    } else {
        const passwordHash = await passwordHasher.hash(password || DEFAULT_PASSWORD);
        userId = await userModel.create({ name: username, email, passwordHash });
    }

    logger.info('checkout_iniciado', { courseId, userId });

    if (!paymentModel.isCardApproved(cardNumber)) {
        throw new PaymentDeniedError();
    }

    const enrollmentId = await enrollmentModel.completeCheckout({
        userId,
        courseId,
        amount: course.price,
        status: paymentModel.PAYMENT_STATUSES.PAID,
        auditAction: `Checkout curso ${courseId} por ${userId}`,
    });

    cache.set(`last_checkout_${userId}`, course.title);

    return { msg: 'Sucesso', enrollment_id: enrollmentId };
}

module.exports = { checkout };
