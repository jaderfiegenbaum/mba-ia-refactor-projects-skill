const config = {
    port: parseInt(process.env.PORT || '3000', 10),
    dbPass: process.env.DB_PASS || 'dev-only-password-change-me',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || 'dev-only-key-change-me',
    smtpUser: process.env.SMTP_USER || 'no-reply@example.com',
    adminApiKey: process.env.ADMIN_API_KEY || 'dev-only-admin-key-change-me',
};

module.exports = config;
