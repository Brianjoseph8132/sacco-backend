from models import Account,db
from flask import jsonify,request, Blueprint
from werkzeug.security import generate_password_hash
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request


account_bp = Blueprint("account_bp", __name__)