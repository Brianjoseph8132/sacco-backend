from models import Notification,db
from flask import jsonify,request, Blueprint
from werkzeug.security import generate_password_hash
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request


notification_bp = Blueprint("notification_bp", __name__)