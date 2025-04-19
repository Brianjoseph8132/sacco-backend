from models import Loan,db
from flask import jsonify,request, Blueprint
from werkzeug.security import generate_password_hash
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request


loan_bp = Blueprint("loan_bp", __name__)