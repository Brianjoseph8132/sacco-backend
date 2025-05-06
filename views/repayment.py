from models import LoanRepayment,db, Loan, Notification, Member, Account
from flask import jsonify,request, Blueprint
from werkzeug.security import generate_password_hash
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request
from decimal import Decimal
from datetime import datetime


repayment_bp = Blueprint("repayment_bp", __name__)


def create_notification(recipient_id, message, type, loan_id=None, sender_id=None):
    notif = Notification(
        recipient_id=recipient_id,
        sender_id=sender_id,
        message=message,
        type=type,
        loan_id=loan_id,
        timestamp=datetime.utcnow()
    )
    db.session.add(notif)
    db.session.commit()


# loan repayment
@repayment_bp.route('/<int:loan_id>/repayments', methods=['POST'])
@jwt_required()
def create_repayment(loan_id):
    current_user_id = get_jwt_identity()
    current_user = Member.query.get(current_user_id)
    
    loan = Loan.query.get_or_404(loan_id)
    
    if loan.member_id != current_user.id:
        return jsonify({"error": "You can only repay your own loans"}), 403
    
    if loan.status != 'approved':
        return jsonify({"error": "Cannot repay non-approved loans"}), 400

    data = request.get_json()
    
    try:
        amount = Decimal(str(data['amount']))  # Always convert to Decimal
        payment_method = data.get('payment_method', 'M-Pesa')
    except (ValueError, KeyError):
        return jsonify({"error": "Invalid payment details"}), 400

    if amount <= 0:
        return jsonify({"error": "Amount must be positive"}), 400

    # Calculate total due
    total_due = loan.amount * (Decimal('1') + loan.interest_rate / Decimal('100'))

    # Calculate total already repaid
    total_repaid = sum((r.amount for r in loan.repayments), Decimal('0.00'))

    new_total_repaid = total_repaid + amount

    repayment = LoanRepayment(
        loan_id=loan_id,
        amount=amount,
        payment_method=payment_method
    )

    db.session.add(repayment)

    balance = total_due - new_total_repaid

    # Fetch member's account
    member_account = Account.query.filter_by(member_id=current_user.id).first()
    if not member_account:
        return jsonify({"error": "Member account not found"}), 404

    # If loan fully paid or overpaid
    if new_total_repaid >= total_due:
        loan.status = 'paid'
        loan.due_date = datetime.utcnow()

        # Send loan paid notification
        notification = Notification(
            recipient_id=current_user.id,
            title="Loan Fully Repaid",
            message=f"Loan #{loan_id} has been fully settled. Total paid: {new_total_repaid}",
            type="loan_paid",
            loan_id=loan_id
        )
        db.session.add(notification)

        # Handle overpayment
        excess_amount = new_total_repaid - total_due
        if excess_amount > 0:
            member_account.deposit(excess_amount)

    try:
        db.session.commit()
        return jsonify({
            "message": "Repayment recorded",
            "balance_remaining": float(balance if balance > 0 else 0),
            "loan_status": loan.status,
            "overpaid_amount": float(excess_amount) if new_total_repaid > total_due else 0.0
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# repayment summary
@repayment_bp.route('/repayments/summary', methods=['GET'])
@jwt_required()
def repayment_summary():
    current_user = Member.query.filter_by(username=get_jwt_identity()).first()
    
    # Get all active loans
    loans = Loan.query.filter_by(member_id=current_user.id, status='approved').all()
    
    summary = []
    for loan in loans:
        total_repaid = sum(r.amount for r in loan.repayments)
        total_due = loan.amount * (1 + loan.interest_rate/100)
        
        summary.append({
            "loan_id": loan.id,
            "original_amount": float(loan.amount),
            "total_repaid": float(total_repaid),
            "balance": float(total_due - total_repaid),
            "due_date": loan.due_date.isoformat(),
            "next_payment_due": (  # Simple calculation
                min(loan.amount/3, total_due - total_repaid) 
                if total_repaid < total_due else 0
            )
        })
    
    return jsonify({"summary": summary})




@repayment_bp.route('/<int:loan_id>/balance', methods=['GET'])
@jwt_required()
def check_loan_balance(loan_id):
    current_user_id = get_jwt_identity()
    current_user = Member.query.get(current_user_id)
    
    loan = Loan.query.get_or_404(loan_id)

    # Only allow user to check their own loan
    if loan.member_id != current_user.id:
        return jsonify({"error": "You can only check your own loan"}), 403

    total_due = loan.amount * (1 + loan.interest_rate / 100)
    total_repaid = sum(r.amount for r in loan.repayments)
    balance = total_due - total_repaid

    return jsonify({
        "loan_id": loan_id,
        "loan_amount": loan.amount,
        "interest_rate": loan.interest_rate,
        "total_due": total_due,
        "total_repaid": total_repaid,
        "balance": balance,
        "loan_status": loan.status
    }), 200
