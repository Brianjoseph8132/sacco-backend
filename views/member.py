from models import Member,db
from flask import jsonify,request, Blueprint
from werkzeug.security import generate_password_hash
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request
import re
from email_validator import validate_email, EmailNotValidError


member_bp = Blueprint("member_bp", __name__)



# Validate Kenyan phone number format
def validate_kenyan_phone_number(phone):
    pattern = r'^\+254\d{9}$'  # +254 followed by exactly 9 digits
    if not re.match(pattern, phone):
        return False
    return True



# Add Member 
@member_bp.route("/members", methods=["POST"])
def add_members():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    raw_password = data.get('password')
    phone = data.get('phone')
    id_number = data.get("id_number")
    is_admin = data.get("is_admin", False)

    # Validation for password length before hashing it
    if not isinstance(raw_password, str) or len(raw_password) != 8:
        return jsonify({"error": "Password must be exactly 8 characters"}), 400
    
    password = generate_password_hash(raw_password)  # Hash the password
    
    # Email validation using email-validator
    try:
        valid_email = validate_email(email)
    except EmailNotValidError as e:
        return jsonify({"error": f"Invalid email address: {str(e)}"}), 400

    # Phone validation (Kenyan phone number validation)
    if not validate_kenyan_phone_number(phone):
        return jsonify({"error": "Phone number must start with +254 and be followed by 9 digits."}), 400

    # Validation for ID number (should be 9 digits)
    if not isinstance(id_number, int) or len(str(id_number)) != 9:
        return jsonify({"error": "ID number should be exactly 9 digits"}), 400
    
    # Check if username or email already exists
    check_username = Member.query.filter_by(username=username).first()
    check_email = Member.query.filter_by(email=email).first()

    if check_email or check_username:
        return jsonify({"error": "Username or email already exists"}), 400

    # Add new member to the database
    new_member = Member(
        username=username,
        email=email,
        password=password,
        phone=phone,  # Store phone as it is, validated already
        id_number=id_number,
        is_admin=is_admin
    )
    db.session.add(new_member)
    db.session.commit()
    return jsonify({"success": "Member added successfully!"}), 200



# Update User
@member_bp.route("/update_member", methods=["PUT"])
def update_member():
    data = request.get_json()
    
