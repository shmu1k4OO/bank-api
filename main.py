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

TRANSACTION_HISTORY_HEADER = [
    "timestamp,type,from_card,to_card,amount,mcc,cashback,description"
]
CB_DEBIT_PAY_DESCRIPTION = "{amount:.2f}₽ (MCC: {mcc}) с карты #{card_id} (кешбэк {cashback_amount:.2f}₽)"
SAVING_INTEREST_DESCRIPTION = "Начислены проценты {interest:.2f}₽ по накопительной карте #{card_id}"
DEPOSIT_DESCRIPTION = "{amount:.2f}₽ → карта #{card_id}"
TRANSFER_DESCRIPTION = "{amount:.2f}₽: карта #{from_card} → карта #{to_card}"
PAY_DESCRIPTION = "{amount:.2f}₽ (MCC: {mcc}) с карты #{card_id}"
BALANCE_DECRIPTION = "Баланс: {balance:.2f}₽"

DEBIT_DEFAULT_CASHBACK_RATE = 0.03
SAVING_CARD_DEFAULT_INTEREST = 0.015
DEFAULT_ACCOUNT_BALANCE = 0.00
DEFAULT_CASHBACK_BALANCE = 0.00
DEFAULT_CASHBACK_TRANSACTION = 0.00
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

TIMESTAMP_START = _dt.datetime(2022, 1, 1, 9, 0, 0)


def timestamp_generator():
    for i in _it.count():
        base_date = TIMESTAMP_START + _dt.timedelta(days=i)
        hour = 9 + (i * 3) % 10        # цикличное смещение часа
        minute = (i * 7) % 60          # цикличное смещение минут
        second = (i * 11) % 60         # цикличное смещение секунд
        yield base_date.replace(hour=hour % 24, minute=minute, second=second)


TIMESTAMP_GENERATOR = timestamp_generator()


def next_timestamp_after(issue_date: _dt.date) -> _dt.datetime:
    
    while True:
        ts = next(TIMESTAMP_GENERATOR)
        if ts.date() > issue_date:
            return ts


# =============================== ENUM'Ы ===============================
class CardStatus(Enum):
    ACTIVE = "Active"
    CLOSED = "Closed"
    BLOCKED = "Blocked"


CARD_STATUS = CardStatus.ACTIVE


class TransactionType(Enum):
    DEPOSIT = "deposit"
    TRANSFER = "transfer"
    PAY = "pay"
    INTEREST = "interest"


@dataclass
class User:
    last_name: str
    first_name: str
    phone: str
    pin: str
    user_id: int

    accounts: list = field(default_factory=list)
    cards: list = field(default_factory=list)

    def change_pin(self, old_pin, new_pin):
        if self.pin == old_pin:
            self.pin = new_pin 


@dataclass
class Account:
    owner: "User"
    acc_id: str
    balance: float = DEFAULT_ACCOUNT_BALANCE
    cashback_balance: float = DEFAULT_CASHBACK_BALANCE


