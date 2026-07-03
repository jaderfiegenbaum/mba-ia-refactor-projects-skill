class AppError extends Error {
    constructor(message, statusCode) {
        super(message);
        this.statusCode = statusCode;
    }
}

class CourseNotFoundError extends AppError {
    constructor(message = 'Curso não encontrado') {
        super(message, 404);
    }
}

class PaymentDeniedError extends AppError {
    constructor(message = 'Pagamento recusado') {
        super(message, 400);
    }
}

module.exports = { AppError, CourseNotFoundError, PaymentDeniedError };
