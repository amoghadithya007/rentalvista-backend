import os
import pymongo
from flask import Flask, jsonify, request, flash
from flask_mail import Mail
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
import json
from functools import wraps
from logging.config import fileConfig

from services.users import register_user, login_user, forgot_password, change_password, edit_profile, get_user_detail, logout_user
from services.token import decode_jwt

listen = ['high', 'default', 'low']

app = Flask(__name__)
fileConfig('logging.cfg')
# ref for log  https://www.scalyr.com/blog/getting-started-quickly-with-flask-logging/

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['MAIL_SERVER'] = 'smtp.sendgrid.net'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'apikey'
app.config['MAIL_PASSWORD'] = os.environ.get('SENDGRID_API_KEY')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

mail = Mail(app)
CORS(app)
bcrypt = Bcrypt(app)

MONGODB_URI = os.environ.get('MONGODB_URI_PART1') # add db url
client = MongoClient(MONGODB_URI + '&w=majority')
database = client.rentalvista

#client = pymongo.MongoClient("mongodb+srv://testuser:test123@tutorial6-ju5ov.mongodb.net/web?retryWrites=true&w=majority")
#database = client.web

def authentication(auth):
    @wraps(auth)
    def token_auth(*args, **kwargs):
        try:
            # print(request.json)
            token = request.json['headers']['Authorization']

            if not token:
                return jsonify({"msg": "Please Login First!"}), 403
            
            token_data = decode_jwt(token)
            if token_data == "Signature expired. Please log in again." or token_data == 'Invalid token. Please log in again.':
                return jsonify({"msg": "Please Login First!"}), 403
            
            if database.deniedTokens.count_documents({"token": token}) != 0:
                return jsonify({"msg": "Please Login First!"}), 403

            return auth(*args, **kwargs)
        except Exception as e:
            return jsonify({"msg" : 'Some internal error occurred!', "error": str(e)})

    return  token_auth

@app.route("/", methods=["GET"])
def index():
    app.logger.info('Processing Index')
    return "Hello"

@app.route("/users/signup", methods=["POST"])
def signup():
    app.logger.info('Processing Signup...')
    user = database.user
    try:
        data = request.json['data']
        temp = data['name']
    except:
        data = request.json
    return register_user(data["name"], data["email"], data["password"], data["contact"], user, bcrypt)

@app.route("/users/login", methods=["POST"])
def login():
    app.logger.info('Processing Login...')
    user = database.user
    print(request.json)
    try:
        data = request.json['data']
        temp = data['email']
    except:
        data = request.json
    return login_user(data['email'], data['password'], user, bcrypt)

@app.route("/users/forgot", methods=["POST"])
def forgot():
    app.logger.info('Processing Forgot Password...')
    user = database.user
    try:
        data = request.json['data']
        temp = data['email']
    except:
        data = request.json
    return forgot_password(data['email'], user, mail, bcrypt)

@app.route("/users/change", methods=["POST"])
@authentication
def change():
    app.logger.info('Processing Change Password...')
    token = request.json['headers']['Authorization']
    user = database.user
    try:
        data = request.json['data']
        temp = data['password']
        print(data)
    except:
        data = request.json
        print(data)
    return change_password(token, data['password'], data['new_password'], user, bcrypt)

@app.route("/users/user", methods=["POST"])
@authentication
def user_detail():
    app.logger.info('Processing Find User...')
    token = request.json['headers']['Authorization']
    user = database.user
    return get_user_detail(token, user)

@app.route("/users/edit", methods=["POST"])
@authentication
def edit():
    app.logger.info('Processing Edit Profile...')
    token = request.json['headers']['Authorization']
    user = database.user
    try:
        data = request.json['data']
        temp = data['name']
    except:
        data = request.json
    return edit_profile(token, data['name'], data['contact'], user)

@app.route("/users/logout", methods=["POST"])
@authentication
def logout():
    app.logger.info('Processing Logout...')
    token = request.json['headers']['Authorization']
    # print(token)
    user = database.user
    deniedToken = database.deniedTokens
    return logout_user(token, user, deniedToken)
    
@app.route("/getblog", methods=["GET"])
def getblog():
    blog_collection = database.blogs
    blog = blog_collection.find({}, {'_id': 0})
    blog_list = list(blog)
    return jsonify(blog_list)
    
@app.route("/addblog", methods=["POST"])
def addblog():
    get_user_data = request.get_json()
    title = get_user_data["title"]
    author = get_user_data["author"]
    desc = get_user_data["desc"]
    if not get_user_data:
        err = {'ERROR': 'No data passed'}
        return jsonify(err)
    else:
        lastid = database.blogs.find().sort([("_id",-1)]).limit(1)
        id = int(lastid [0]["id"]) + 1
        
        print(id)
        database.blogs.insert({'id': str(id),'title': title,'author': author, 'desc': desc})
        return jsonify("User added successfully!..")

@app.route("/put", methods=["PUT"])
def put():
    get_user_data = request.get_json()
    username = str(get_user_data["username"])
    new_name = get_user_data["newname"]
    if not get_user_data:
        err = {'ERROR': 'No data passed'}
        return jsonify(err)
    else:
        # If username is passed and is found in db, replace it with the new value
        if username:
            if db.users.find_one({'username': username}):
                db.users.update_one({'username': username}, {
                                    "$set": {'username': new_name}})
                return {'response': 'Username:'+str(username)+' updated with username:'+str(new_name)}
            else:
                return {'Error': 'Username ' + str(username) + ' not found'}

        else:
            return {'response': 'Username missing'}

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)

# !Done TODO: 0. Create a logout method
# !Done TODO: 1. Create a deniedTokens tokens 
# !Done TODO: 2. on logout add token to deniedTokens 
# !Done TODO: 3. on logout clear token from user 
# !Done TODO: 3. check token if token is in deniedTokens or not for services which needs authentication