class Card:
    def __init__(
            self,
            account,
            bank,
            card_id,
            payment_system,
            pan,
            issue_date,
            expiry_date,
            status=CARD_STATUS,
            card_currency=CARD_CURRENCY,
            bank_name=None,
            bank_bic=None,
            **kwargs

    ):  
        self.account = account
        self.bank = bank
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
            "cashback_balance": f"Кешбэк:        {self.account.cashback_balance:.2f}₽",
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
    
    def get_balance(self):
        return f"Баланс: {self.account.balance:.2f}₽"

    def close(self):
        self.status = CardStatus.CLOSED

    def deposit(self, amount):
        self.account.balance += amount
        timestamp = next_timestamp_after(self.issue_date)
        description = DEPOSIT_DESCRIPTION.format(amount=amount, card_id=self.card_id)
        transaction = Transaction(
            None,
            self.card_id,
            amount,
            DEFAULT_CASHBACK_BALANCE, 
            TransactionType.DEPOSIT.value,
            None,
            description,
            timestamp  
        )
        self.bank.transaction_log.append(transaction)

    def transfer(self, to_card, amount):
        latest_issue = max(self.issue_date, to_card.issue_date)
        timestamp = next_timestamp_after(latest_issue)

        if self.account.balance >= amount:
            if to_card in self.bank.cards:
                self.account.balance -= amount
                to_card.account.balance += amount
                description = TRANSFER_DESCRIPTION.format(
                    amount=amount,
                    from_card=self.card_id, 
                    to_card=to_card.card_id
                )
                transaction = Transaction(
                    self.card_id,
                    to_card.card_id, 
                    amount, 
                    DEFAULT_CASHBACK_BALANCE,
                    TransactionType.TRANSFER.value, 
                    None, 
                    description, 
                    timestamp      
                )
                self.bank.transaction_log.append(transaction)

    def pay(self, amount, mcc):
        if self.account.balance >= amount:
            self.account.balance -= amount
            timestamp = next_timestamp_after(self.issue_date)
            description = PAY_DESCRIPTION.format(amount=amount, mcc=mcc, card_id=self.card_id)
            transaction = Transaction(
                self.card_id, 
                None, 
                amount,
                DEFAULT_CASHBACK_BALANCE, 
                TransactionType.PAY.value, 
                mcc, 
                description, 
                timestamp
            )
            self.bank.transaction_log.append(transaction)
    
    def get_transaction_history(self):
        card_transaction_history = [TRANSACTION_HISTORY_HEADER[0]]
        sorted_transaction = sorted(self.bank.transaction_log, key=lambda t: t.timestamp)
        for transaction in sorted_transaction:
            if self.card_id == transaction.from_card or self.card_id == transaction.to_card:
                if transaction.type == TransactionType.DEPOSIT.value:
                    sign = "+"
                elif transaction.type == TransactionType.PAY.value:
                    sign = "-"
                else:
                    if self.card_id == transaction.from_card:
                        sign = "-"
                    else:
                        sign = "+"

                card_transaction_history.append(
                    f"{transaction.timestamp},{transaction.type},"
                    f"{transaction.from_card or ''},{transaction.to_card or ''},"
                    f"{sign}{transaction.amount:.2f}₽,{transaction.mcc or ''},"
                    f"{transaction.cashback:.2f}₽,{transaction.description}"
                )
        return card_transaction_history

   
@dataclass
class Transaction:
    from_card: int | None
    to_card: int | None
    amount: float
    cashback: float
    type: str
    mcc: str | None
    description: str
    timestamp: _dt.datetime


@dataclass
class Bank:

    name: str
    bic: str
    customers: list = field(default_factory=list)
    accounts: list = field(default_factory=list)
    cards: list = field(default_factory=list)
    transaction_log: list = field(default_factory=list)

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
        
        card = card_class(
            acc,
            self, 
            next(self._card_seq),
            payment_system, 
            pan, 
            issue_date=None, 
            expiry_date=None, 
            status=CARD_STATUS, 
            card_currency=CARD_CURRENCY, 
            bank_name=self.name,
            bank_bic=self.bic,
            **kwargs    
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
                        cards=[card])
        
            self.customers.append(user)
            self.accounts.append(account)
            self.cards.append(card)

        else:
            for user in self.customers:
                if user.phone == phone and user.last_name == last_name and user.first_name == first_name:
                    user.accounts.append(account)
                    user.cards.append(card)
                    break

        acc.owner = user
        return card
    
    def get_global_history(self):
        bank_transaction_histoty = [TRANSACTION_HISTORY_HEADER[0]]
        sorted_transaction = sorted(self.transaction_log, key=lambda t: t.timestamp)
        for transaction in sorted_transaction:
            bank_transaction_histoty.append(
                f"{transaction.timestamp},{transaction.type},"
                f"{transaction.from_card or ''},{transaction.to_card or ''},"
                f"{transaction.amount:.2f}₽,{transaction.mcc or ''},"
                f"{transaction.cashback:.2f}₽,{transaction.description}"
            )
        return bank_transaction_histoty
    
    def issue_simple_debit_card(
            self, last_name, first_name, pin, phone, payment_system, **kwargs
    ):
        
        return self.apply_for_card(
            last_name,
            first_name,
            pin,
            phone,
            payment_system,
            card_class=SimpleDebitCard,
            **kwargs
        )
    
    def issue_cashback_debit_card(
            self, last_name, first_name, pin, phone, payment_system, **kwargs
    ):
        
        return self.apply_for_card(
            last_name,
            first_name,
            pin,
            phone,
            payment_system,
            card_class=CashbackDebitCard,
            **kwargs
        )
    
    def issue_saving_card(
            self, last_name, first_name, pin, phone, payment_system, **kwargs
    ):
        
        return self.apply_for_card(
            last_name,
            first_name,
            pin,
            phone,
            payment_system,
            card_class=SavingCard,
            **kwargs
        )


