import datetime as _dt
import itertools as _it
from dataclasses import dataclass, field
from enum import Enum


# =============================== КОНСТАНТЫ ===============================
DEFAULT_CARD_INFO_FIELDS = [
    "card_id",
    "user_id",
    "phone",
    "bank_name",
    "bank_bic",
    "acc_id",
    "pan",
    "payment_system",
    "currency",
    "status",
    "issue_date",
    "expiry_date",
    "balance",
    "cashback_balance",
    "user_cards",
]
DEFAULT_ACCOUNT_BALANCE = 0.00
DEFAULT_CASHBACK_BALANCE = 0.00
CARD_CURRENCY = "RUB"
DEFAULT_PAYMENT_SYSTEM = "MIR"

ACCOUNT_TYPE_CODE = "40817"  # тип счета для физлиц
ACCOUNT_BRANCH = "0000"  # отсутствие филиалов у банка
ACCOUNT_CURRENCY = "810"  # идентификатор для рублёвых операций


EMPTY_PAN = "0000000000000000"

BIN_BY_SYSTEM = {
    "MIR": "220400",
    "VISA": "400000",
    "MASTERCARD": "510000",
}


# =============================== ГЕНЕРАТОРЫ ДАННЫХ ===============================
ISSUE_DATE_START = _dt.date(2022, 1, 1)
ISSUE_DATE_GENERATOR = (ISSUE_DATE_START + _dt.timedelta(days=i) for i in _it.count())
EXPIRY_YEARS = 4


# =============================== ENUM'Ы ===============================
class CardStatus(Enum):
    ACTIVE = "Active"
    CLOSED = "Closed"
    BLOCKED = "Blocked"


CARD_STATUS = CardStatus.ACTIVE


@dataclass
class User:
    last_name: str
    first_name: str
    phone: str
    pin: str
    user_id: int

    accounts: list = field(default_factory=list)
    cards: list = field(default_factory=list)


@dataclass
class Account:
    owner: "User"
    acc_id: str
    balance: float = DEFAULT_ACCOUNT_BALANCE


class Card:
    def __init__(
            self,
            account,
            card_id,
            payment_system,
            pan,
            issue_date,
            expiry_date,
            status=CARD_STATUS,
            card_currency=CARD_CURRENCY,
            bank_name=None,
            bank_bic=None

    ):  
        self.account = account
        self.card_id = card_id
        self.payment_system = payment_system
        self.pan = pan
        self.issue_date = issue_date
        self.expiry_date = expiry_date
        self.status = status
        self.card_currency = card_currency
        self.bank_name = bank_name
        self.bank_bic = bank_bic

        if self.issue_date is None:
            self.issue_date = next(ISSUE_DATE_GENERATOR)
        if self.expiry_date is None and self.issue_date is not None:
            self.expiry_date = _dt.date(
                self.issue_date.year + EXPIRY_YEARS,
                self.issue_date.month,
                self.issue_date.day,
            )

    def get_card_info(self, fields: list = None):
            
        user = self.account.owner
        data = {
            "bank_name": f"Банк:          {self.bank_name}",
            "bank_bic": f"БИК банка:     {self.bank_bic}",
            "card_id": f"Карта #{self.card_id}",
            "user_id": f"Пользователь:  {user.user_id} — {user.last_name} {user.first_name}",
            "phone": f"Телефон:       {user.phone}",
            "pan": f"PAN:           {self.pan}",
            "acc_id": f"Счёт:          {self.account.acc_id}",
            "payment_system": f"Плат. система: {self.payment_system}",
            "currency": f"Валюта:        {self.card_currency}",
            "status": f"Статус:        {self.status.value}",
            "issue_date": f"Выпуск:        {self.issue_date}",
            "expiry_date": f"Срок:          {self.expiry_date}",
            "user_cards": f"Карты пользователя: {user.cards}",
            "cashback_balance": f"Кешбэк:        {DEFAULT_CASHBACK_BALANCE:.2f}₽",
            "balance": f"Баланс:        {self.account.balance:.2f}₽",
        }

        if fields is None:
            fields = DEFAULT_CARD_INFO_FIELDS
        return (
            "\n".join([data[field] for field in fields if field in data])
            + "\n"
            + "-" * 50
        )

    def __repr__(self):
        return (
            f"Card(card_id={self.card_id}, pan={self.pan}, account={self.account}, "
            f"status={self.status}, issue_date={self.issue_date}, expiry_date={self.expiry_date})"
        )


