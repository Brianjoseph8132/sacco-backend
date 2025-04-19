from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData, ForeignKey
from datetime import datetime
from werkzeug.security import generate_password_hash

metadata = MetaData()
db = SQLAlchemy(metadata=metadata)

class Member(db.Model):
    __tablename__ = 'members'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    id_number = db.Column(db.String(20), unique=True)
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')
    is_admin = db.Column(db.Boolean, default=False)
    
    account = db.relationship('Account', backref='member', uselist=False, lazy=True)
    loans = db.relationship('Loan', backref='member', lazy=True)

    notifications_received = db.relationship('Notification', foreign_keys='Notification.recipient_id', backref='recipient', lazy=True)
    notifications_sent = db.relationship('Notification', foreign_keys='Notification.sender_id', backref='sender', lazy=True)


    def set_id_number(self,id_number):
        self.pin = generate_password_hash(id_number)

class Account(db.Model):
    __tablename__ = 'account'
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    balance = db.Column(db.Float, default=0.0, nullable=False)
    pin = db.Column(db.String(128), nullable=False)

    def set_pin(self, pin):
        self.pin = generate_password_hash(pin)

    def deposit(self, amount):
        if isinstance(amount, str):
            amount = float(amount)
        self.balance += amount
        transaction = Transaction(type="deposit", amount=amount, account_id=self.id)
        db.session.add(transaction)

    def withdraw(self, amount):
        if isinstance(amount, str):
            amount = float(amount)
        self.balance -= amount
        transaction = Transaction(type="withdraw", amount=amount, account_id=self.id)
        db.session.add(transaction)

    def __repr__(self):
        return f"<Account {self.id} - Balance: {self.balance}>"

class Transaction(db.Model):
    __tablename__ = 'transaction'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(10), nullable=False)  # 'deposit' or 'withdraw'
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)

    def __repr__(self):
        return f"<Transaction {self.id} - {self.type} {self.amount}>"

class Loan(db.Model):
    __tablename__ = 'loans'
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    interest_rate = db.Column(db.Numeric(5, 2), default=12.0)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    approval_date = db.Column(db.DateTime)
    due_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')  # pending/approved/rejected/paid
    guarantor_id = db.Column(db.Integer, db.ForeignKey('members.id'))
    approved_by = db.Column(db.Integer, db.ForeignKey('members.id'))

    repayments = db.relationship('LoanRepayment', backref='loan', lazy=True)

class LoanRepayment(db.Model):
    __tablename__ = 'loan_repayments'
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(50))

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(50))  # 'loan_request', 'loan_status_update', 'repayment_notice', etc.
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=True)

class TokenBlocklist(db.Model):
    __tablename__ = 'token_blocklist'
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False)
