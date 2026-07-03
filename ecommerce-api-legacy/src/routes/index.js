const express = require('express');
const checkoutController = require('../controllers/checkoutController');
const adminController = require('../controllers/adminController');
const userController = require('../controllers/userController');
const requireAdmin = require('../middlewares/requireAdmin');
const { isValidEmail, isValidCardNumber, isValidId } = require('../utils/validators');

const router = express.Router();

router.post('/api/checkout', async (req, res, next) => {
    const { usr: username, eml: email, pwd: password, c_id: courseId, card: cardNumber } = req.body;

    if (!username || !email || !courseId || !cardNumber) {
        return res.status(400).send('Bad Request');
    }
    if (!isValidId(courseId) || !isValidEmail(email) || !isValidCardNumber(cardNumber)) {
        return res.status(400).send('Bad Request');
    }

    try {
        const result = await checkoutController.checkout({ username, email, password, courseId, cardNumber });
        res.status(200).json(result);
    } catch (err) {
        next(err);
    }
});

router.get('/api/admin/financial-report', async (req, res, next) => {
    try {
        const report = await adminController.getFinancialReport();
        res.json(report);
    } catch (err) {
        next(err);
    }
});

router.delete('/api/users/:id', requireAdmin, async (req, res, next) => {
    if (!isValidId(req.params.id)) {
        return res.status(400).send('Bad Request');
    }

    try {
        await userController.remove(req.params.id);
        res.send('Usuário deletado.');
    } catch (err) {
        next(err);
    }
});

module.exports = router;