@dataclass
class Bank:

    name: str
    bic: str
    customers: list = field(default_factory=list)
    accounts: list = field(default_factory=list)
    cards: list = field(default_factory=list)

    _user_seq: any = field(default_factory=lambda: _it.count(1), init=False)
    _account_seq: any = field(default_factory=lambda: _it.count(1), init=False)
    _card_seq: any = field(default_factory=lambda: _it.count(1), init=False)
    _pan_seq: any = field(default_factory=lambda: _it.count(1), init=False)

    def _next_account_number(self):
         
        mask = [7, 1, 3] * 8

        serial = f"{next(self._account_seq):07d}"

        bic_tail = self.bic[-3:]

        for control_digit in range(10):
            candidate_account_number = (ACCOUNT_TYPE_CODE + ACCOUNT_CURRENCY + str(control_digit) + ACCOUNT_BRANCH + 
                                        serial)
            control_sum = 0

            for i in range(len(mask) - 1):  # 23 элемента
                product = int((bic_tail + candidate_account_number)[i]) * mask[i]
                control_sum += product % 10
            
            if control_sum % 10 == 0:
                return candidate_account_number

    def _generate_pan(self, pay_system):

        bin_number = BIN_BY_SYSTEM.get(pay_system.upper(), BIN_BY_SYSTEM[DEFAULT_PAYMENT_SYSTEM])
        serial = f"{next(self._pan_seq):09d}"
        product = bin_number + serial

        return product + str(self._luhn(product))

    def _luhn(self, digits15):

        digits = [int(d) for d in digits15[::-1]]
        for i in range(1, len(digits), 2):
            double_value_of_digit = digits[i] * 2
            if double_value_of_digit > 9:
                digits[i] = double_value_of_digit - 9
            else:
                digits[i] = double_value_of_digit
        
        return (10 - sum(digits) % 10) % 10
    
    def apply_for_card(
            self,
            last_name,
            first_name,
            pin,
            phone,
            payment_system=DEFAULT_PAYMENT_SYSTEM,
            card_class: type = Card,
            **kwargs,
    ):  
        pan = self._generate_pan(payment_system)

        account = self._next_account_number()

        acc = Account(None, account, DEFAULT_ACCOUNT_BALANCE)
        
        card = Card(acc,
                    next(self._card_seq),
                    payment_system, 
                    pan, 
                    issue_date=None, 
                    expiry_date=None, 
                    status=CARD_STATUS, 
                    card_currency=CARD_CURRENCY, 
                    bank_name=self.name,
                    bank_bic=self.bic    
                    )

        if (
            phone not in [user.phone for user in self.customers] 
            or last_name not in [user.last_name for user in self.customers] 
            or first_name not in [user.first_name for user in self.customers]
        ): 
            user = User(last_name,
                        first_name,
                        phone, 
                        pin, 
                        next(self._user_seq), 
                        accounts=[account], 
                        cards=[pan])
        
            self.customers.append(user)
            self.accounts.append(account)
            self.cards.append(pan)

        else:
            for user in self.customers:
                if user.phone == phone and user.last_name == last_name and user.first_name == first_name:
                    user.accounts.append(account)
                    user.cards.append(pan)
                    break

            #  self.accounts.append(account)
            #  self.cards.append(card)

        acc.owner = user

        return card
    
bank = Bank("Demo Bank", "044452345")

card_data = [
  ("Иванов", "Иван", "1234", "+79161234501", "MIR"),
  ("Петров", "Пётр", "5678", "+79161234502", "VISA"),
  ("Сидоров", "Сидор", "0000", "+79161234503", "MASTERCARD"),
  ("Кузнецов", "Кузьма", "9999", "+79161234504", "VISA"),
  ("Смирнов", "Сергей", "1111", "+79161234505", "MIR"),
  ("Смирнов", "Сергей", "1111", "+79161234505", "VISA"),
  ("Захаров", "Кирилл", "1212", "+79161234507", "MASTERCARD")
]

cards = []
print("Список всех выпущенных карт:\n")
for last_name, first_name, pin, phone, system in card_data:
  card = bank.apply_for_card(last_name, first_name, pin, phone, system)
  print(card.get_card_info())
  cards.append(card)