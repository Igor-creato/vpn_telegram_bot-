# payment/yookassa_handler.py
import uuid
import yookassa
from yookassa import Payment

yookassa.Configuration.configure('1010483', 'test_FJXioO5_pc4olCr1-o0UYDSSrfD--l6gb93zOMqVUfA')

def create_payment(amount, payment_id):
    idempotence_key = str(uuid.uuid4())
    payment = Payment.create({
        "amount": {
            "value": amount,
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://yourwebsite.com"
        },
        "capture": True,
        "description": f"Оплата заказа No{payment_id}"
    }, idempotence_key)

    return payment.confirmation.confirmation_url, payment.id

def check_payment_status(payment_id):
    payment = Payment.find_one(payment_id)
    return payment.status

