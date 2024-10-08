from app.db import mongo_client # Import PyMongo
from flask import Blueprint, jsonify, request
from bson.objectid import ObjectId
from .models import User, UserSchema
from . import bcrypt
import os
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from marshmallow import ValidationError
from .alerts import send_alert
from .classifyAnimalImage import *
from .classifyBirdImage import *
from .classifyBirdSound import *
from .classifyAnimalSound import *

routes = Blueprint("routes", __name__)

#Test Route
@routes.route("/", methods=["GET"])
def index():
    return jsonify({"message": "Hello, World!"})

#User Authentication Routes And Business Logic

user_schema = UserSchema() # Create a UserSchema instance

#API END POINT FOR REGISTERING A USER IN THE DATABASE

@routes.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing data"}), 400

    try:
        user = user_schema.load(data)
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400

    # Check for duplicate username or email before saving
    user_exists = mongo_client.db.users.find_one({
        '$or': [
            {'username': user.username},
            {'email': user.email}
        ]
    })
    if user_exists:
        return jsonify({"error": "Username or email already exists"}), 400
   
    mongo_client.db.users.insert_one(user.to_dict())
    return jsonify({
        "message": "User created successfully",
        "user": user_schema.dump(user)
    }), 201


#API END POINT FOR LOGIN A USER IN THE DATABASE
@routes.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing data"}), 400
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({"error": "Missing username or password"}), 400
    user_dict = mongo_client.db.users.find_one({'email': email})
    

    try:
        # Retrieve user from database (implement this)
        # e.g., user = db.users.find_one({"email": email})

        if not user_dict:
            return jsonify({"message": "User not found"}), 404
            # Print retrieved user details for debugging
        print(f"Retrieved user: {user_dict}")

        user = User(
        username=user_dict.get('username'),
        email=user_dict.get('email'),
        password=user_dict.get('password'),
        created_at=user_dict.get('created_at'),
        _id=user_dict.get('_id')
        )

        # Retrieve the hashed password from the user_dict
        hashed_password = user_dict.get('password')
        
        

        if not bcrypt.check_password_hash(hashed_password, password):
            return jsonify({"message": "Incorrect password"}), 401
         # Convert ObjectId to string
        user_dict['_id'] = str(user_dict['_id'])

        access_token = create_access_token(identity=user.email)
        response_dict = {
            "username": user_dict.get('username'),
            "email": user_dict.get('email'),
            "accesstoken": access_token
        }

        return jsonify(response_dict), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 400

#routes regarding alerts
@routes.route("/sendalert", methods=["POST"])
def send_alert_route():
    print("inside send alert route")
    data = request.form.to_dict()
    image_file = request.files['image']
    user_email = data.get('user_email')
    user_name = data.get('user_name')
    user = mongo_client.db.users.find_one({'email': user_email})


    if not user:
        return jsonify({"message": "User not found"}), 404
    
    


    s=send_alert(data,image_file)
    return jsonify({"message": "Alert sent successfully"}), 200

#Get all the alerts for a specific user
@routes.route("/api/alerts", methods=["GET"])
@jwt_required()
def get_alerts():
    user_email = get_jwt_identity()
    user = mongo_client.db.users.find_one({'email': user_email})
    if not user:
        return jsonify({"message": "User not found"}), 404
    alerts = user.get('alerts', [])  
    for alert in alerts:
        if '_id' in alert:
            alert['_id'] = str(alert['_id'])  # Convert ObjectId to string
        if 'user_id' in alert:
            alert['user_id'] = str(alert['user_id'])
    return jsonify({"alerts": alerts}), 200


@routes.route("/classify-bird-audio", methods=["POST"])
def classify_bird_audio_():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file found"}), 400
    audio_file = request.files['audio']
    response = classify_bird_sound(audio_file)
    return jsonify(response)

@routes.route("/classify-animal-audio", methods=["POST"])
def classify_animal_audio_():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file found"}), 400
    audio_file = request.files['audio']
    response = classify_animal_sound(audio_file)
    return jsonify(response)

@routes.route("/classify-bird-image", methods=["POST"])
def classify_bird_image_():
    if 'image' not in request.files:
        return jsonify({"error": "No image file found"}), 400
    image_file = request.files['image']
    response = classify_bird_image(image_file)
    return jsonify(response)

@routes.route("/classify-animal-image", methods=["POST"])
def classify_animal_image_():
    if 'image' not in request.files:
        return jsonify({"error": "No image file found"}), 400
    image_file = request.files['image']
    response = classify_animal_image(image_file)
    return jsonify(response)