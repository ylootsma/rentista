"""Turns Mollie payment updates into order and subscription changes.

Both the webhook (Mollie calls us) and the return page (the customer comes back)
call these functions, so every step is written to be safe when it runs twice.
"""
import datetime
import os

from flask import request

from models.order import Order
from models.order_outfit import Order_Outfit
from models.outfit import Outfit
from models.size import Size
from models.subscription import Subscription
from rentista_web.util import mollie

AWAITING_PAYMENT = "awaiting_payment"
PROCESSING = "processing_payment"
PAYMENT_FAILED = "payment_failed"
PREPARATION = "preparation"
UNPAID_STATUSES = (AWAITING_PAYMENT, PROCESSING, PAYMENT_FAILED)

SIZE_FIELDS = ("size_xs", "size_s", "size_m", "size_l", "size_xl")


def base_url():
    return (os.getenv("BASE_URL") or request.url_root).rstrip("/")


# ---------------------------------------------------------------- orders

def reserve_stock(order):
    """Take the ordered sizes out of stock. Runs once per paid order."""
    for order_outfit in Order_Outfit.select().where(Order_Outfit.order == order.id):
        size = Size.get_or_none(Size.outfit == order_outfit.outfit_id)
        if size is None:
            continue
        field = order_outfit.size
        if field in SIZE_FIELDS:
            setattr(size, field, int(getattr(size, field)) - 1)
            size.save()
        total = sum(int(getattr(size, f)) for f in SIZE_FIELDS)
        if total < 1:
            outfit = Outfit.get_by_id(order_outfit.outfit_id)
            outfit.in_stock = False
            outfit.save()


def finalize_order(order_id):
    """Mark a paid order as ready for preparation.

    The conditional update makes sure only one caller (webhook or return
    page) gets to reserve the stock.
    """
    claimed = (Order
               .update(status=PROCESSING)
               .where((Order.id == order_id) & (Order.status.in_([AWAITING_PAYMENT, PAYMENT_FAILED])))
               .execute())
    if not claimed:
        return False
    order = Order.get_by_id(order_id)
    reserve_stock(order)
    order.status = PREPARATION
    order.is_open = True
    order.save()
    return True


def handle_order_payment(payment):
    """Update the order that belongs to a Mollie payment. Returns the order."""
    order_id = (payment.get("metadata") or {}).get("order_id")
    order = Order.get_or_none(Order.id == order_id) if order_id else None
    if order is None or order.mollie_payment_id != payment["id"]:
        return None

    status = payment["status"]
    if status == "authorized":
        # Klarna, Riverty and in3 first authorize; capturing releases the money
        # for payout. Rentista ships rentals right away, so capture straight away.
        try:
            mollie.capture_payment(payment["id"])
        except mollie.MollieError:
            pass  # already captured by the other caller
        finalize_order(order.id)
    elif status == "paid":
        finalize_order(order.id)
    elif status in ("failed", "canceled", "expired"):
        Order.update(status=PAYMENT_FAILED).where(
            (Order.id == order.id) & (Order.status == AWAITING_PAYMENT)).execute()
    return Order.get_by_id(order.id)


# ---------------------------------------------------------------- subscriptions

def add_one_month(day):
    month = day.month % 12 + 1
    year = day.year + (1 if day.month == 12 else 0)
    for candidate in (day.day, 30, 29, 28):
        try:
            return day.replace(year=year, month=month, day=candidate)
        except ValueError:
            continue


def handle_subscription_payment(payment):
    """Update a subscription after its first or a monthly payment."""
    status = payment["status"]

    # Monthly payments made by a Mollie subscription.
    if payment.get("subscriptionId"):
        subscription = Subscription.get_or_none(
            Subscription.mollie_subscription_id == payment["subscriptionId"])
        if subscription is None:
            return None
        if status == "paid":
            subscription.subscription_active = True
            subscription.save()
        elif status in ("failed", "canceled", "expired"):
            subscription.subscription_active = False
            subscription.save()
        return subscription

    # The first payment, which also gives Mollie permission for the monthly debit.
    subscription_id = (payment.get("metadata") or {}).get("subscription_id")
    subscription = Subscription.get_or_none(Subscription.id == subscription_id) if subscription_id else None
    if subscription is None or subscription.mollie_payment_id != payment["id"]:
        return None
    if status != "paid":
        return subscription

    # Claim the subscription so the monthly debit is only created once.
    claimed = (Subscription
               .update(mollie_subscription_id="creating")
               .where((Subscription.id == subscription.id) & (Subscription.mollie_subscription_id.is_null()))
               .execute())
    if not claimed:
        return Subscription.get_by_id(subscription.id)

    start = add_one_month(datetime.date.today())
    try:
        mollie_subscription = mollie.create_subscription(
            customer_id=payment["customerId"],
            amount=subscription.subscription_price,
            interval="1 month",
            start_date=start,
            description="Rentista abonnement %s outfits (#%s)" % (
                subscription.subscription_type, subscription.id),
            webhook=mollie.webhook_url(base_url(), "/subscriptions/webhook"),
            metadata={"subscription_id": subscription.id},
        )
    except mollie.MollieError:
        Subscription.update(mollie_subscription_id=None).where(
            Subscription.id == subscription.id).execute()
        raise

    subscription = Subscription.get_by_id(subscription.id)
    subscription.mollie_subscription_id = mollie_subscription["id"]
    subscription.subscription_active = True
    subscription.save()
    return subscription


def active_subscription(user_id):
    return (Subscription
            .select()
            .where((Subscription.user == user_id) & (Subscription.subscription_active == True))  # noqa: E712
            .first())
