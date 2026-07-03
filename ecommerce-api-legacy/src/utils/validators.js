const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const CARD_NUMBER_REGEX = /^\d{13,19}$/;
const ID_REGEX = /^\d+$/;

function isValidEmail(email) {
    return typeof email === 'string' && EMAIL_REGEX.test(email);
}

function isValidCardNumber(cardNumber) {
    return typeof cardNumber === 'string' && CARD_NUMBER_REGEX.test(cardNumber);
}

function isValidId(id) {
    return ID_REGEX.test(String(id));
}

module.exports = { isValidEmail, isValidCardNumber, isValidId };
