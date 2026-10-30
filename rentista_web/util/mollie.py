"""Small Mollie REST client for Rentista.

Talks to the Mollie v2 API directly with `requests`, so no extra SDK is needed.
Set MOLLIE_API_KEY to a `test_...` key while testing and a `live_...` key in
production.
"""
import os
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import urlparse

import requests

API_BASE = "https://api.mollie.com/v2"
CURRENCY = "EUR"
TIMEOUT = 15


class MollieError(Exception):
    def __init__(self, status, detail):
        super().__init__("Mollie API error %s: %s" % (status, detail))
        self.status = status
        self.detail = detail


# ---------------------------------------------------------------- helpers

def to_decimal(value):
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def money(value):
    """Mollie amount object, e.g. {"currency": "EUR", "value": "93.00"}."""
    return {"currency": CURRENCY, "value": "%.2f" % to_decimal(value)}


def vat_rate():
    return to_decimal(os.getenv("MOLLIE_VAT_RATE", "21"))


def vat_amount(total, rate):
    """VAT included in a gross amount."""
    total = to_decimal(total)
    return to_decimal(total * rate / (Decimal("100") + rate))


def build_order_lines(items, discount, rate=None):
    """Order lines for Klarna, Riverty and in3.

    items: list of (description, price) for every outfit that is charged.
    discount: total discount for the order (positive number).
    The sum of all line totals always equals the amount that is charged.
    """
    rate = vat_rate() if rate is None else to_decimal(rate)
    lines = []
    for description, price in items:
        price = to_decimal(price)
        lines.append({
            "type": "physical",
            "description": description[:255],
            "quantity": 1,
            "unitPrice": money(price),
            "totalAmount": money(price),
            "vatRate": "%.2f" % rate,
            "vatAmount": money(vat_amount(price, rate)),
        })
    discount = to_decimal(discount)
    if discount > 0:
        lines.append({
            "type": "discount",
            "description": "Korting",
            "quantity": 1,
            "unitPrice": money(-discount),
            "totalAmount": money(-discount),
            "vatRate": "%.2f" % rate,
            "vatAmount": money(-vat_amount(discount, rate)),
        })
    return lines


COUNTRY_CODES = {
    "nederland": "NL", "netherlands": "NL", "holland": "NL", "the netherlands": "NL",
    "belgie": "BE", "belgië": "BE", "belgium": "BE",
    "duitsland": "DE", "germany": "DE", "deutschland": "DE",
    "oostenrijk": "AT", "austria": "AT", "österreich": "AT",
}


def country_code(country):
    value = (country or "").strip()
    if len(value) == 2 and value.isalpha():
        return value.upper()
    return COUNTRY_CODES.get(value.lower(), "NL")


def split_name(full_name):
    parts = (full_name or "").strip().split(None, 1)
    if not parts:
        return "Klant", "Rentista"
    if len(parts) == 1:
        return parts[0], parts[0]
    return parts[0], parts[1]


def build_address(name, email, street, housenumber, postal, city, country, phone=None):
    given, family = split_name(name)
    address = {
        "givenName": given,
        "familyName": family,
        "email": email,
        "streetAndNumber": ("%s %s" % (street or "", housenumber or "")).strip(),
        "postalCode": (postal or "").strip(),
        "city": (city or "").strip(),
        "country": country_code(country),
    }
    phone = (phone or "").replace(" ", "")
    if phone.startswith("+"):
        address["phone"] = phone
    return address


def webhook_url(base_url, path):
    """Mollie cannot reach localhost, so skip the webhook during local testing."""
    host = urlparse(base_url).hostname or ""
    if host in ("localhost", "127.0.0.1", "0.0.0.0") or host.endswith(".local"):
        return None
    return base_url.rstrip("/") + path


def checkout_url(payment):
    return payment["_links"]["checkout"]["href"]


# ---------------------------------------------------------------- API calls

def _request(method, path, payload=None):
    api_key = os.getenv("MOLLIE_API_KEY")
    if not api_key:
        raise MollieError(0, "MOLLIE_API_KEY is not set")
    response = requests.request(
        method,
        API_BASE + path,
        json=payload,
        headers={"Authorization": "Bearer " + api_key},
        timeout=TIMEOUT,
    )
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise MollieError(response.status_code, detail)
    if response.status_code == 204 or not response.content:
        return {}
    return response.json()


def create_payment(amount, description, redirect_url, webhook=None, metadata=None,
                   lines=None, billing_address=None, shipping_address=None,
                   customer_id=None, sequence_type=None):
    payload = {
        "amount": money(amount),
        "description": description,
        "redirectUrl": redirect_url,
        "locale": "nl_NL",
    }
    if webhook:
        payload["webhookUrl"] = webhook
    if metadata:
        payload["metadata"] = metadata
    if lines:
        payload["lines"] = lines
    if billing_address:
        payload["billingAddress"] = billing_address
    if shipping_address:
        payload["shippingAddress"] = shipping_address
    if customer_id:
        payload["customerId"] = customer_id
    if sequence_type:
        payload["sequenceType"] = sequence_type
    return _request("POST", "/payments", payload)


def get_payment(payment_id):
    return _request("GET", "/payments/%s" % payment_id)


def capture_payment(payment_id):
    """Capture an authorized Klarna/Riverty payment so it gets paid out."""
    return _request("POST", "/payments/%s/captures" % payment_id, {})


def create_customer(name, email):
    return _request("POST", "/customers", {"name": name, "email": email})


def create_subscription(customer_id, amount, interval, start_date, description,
                        webhook=None, metadata=None):
    payload = {
        "amount": money(amount),
        "interval": interval,
        "startDate": start_date.isoformat(),
        "description": description,
    }
    if webhook:
        payload["webhookUrl"] = webhook
    if metadata:
        payload["metadata"] = metadata
    return _request("POST", "/customers/%s/subscriptions" % customer_id, payload)


def cancel_subscription(customer_id, subscription_id):
    return _request("DELETE", "/customers/%s/subscriptions/%s" % (customer_id, subscription_id))
