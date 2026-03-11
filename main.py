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
class Bank:

    name: str
    bic: str

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
        
        return (10 - sum(digits) % 10) % 10