from sqlmodel import SQLModel, Field, Relationship
from database.model import Order, RetiradaProduto
from typing import List, Optional
import re 

EMAIL_REGEX = r"[A-Za-z0-9._%+-]+@(gmail|hotmail)\.[a-zA-Z]{1,3}"

class SalePoint:
    def __init__(self):
        self._id: int | None = None
        self._name: str | None = None
        self._email: str | None = None
        self._password_hash: str | None = None
        self._level: int | None = None
        self._orders: list[Order] = []
        self._outbounds: list[RetiradaProduto] = []


    @property
    def id(self) -> int | None:
        return self._id

    @property
    def name(self) -> str | None:
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        self._name = name.strip().upper()

    @property
    def email(self) -> str | None:
        return self._email

    @email.setter
    def email(self, email: str | None) -> None:
        trated_email = email.strip().lower() if email else None
        
        if trated_email and not re.fullmatch(EMAIL_REGEX, trated_email):
            raise ValueError("Invalid email format")

        self._email = trated_email

    @property
    def password_hash(self) -> str | None:
        return self._password_hash

    @password_hash.setter
    def password_hash(self, password_hash: str) -> None:
        trated_password_hash = password_hash.strip()

        if not trated_password_hash:
            raise ValueError("Password cannot be empty")

        self._password_hash = trated_password_hash

    @property
    def level(self) -> int | None:
        return self._level  

    @level.setter
    def level(self, level: int) -> None:
        if level not in (0, 1):    
            raise ValueError("Level must be either 0 or 1")
        self._level = level

    @property
    def orders(self) -> list[Order]:
        return self._orders.copy()

    @property
    def outbounds(self) -> list[RetiradaProduto]:
        return self._outbounds.copy()

    def add_order(self, order: Order) -> None:
        if order not in self._orders:
            self._orders.append(order)

    def add_outbound(self, outbound: RetiradaProduto) -> None:
        if outbound not in self._outbounds:
            self._outbounds.append(outbound)

    def remove_order(self, order: Order) -> None:
        if order in self._orders:
            self._orders.remove(order)

    def remove_all_orders(self) -> None:
        self._orders.clear()

    def remove_all_outbounds(self) -> None:
        self._outbounds.clear()

    def remove_outbound(self, outbound: RetiradaProduto) -> None:
        if outbound in self._outbounds:
            self._outbounds.remove(outbound)

    def get_order_by_id(self, order_id: int) -> Optional[Order]:
        for order in self._orders:
            if order.id == order_id:
                return order
        return None

    def get_outbound_by_id(self, outbound_id: int) -> Optional[RetiradaProduto]:
        for outbound in self._outbounds:
            if outbound.id == outbound_id:
                return outbound
        return None