from .token import encode_jwt, decode_jwt
from flask import flash, jsonify
from flask_mail import Message
from .password_generator import generate_random_pass
from datetime import datetime
from bson.objectid import ObjectId

def register_user(name: str, email: str, password: str, contact:str, user, bcrypt) -> str:
    try:
        if user.count_documents({"email": email}) == 0:
            hashed_password = bcrypt.generate_password_hash(password)
            user_id = user.insert_one({"name":name, "email": email, "password": hashed_password, "contact": contact, "token": ""}).inserted_id
            return jsonify({"msg" : 'Registration Success!'})

        return "User Already Exist!"
    except Exception as e:
        return jsonify({"msg" : 'Some internal error occurred!', "error": str(e)})

def login_user(email: str, password: str, user, bcrypt) -> str:
    try:
        if user.count_documents({"email": email}) == 0:
            return jsonify({"msg":"User does not exist!"})
    except Exception as e:
        print(e)
    try:
        result = user.find_one({"email":email}, {"password": password, "_id":1})
        if compare_password(bcrypt, result['password'], password):
            token = encode_jwt(str(result['_id'])) # converted id into string then passed to encode_jwt
            user.update_one({"email" : email},{'$set': { "token" : token.decode('utf-8')}})
            return jsonify({'msg': 'Login Success!', "token": token.decode('utf-8')}) # need to decode JWT from bytes to string 

        return jsonify({"msg" : "Email or Password is incorrect!"})
    except Exception as e:
        return jsonify({"msg" : 'Some internal error occurred!', "error": str(e)})

def forgot_password(email: str, user, mail, bcrypt) -> str:
    try:
        if user.count_documents({"email": email}) == 0:
            return jsonify({"msg": "User does not exist!"})

        new_password = generate_random_pass()

        msg = Message('Reset Password', recipients=[email])
        msg.html = ('<h2>Password Reset</h2>' 
                    '<p>Your new password is <b>'+new_password+'</b></p>'
                    '<p><i><b>Note:</b>Do not Share this mail with anyone.</i></P>')
        mail.send(msg)
        flash(f'Reset Password sent to {email}.')
        
        hashed_password = bcrypt.generate_password_hash(new_password)
        user.update_one({"email" : email},{'$set': { "password" : hashed_password}})
        return jsonify({"msg" : "Password Reset Success!"})
    except Exception as e:
        return jsonify({"msg" : 'Some internal error occurred!', "error": str(e)})

def change_password(token: str, password: str, new_password: str, user, bcrypt) -> str:
    try:
        print(token)
        # token = token.encode('utf-8')
        user_data = user.find_one({"token":token}, {"password": password, "_id":0})
        print(user_data)
        if compare_password(bcrypt, user_data['password'], password):
            print('in if')
            hashed_password = bcrypt.generate_password_hash(new_password)
            user.update_one({"token" : token},{'$set': { "password" : hashed_password}})
            return jsonify({"msg" : "Password Changed!"})
        return jsonify({"msg" : 'Incorrect Current Password!'})
    except Exception as e:
        return jsonify({"msg" : 'Some internal error occurred!', "error": str(e)})

def edit_profile(token: str, name: str, contact: str, user):
    try:
        # token = token.encode('utf-8')
        user.update_one({"token" : token},{'$set': { "name" : name, "contact": contact}})
        updated_data = user.find_one({"token": token}, {"name": name, "contact": contact ,"_id":0})
        return jsonify(updated_data)
    except Exception as e:
        return jsonify({"msg" : 'Some internal error occurred!', "error": str(e)})

def get_user_detail(token: str, user):
    try:
        # token = token.encode('utf-8')
        data = user.find_one({"token": token}, {"name": 1, "email": 1, "contact": 1 ,"_id":0})
        return jsonify(data)
    except Exception as e:
        return jsonify({"msg" : 'Some internal error occurred!', "error": str(e)})

def logout_user(token: str, user, deniedToken) -> str:
    token_data = decode_jwt(token)
    # print(token_data)
    try:
        user.update_one({"_id" : ObjectId(token_data)},{'$set': {"token" : ""}})
        deniedToken.insert_one({"token": token, "denied_time": str(datetime.now())}).inserted_id
    except Exception as e:
        return jsonify({"msg" : 'Some internal error occurred!', "error": str(e)})
    return jsonify({"msg": "Logout Success!"})

def compare_password(bcrypt, hashed_password, password) -> bool:
    return bcrypt.check_password_hash(hashed_password, password)