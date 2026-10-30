"""Server-side price calculation for the cart.

Mirrors the calculation on the outfits pages, so the customer pays exactly what
the cart shows. The price is never taken from the URL or the browser.
"""
from decimal import Decimal

SUBSCRIPTION_PLANS = {
    # number of outfits per time: monthly price in euro
    3: Decimal("93"),
    4: Decimal("109"),
    5: Decimal("125"),
}
PLAN_BY_PRICE = {int(price): outfits for outfits, price in SUBSCRIPTION_PLANS.items()}

MULTI_ITEM_DISCOUNT = Decimal("0.33")


def subscription_outfits(subscription):
    """Number of outfits an active subscription covers, or None."""
    if subscription is None:
        return None
    try:
        return int(subscription.subscription_type)
    except (TypeError, ValueError):
        return None


def calculate_cart(cart_outfits, covered_by_subscription=None):
    """Work out what has to be paid for the cart.

    cart_outfits: outfits in the cart, in cart order. Each needs `.id`,
        `.outfit_name`, `.brand_name` and `.outfit_price`.
    covered_by_subscription: number of outfits the customer's active
        subscription covers, or None without a subscription.

    Returns dict with `charged` (outfits to pay for), `amount` (before
    discount), `discount` and `price` (to pay), all Decimals.
    """
    amount = Decimal("0")
    discount = Decimal("0")
    charged = []

    if covered_by_subscription is not None:
        extra = len(cart_outfits) - covered_by_subscription
        if extra > 0:
            # The cheapest outfits beyond the subscription are charged.
            cheapest_first = sorted(cart_outfits, key=lambda o: Decimal(str(o.outfit_price)))
            charged = cheapest_first[:extra]
            amount = sum((Decimal(str(o.outfit_price)) for o in charged), Decimal("0"))
            count = len(charged)
            discount = amount / count * MULTI_ITEM_DISCOUNT * (count - 1)
    else:
        charged = list(cart_outfits)
        for index, outfit in enumerate(charged):
            price = Decimal(str(outfit.outfit_price))
            amount += price
            if index > 0:
                discount += price * MULTI_ITEM_DISCOUNT

    amount = amount.quantize(Decimal("0.01"))
    discount = discount.quantize(Decimal("0.01"))
    return {
        "charged": charged,
        "amount": amount,
        "discount": discount,
        "price": amount - discount,
    }
