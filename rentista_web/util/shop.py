import datetime
from random import randrange

import peewee as pw
from flask import session

from models.base_model import db
from models.order import Order
from models.order_outfit import Order_Outfit
from models.outfit import Outfit
from models.size import Size
from models.subscription import Subscription

SIZES = ['size_xs', 'size_s', 'size_m', 'size_l', 'size_xl']

# Prices and number of outfits per subscription plan. The server is the only
# source of truth for these: never trust a price sent by the browser.
PLANS = {
    'standard': {'price': 93, 'outfits': 3},
    'premium': {'price': 109, 'outfits': 4},
    'exclusive': {'price': 125, 'outfits': 5},
}

# Each extra item after the first gets this discount.
MULTI_ITEM_DISCOUNT = 0.33


def included_outfits(subscription):
    # subscription_type holds the number of outfits; older rows may hold the plan name
    value = str(subscription.subscription_type)
    if value in PLANS:
        return PLANS[value]['outfits']
    return int(value)


def get_cart():
    return list(session.get('cart', [])), list(session.get('size', []))


def clear_cart():
    session.pop('cart', None)
    session.pop('size', None)


def cart_summary(user):
    """Work out what the current cart costs for this user (None = visitor)."""
    cart, _ = get_cart()
    subscription = None
    amount = 0
    discount = 0
    surplus = []
    sub = []

    if cart and user is not None:
        subscription = Subscription.get_or_none(Subscription.user == user.id)

    if cart and subscription:
        sub_length = included_outfits(subscription)
        if len(cart) > sub_length:
            # The cheapest items beyond the subscription allowance are charged
            extra = len(cart) - sub_length
            for item in Outfit.select().where(Outfit.id.in_(cart)).order_by(Outfit.outfit_price.asc()):
                if len(surplus) >= extra:
                    break
                amount += item.outfit_price
                surplus.append(item.id)
            if surplus:
                discount = float(amount) / len(surplus) * MULTI_ITEM_DISCOUNT * (len(surplus) - 1)
        sub = [s for s in cart if s not in surplus]
    elif cart:
        prices = {o.id: o.outfit_price for o in Outfit.select().where(Outfit.id.in_(cart))}
        for count, s in enumerate(cart):
            item = prices.get(s, 0)
            amount += item
            if count > 0:
                discount += float(item) * MULTI_ITEM_DISCOUNT

    amount = float(amount)
    price = round(amount - discount, 2) if amount > 0 else 0

    return {
        'sess': cart,
        'subscription': subscription,
        'subtype': included_outfits(subscription) if subscription else 0,
        'amount': amount,
        'discount': discount,
        'price': price,
        'surplus': surplus,
        'sub': sub,
    }


def in_stock(outfit_id, size):
    if size not in SIZES:
        return False
    stock = Size.get_or_none(Size.outfit == outfit_id)
    return stock is not None and getattr(stock, size) > 0


def cart_problems():
    """Return a list of messages for cart items that can no longer be ordered."""
    cart, sizes = get_cart()
    problems = []
    for outfit_id, size in zip(cart, sizes):
        if not in_stock(outfit_id, size):
            outfit = Outfit.get_or_none(Outfit.id == outfit_id)
            name = outfit.outfit_name if outfit else outfit_id
            problems.append(f'{name} ({size.replace("size_", "").upper()}) is niet meer op voorraad.')
    return problems


def open_order(user):
    return Order.get_or_none((Order.user == user.id) & (Order.is_open == True))


def place_order(user):
    """Create the order for the current cart and take the items out of stock."""
    cart, sizes = get_cart()
    with db.atomic():
        order = Order.create(order_customer_id=randrange(10), user=user.id,
                             order_date=datetime.date.today(), status='preparation', is_open=True)
        for outfit_id, size in zip(cart, sizes):
            Order_Outfit.create(order=order.id, outfit=outfit_id, size=size)
            field = getattr(Size, size)
            Size.update({field: field - 1}).where(Size.outfit == outfit_id).execute()

        for outfit_id in cart:
            stock = Size.get_or_none(Size.outfit == outfit_id)
            if stock and sum(getattr(stock, s) for s in SIZES) < 1:
                Outfit.update(in_stock=False).where(Outfit.id == outfit_id).execute()

    clear_cart()
    return order
