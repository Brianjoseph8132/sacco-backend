from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData, ForeignKey
from datetime import datetime

metadata = MetaData()
db = SQLAlchemy(metadata=metadata)

class Member(db.Model):
    __tablename__ = "member"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    savings = db.Column(db.Float, default=0.0)
    is_approved = db.Column(db.Boolean, default=False)  # Admin approval

    # Relationships
    transactions = db.relationship('Transaction', backref='member', lazy=True, cascade="all, delete-orphan")
    loans = db.relationship('Loan', backref='member', lazy=True, cascade="all, delete-orphan")
    contributions = db.relationship('Contribution', backref='member', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        """Convert object to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "savings": self.savings,
            "is_approved": self.is_approved
        }


class Transaction(db.Model):
    __tablename__ = "transaction"

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, ForeignKey('member.id', ondelete="CASCADE"), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # "deposit" or "withdraw"
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "member_id": self.member_id,
            "transaction_type": self.transaction_type,
            "amount": self.amount,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }


class Loan(db.Model):
    __tablename__ = "loan"

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, ForeignKey('member.id', ondelete="CASCADE"), nullable=False)
    admin_id = db.Column(db.Integer, ForeignKey('member.id'), nullable=True)  # Admin who approved/rejected
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="pending")  # "pending", "approved", "rejected"
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to track which admin approved/rejected the loan
    admin = db.relationship("Member", foreign_keys=[admin_id])

    repayments = db.relationship('Repayment', backref='loan', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "member_id": self.member_id,
            "admin_id": self.admin_id,
            "amount": self.amount,
            "status": self.status,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }


class Contribution(db.Model):
    __tablename__ = "contribution"

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, ForeignKey('member.id', ondelete="CASCADE"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "member_id": self.member_id,
            "amount": self.amount,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }


class Repayment(db.Model):
    __tablename__ = "repayment"

    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, ForeignKey('loan.id', ondelete="CASCADE"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "loan_id": self.loan_id,
            "amount": self.amount,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }



# 
class TokenBlocklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False)