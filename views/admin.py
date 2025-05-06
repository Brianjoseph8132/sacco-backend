from models import Account,db, Member, Transaction,LoanRepayment, Loan,Notification
from flask import jsonify,request, Blueprint
from werkzeug.security import generate_password_hash
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request
from decorator import admin_required
from datetime import datetime

admin_bp = Blueprint("admin_bp", __name__)



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



@admin_bp.route('/<int:loan_id>/approve', methods=['PATCH'])
@jwt_required()
@admin_required
def approve_loan(loan_id):
    from datetime import datetime  # just in case

    # Verify admin privileges
    current_user_id = get_jwt_identity()
    admin = Member.query.get(current_user_id)
    if not admin or not admin.is_admin:
        return jsonify({"error": "Admin privileges required"}), 403

    # Get loan and validate status
    loan = Loan.query.get_or_404(loan_id)
    if loan.status != 'pending':
        return jsonify({"error": "Loan has already been processed"}), 400

    # Parse request
    data = request.get_json()
    action = data.get('action')
    if action not in ['approve', 'reject']:
        return jsonify({"error": "Invalid action. Use 'approve' or 'reject'"}), 400

    # Process approval/rejection
    if action == 'approve':
        loan.status = 'approved'
        loan.approval_date = datetime.utcnow()
        loan.approved_by = admin.id  

        member_account = Account.query.filter_by(member_id=loan.member_id).first()
        if not member_account:
            return jsonify({"error": "Member account not found"}), 404

        member_account.deposit(float(loan.amount))

        transaction = Transaction(
            type="loan_disbursement",
            amount=float(loan.amount),
            account_id=member_account.id,
            loan_id=loan.id
        )
        db.session.add(transaction)

        notification_message = (
            f"Your loan of {loan.amount} has been approved!\n"
            f"Amount credited: {loan.amount}\n"
            f"New balance: {member_account.balance}\n"
            f"Term_months: {loan.term_months}"
        )
    else:
        loan.status = 'rejected'
        notification_message = (
            f"Your loan application of {loan.amount} has been rejected.\n"
            f"Reason: {data.get('reason', 'Not specified')}"
        )

    notification = Notification(
        recipient_id=loan.member_id,
        title=f"Loan {action.title()}",
        message=notification_message,
        type=f"loan_{action}",
        loan_id=loan.id
    )
    db.session.add(notification)

    try:
        db.session.commit()
        return jsonify({
            "message": f"Loan {action} successfully",
            "new_balance": member_account.balance if action == 'approve' else None
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500


# repayment management
@admin_bp.route('/repayments/<int:repayment_id>', methods=['GET', 'DELETE'])
@jwt_required()
@admin_required
def manage_repayment(repayment_id):
    # Admin verification
    current_user = Member.query.filter_by(username=get_jwt_identity()).first()
    if not current_user.is_admin:
        return jsonify({"error": "Admin access required"}), 403

    repayment = LoanRepayment.query.get_or_404(repayment_id)
    loan = repayment.loan

    if request.method == 'GET':
        return jsonify({
            "repayment": {
                "id": repayment.id,
                "loan_id": repayment.loan_id,
                "amount": float(repayment.amount),
                "date": repayment.payment_date.isoformat(),
                "method": repayment.payment_method
            },
            "loan_details": {
                "member": loan.member.username,
                "original_amount": float(loan.amount),
                "status": loan.status
            }
        })

    elif request.method == 'DELETE':
        # Recalculate loan status
        db.session.delete(repayment)
        
        # Check if loan status needs to be reverted
        if loan.status == 'paid':
            total_repaid = sum(r.amount for r in loan.repayments if r.id != repayment_id)
            if total_repaid < (loan.amount * (1 + loan.interest_rate/100)):
                loan.status = 'approved'
        
        try:
            db.session.commit()
            return jsonify({"message": "Repayment deleted successfully"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500


# 5. Admin: Send Notification to Member
@admin_bp.route('/send', methods=['POST'])
@jwt_required()
@admin_required
def send_notification():
    """Send a notification to a specific member (admin only)"""
    current_user_id = get_jwt_identity()
    admin = Member.query.get(current_user_id)
    
    if not admin or not admin.is_admin:
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    required_fields = ['recipient_id', 'title', 'message', 'type']
    if not all(field in data for field in required_fields):
        return jsonify({"error": f"Missing required fields: {', '.join(required_fields)}"}), 400

    notification = Notification(
        recipient_id=data['recipient_id'],
        sender_id=current_user_id,
        title=data['title'],
        message=data['message'],
        type=data['type'],
        loan_id=data.get('loan_id')
    )

    db.session.add(notification)
    db.session.commit()

    return jsonify({
        "message": "Notification sent successfully",
        "notification_id": notification.id
    }), 201

# 6. Admin: Broadcast Notification
@admin_bp.route('/broadcast', methods=['POST'])
@jwt_required()
@admin_required
def broadcast_notification():
    """Broadcast notification to all members (admin only)"""
    current_user_id = get_jwt_identity()
    admin = Member.query.get(current_user_id)
    
    if not admin or not admin.is_admin:
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    required_fields = ['title', 'message', 'type']
    if not all(field in data for field in required_fields):
        return jsonify({"error": f"Missing required fields: {', '.join(required_fields)}"}), 400

    members = Member.query.filter(Member.id != current_user_id).all()
    notifications = []
    
    for member in members:
        notifications.append(Notification(
            recipient_id=member.id,
            sender_id=current_user_id,
            title=data['title'],
            message=data['message'],
            type=data['type'],
            loan_id=data.get('loan_id')
        ))

    db.session.bulk_save_objects(notifications)
    db.session.commit()

    return jsonify({
        "message": f"Notification broadcasted to {len(members)} members"
    }), 201


@admin_bp.route('/admin/notifications', methods=['GET'])
@jwt_required()
@admin_required
def get_admin_notifications():
    """Get notifications with admin filters (all users or specific)"""
    # Verify admin privileges
    current_user_id = get_jwt_identity()
    admin = Member.query.get(current_user_id)
    if not admin or not admin.is_admin:
        return jsonify({"error": "Admin privileges required"}), 403

    # Pagination and filtering
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    member_id = request.args.get('member_id')
    notification_type = request.args.get('type')
    is_read = request.args.get('is_read')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Base query
    query = Notification.query.join(Member, Notification.recipient_id == Member.id)

    # Apply filters
    if member_id:
        query = query.filter(Notification.recipient_id == member_id)
    if notification_type:
        query = query.filter(Notification.type == notification_type)
    if is_read and is_read.lower() in ['true', 'false']:
        query = query.filter(Notification.is_read == (is_read.lower() == 'true'))
    
    # Date range filter
    if start_date:
        try:
            start_date = datetime.fromisoformat(start_date)
            query = query.filter(Notification.timestamp >= start_date)
        except ValueError:
            return jsonify({"error": "Invalid start_date format (use ISO format)"}), 400
    
    if end_date:
        try:
            end_date = datetime.fromisoformat(end_date)
            query = query.filter(Notification.timestamp <= end_date)
        except ValueError:
            return jsonify({"error": "Invalid end_date format (use ISO format)"}), 400

    # Execute query
    notifications = query.order_by(desc(Notification.timestamp))\
                       .paginate(page=page, per_page=per_page, error_out=False)

    # Build response
    return jsonify({
        "notifications": [{
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "type": n.type,
            "is_read": n.is_read,
            "timestamp": n.timestamp.isoformat(),
            "loan_id": n.loan_id,
            "recipient": {
                "id": n.recipient.id,
                "username": n.recipient.username,
                "name": f"{n.recipient.first_name} {n.recipient.last_name}"
            },
            "sender": {
                "id": n.sender.id,
                "username": n.sender.username,
                "name": f"{n.sender.first_name} {n.sender.last_name}"
            } if n.sender else None
        } for n in notifications.items],
        "meta": {
            "total": notifications.total,
            "pages": notifications.pages,
            "current_page": notifications.page,
            "filters": {
                "member_id": member_id,
                "type": notification_type,
                "is_read": is_read,
                "start_date": start_date,
                "end_date": end_date
            }
        }
    })





@admin_bp.route('/<int:loan_id>', methods=['GET'])
@jwt_required()
def get_loan_details(loan_id):
    """Get detailed loan information including repayment status"""
    current_user_id = get_jwt_identity()
    loan = Loan.query.get_or_404(loan_id)

    # Verify ownership or admin status
    if loan.member_id != current_user_id and not Member.query.get(current_user_id).is_admin:
        return jsonify({"error": "Unauthorized access"}), 403

    return jsonify({
        "loan": {
            "id": loan.id,
            "amount": float(loan.amount),
            "purpose": loan.purpose,
            "status": loan.status,
            "interest_rate": float(loan.interest_rate),
            "total_interest": loan.total_interest,
            "total_amount_due": loan.total_amount_due,
            "amount_repaid": loan.amount_repaid,
            "balance_remaining": loan.total_amount_due - loan.amount_repaid,
            "repayment_progress": f"{loan.repayment_progress:.1f}%",
            "application_date": loan.application_date.isoformat(),
            "approval_date": loan.approval_date.isoformat() if loan.approval_date else None,
            "due_date": loan.due_date.isoformat() if loan.due_date else None,
            "actual_completion_date": loan.actual_completion_date.isoformat() if loan.actual_completion_date else None
        },
        "repayments": [{
            "id": r.id,
            "amount": float(r.amount),
            "date": r.payment_date.isoformat(),
            "method": r.payment_method,
            "receipt_number": r.receipt_number
        } for r in loan.repayments]
    })