class SimpleDebitCard(Card):
    pass


class CashbackDebitCard(Card):
    def __init__(
            self,
            account,
            bank,
            card_id,
            payment_system,
            pan,
            issue_date,
            expiry_date,
            status=CARD_STATUS,
            card_currency=CARD_CURRENCY,
            bank_name=None,
            bank_bic=None,
            cashback_rate=DEBIT_DEFAULT_CASHBACK_RATE,
            **kwargs

    ):
        super().__init__(
            account,
            bank,
            card_id,
            payment_system,
            pan,
            issue_date,
            expiry_date,
            status,
            card_currency,
            bank_name,
            bank_bic,
            **kwargs
        )
        self.cashback_rate = cashback_rate

    def pay(self, amount, mcc):
        if self.account.balance >= amount:
            self.account.balance -= amount
            timestamp = next_timestamp_after(self.issue_date)
            cashback_amount = round((amount * self.cashback_rate), 2)
            self.account.cashback_balance += cashback_amount
            description = CB_DEBIT_PAY_DESCRIPTION.format(
                amount=amount, 
                mcc=mcc, 
                card_id=self.card_id, 
                cashback_amount=cashback_amount
            )
            transaction = Transaction(
                self.card_id,
                None, 
                amount,
                cashback_amount, 
                TransactionType.PAY.value, 
                mcc, 
                description,
                timestamp
            )
            self.bank.transaction_log.append(transaction)


class SavingCard(Card):
    def __init__(
            self,
            account,
            bank,
            card_id,
            payment_system,
            pan,
            issue_date,
            expiry_date,
            status=CARD_STATUS,
            card_currency=CARD_CURRENCY,
            bank_name=None,
            bank_bic=None,
            interest_rate=SAVING_CARD_DEFAULT_INTEREST,
            **kwargs

    ):
        super().__init__(
            account,
            bank,
            card_id,
            payment_system,
            pan,
            issue_date,
            expiry_date,
            status,
            card_currency,
            bank_name,
            bank_bic,
            **kwargs
        )
        self.interest_rate = interest_rate
    
    def accrue_interest(self):
        interest = round((self.account.balance * self.interest_rate), 2)
        self.account.balance += interest
        description = SAVING_INTEREST_DESCRIPTION.format(interest=interest, card_id=self.card_id)
        timestamp = next_timestamp_after(self.issue_date)
        transaction = Transaction(
            None, 
            self.card_id, 
            interest,
            DEFAULT_CASHBACK_BALANCE, 
            TransactionType.INTEREST.value, 
            None, 
            description, 
            timestamp
        )
        self.bank.transaction_log.append(transaction)

bank = Bank("Demo Bank", "044452345")
c_base = bank.issue_saving_card("Кузнецов", "Кирилл", "3333", "+70000000004", "MIR")
c_custom = bank.issue_saving_card("Кузнецов", "Кирилл", "3333", "+70000000005", "MIR", interest_rate=0.03)
c_recv = bank.issue_saving_card("Сидоров", "Сергей", "4444", "+70000000006", "MIR")

c_base.deposit(1000)
c_custom.deposit(1000)
c_recv.deposit(500)

c_base.pay(200, '5411')
c_custom.pay(200, '5814')

c_base.accrue_interest()
c_custom.accrue_interest()

c_base.transfer(c_recv, 150)
c_custom.transfer(c_recv, 120)

print(c_base.get_balance())
print(c_custom.get_balance())
print(c_recv.get_balance())

for row in c_base.get_transaction_history(): print(row)
for row in c_custom.get_transaction_history(): print(row)
for row in c_recv.get_transaction_history(): print(row)