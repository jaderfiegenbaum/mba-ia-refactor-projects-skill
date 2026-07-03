const PAYMENT_STATUSES = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });

function isCardApproved(cardNumber) {
    return cardNumber.startsWith('4');
}

module.exports = { PAYMENT_STATUSES, isCardApproved };
