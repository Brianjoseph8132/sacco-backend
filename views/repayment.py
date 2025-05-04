from models import LoanRepayment,db, Loan, Notification
from flask import jsonify,request, Blueprint
from werkzeug.security import generate_password_hash
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request


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
    
    # Validate payment
    try:
        amount = float(data['amount'])
        payment_method = data.get('payment_method', 'M-Pesa')
    except (ValueError, KeyError):
        return jsonify({"error": "Invalid payment details"}), 400

    if amount <= 0:
        return jsonify({"error": "Amount must be positive"}), 400

    # Create repayment record
    repayment = LoanRepayment(
        loan_id=loan_id,
        amount=amount,
        payment_method=payment_method,
        status='completed'
    )

    # Update loan status if fully repaid
    total_repaid = sum(r.amount for r in loan.repayments) + amount
    total_due = loan.amount * (1 + loan.interest_rate/100)  # Principal + interest
    
    if total_repaid >= total_due:
        loan.status = 'paid'
        loan.due_date = datetime.utcnow()
        
        # Create paid notification
        notification = Notification(
            recipient_id=current_user.id,
            title="Loan Fully Repaid",
            message=f"Loan #{loan_id} has been fully settled. Total paid: {total_repaid}",
            type="loan_paid",
            loan_id=loan_id
        )
        db.session.add(notification)

    db.session.add(repayment)
    
    try:
        db.session.commit()
        return jsonify({
            "message": "Repayment recorded",
            "balance": float(total_due - total_repaid),
            "loan_status": loan.status
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