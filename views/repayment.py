from models import LoanRepayment,db
from flask import jsonify,request, Blueprint
from werkzeug.security import generate_password_hash
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request


repayment_bp = Blueprint("repayment_bp", __name__)