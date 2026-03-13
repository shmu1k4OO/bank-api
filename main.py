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
ISSUE_DATE_START = _dt.date(2026, 1, 1)
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

        if self.issue_date is None:
            self.issue_date = next(ISSUE_DATE_GENERATOR)
        if self.expiry_date is None and self.issue_date is not None:
            self.expiry_date = _dt.date(
                self.issue_date.year + EXPIRY_YEARS,
                self.issue_date.month,
                self.issue_date.day,
            )
        get_card_info(self,):


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
            candidate_account_number  = ACCOUNT_TYPE_CODE + ACCOUNT_CURRENCY + str(control_digit) + ACCOUNT_BRANCH + serial
            control_sum = 0

            for i in range(len(mask) - 1): # 23 элемента
                product = int((bic_tail + candidate_account_number)[i]) * mask[i]
                control_sum += product % 10
            
            if control_sum % 10 == 0:
                return candidate_account_number


    def _generate_pan(self, pay_system):

        bin_number = BIN_BY_SYSTEM.get(pay_system.upper(), BIN_BY_SYSTEM[DEFAULT_PAYMENT_SYSTEM])
        serial = f"{next(self._pan_seq):09d}"
        product = bin_number + serial

        return  product + str(self._luhn(product))


    def _luhn(self, digits15):

        digits = [int(d) for d in digits15[::-1]]
        for i in range(1, len(digits), 2):
            double_value_of_digit = digits[i] * 2
            if double_value_of_digit > 9:
                digits[i] = double_value_of_digit - 9
            else:
                digits[i] = double_value_of_digit
        
        return (10 - sum(digits) % 10) % 1
    
    def aplly_for_card(
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

        card = Card(account,
                    self._card_seq,
                    payment_system, 
                    pan, 
                    issue_date=None, 
                    expiry_date=None, 
                    status=CARD_STATUS, 
                    card_currency=CARD_CURRENCY, 
                    bank_name=self.name
                    )
        
        if phone not in [user.phone for user in self.customers] and last_name not in [user.last_name for user in self.customers] and first_name not in [user.first_name for user in self.customers]:
            
            user = User(last_name,
                        first_name,
                        phone, 
                        pin, 
                        next(self._user_seq), 
                        accounts=[account], 
                        cards=[card])
        
            self.customers.append(user)
            self.accounts.append(account)
            self.cards.append(card)

        else:
             for user in self.customers:
                if user.phone == phone or user.last_name == last_name or user.first_name == first_name:
                    user.accounts.append(account)
                    user.cards.append(card)
                    break

             self.accounts.append(account)
             self.cards.append(card)
                
        return card
    
