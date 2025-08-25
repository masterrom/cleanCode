# checkout.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Protocol, Optional


# Meaning full names, instead of using p,c,f,st,addr,cc
# using checkout/cart, checkout/address, checkout/credit_card
# Smaller and single function helpers _subtotal, _apply_discount, _log
# using exceptions for error handling
# Code is easy to read through without comments, contains meaningfull names and order
# using objects for cart, address, credit_card
# using protocols for payment processing and shipping, and interfacing
# vertical/horizontal separation of concerns

# ----- Value Objects / DTOs -----

@dataclass(frozen=True)
class Money:
    amount: float

    def plus(self, other: "Money") -> "Money":
        return Money(self.amount + other.amount)

    def minus(self, other: "Money") -> "Money":
        return Money(self.amount - other.amount)

    def times(self, factor: float) -> "Money":
        return Money(self.amount * factor)


@dataclass(frozen=True)
class Address:
    street: str
    city: str
    state: str
    zip: str

    def __post_init__(self):
        if not self.zip or len(self.zip) < 5:
            raise ValueError("Invalid ZIP")


@dataclass(frozen=True)
class LineItem:
    sku: str
    unit_price: Money
    quantity: int

    def extended(self) -> Money:
        return self.unit_price.times(self.quantity)


@dataclass(frozen=True)
class Cart:
    items: tuple[LineItem, ...]
    discount_rate: Optional[float] = None  # e.g., 0.10 for 10%


@dataclass(frozen=True)
class Receipt:
    total: Money
    shipping_label: str


# ----- Shipping (Strategy) -----

class ShippingOption(Protocol):
    def label(self, to: Address) -> str: ...
    def surcharge(self) -> Money: ...


class StandardShipping:
    def label(self, to: Address) -> str:
        return f"STD-{to.zip}"

    def surcharge(self) -> Money:
        return Money(0.00)


class ExpressShipping:
    def label(self, to: Address) -> str:
        return f"EXP-{to.zip}"

    def surcharge(self) -> Money:
        return Money(9.99)


# ----- Payment -----

class PaymentDeclined(Exception):
    pass


class PaymentProcessor(Protocol):
    def charge(self, card_number: str, amount: Money) -> None: ...


class SimpleCardProcessor:
    def charge(self, card_number: str, amount: Money) -> None:
        if not card_number or len(card_number) < 12:
            raise PaymentDeclined("Invalid card")
        if not (card_number.startswith("4") or card_number.startswith("5")):
            raise PaymentDeclined("Unsupported card")
        # pretend to succeed


# ----- Tax Policy -----

class TaxPolicy(Protocol):
    def apply(self, pre_tax: Money) -> Money: ...


class NewYorkTax:
    RATE = 0.08875

    def apply(self, pre_tax: Money) -> Money:
        return pre_tax.times(1 + self.RATE)


# ----- Orchestrator -----

class CheckoutService:
    def __init__(self, payments: PaymentProcessor, tax_policy: TaxPolicy):
        self._payments = payments
        self._tax = tax_policy

    def checkout(
        self,
        user_id: str,
        cart: Cart,
        shipping: ShippingOption,
        ship_to: Address,
        card_number: str,
    ) -> Receipt:
        subtotal = self._subtotal(cart.items)
        discounted = self._apply_discount(subtotal, cart.discount_rate)
        with_shipping = discounted.plus(shipping.surcharge())
        total = self._tax.apply(with_shipping)

        self._payments.charge(card_number, total)
        label = shipping.label(ship_to)

        self._log(user_id, total, label)
        return Receipt(total=total, shipping_label=label)

    # --- helpers (one level of abstraction each) ---

    def _subtotal(self, items: Iterable[LineItem]) -> Money:
        total = Money(0.0)
        for li in items:
            total = total.plus(li.extended())
        return total

    def _apply_discount(self, amount: Money, rate: Optional[float]) -> Money:
        if not rate or rate <= 0:
            return amount
        return amount.minus(amount.times(rate))

    def _log(self, user_id: str, total: Money, label: str) -> None:
        print(f"USER={user_id} TOTAL={total.amount:.2f} LABEL={label}")


# ----- Example usage -----
if __name__ == "__main__":
    cart = Cart(
        items=(
            LineItem("SKU-1", Money(12.50), 2),
            LineItem("SKU-2", Money(5.00), 3),
        ),
        discount_rate=0.10,
    )
    ship_to = Address("123 Main St", "NYC", "NY", "10001")
    service = CheckoutService(SimpleCardProcessor(), NewYorkTax())

    receipt = service.checkout(
        user_id="u-123",
        cart=cart,
        shipping=ExpressShipping(),
        ship_to=ship_to,
        card_number="4111111111111111",
    )
    print("TOTAL DUE:", receipt.total.amount, "| LABEL:", receipt.shipping_label)
