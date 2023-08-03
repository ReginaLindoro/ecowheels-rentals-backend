# app.py
from flask import Flask, jsonify, request
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import certifi
from flask_cors import CORS
import bcrypt
from enum import Enum
# TODO:
# from flask_jwt_extended import create_access_token
# from flask_jwt_extended import JWTManager
# from flask_jwt_extended import jwt_required

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

app.config['CORS_HEADERS'] = 'Content-Type'
ca = certifi.where()

# TODO: take configurations outside
# MongoDB configuration
DB_USER = 'ADAP'
DB_USER_PASS = 'ADAP'
MONGO_URI = f'mongodb+srv://{DB_USER}:{DB_USER_PASS}@adapdb.g2igjno.mongodb.net/?retryWrites=true&w=majority'
DB_NAME = 'ADAPdb'
USERS_COLLECTION = 'Users'
RESOURCES_COLLECTION = 'Resources'
PROJECTS_COLLECTION = 'Projects'

# TODO: ADD JWT LATER
# app.config['JWT_SECRET_KEY'] = 'd4949995b0fff3aa8a69cf35092c71bdfa45388049089b91ad77a8f7a41aa61d699fdab8'
# jwt = JWTManager(app)

# TODO: move all these error functions to a different file

# Enum of all status types


class StatusCode(Enum):
    SUCCESS = 200
    CREATION_SUCCESS = 201
    BAD_REQUEST = 400
    WRONG_CREDS = 401
    NOT_FOUND = 404
    USER_EXISTS = 409
    DATABASE_ERROR = 700
    SERVER_ERROR = 500

# Enum of update type in hardware sets


class HardwareUpdateTyep(Enum):
    CHECK_IN = 'checkin'
    CHECK_OUT = 'checkout'


# this function creates an error object
# errorType -> to check with errorType
# message -> message returned from exception or a custom message
def createErrorObject(statusCode, message):
    if statusCode is StatusCode.BAD_REQUEST.value:
        return {
            'code': 400,
            'data': {
                'message': message
            },
            'message': 'Failure'
        }
    elif statusCode is StatusCode.WRONG_CREDS.value:
        return {
            'code': 401,
            'data': {
                'message': message
            },
            'message': 'Failure'
        }
    elif statusCode is StatusCode.NOT_FOUND.value:
        return {
            'code': 404,
            'data': {
                'message': message
            },
            'message': 'Failure'
        }
    elif statusCode is StatusCode.USER_EXISTS.value:
        return {
            'code': 409,
            'data': {
                'message': message
            },
            'message': 'Failure'
        }
    elif statusCode is StatusCode.SERVER_ERROR.value:
        return {
            'code': 500,
            'data': {
                'message': message
            },
            'message': 'Failure'
        }
    elif statusCode is StatusCode.DATABASE_ERROR.value:
        return {
            'code': 700,
            'data': {
                'message': message
            },
            'message': 'Failure'
        }


# TODO:
# creates the login success object with access token
# def createLoginSucessObject(username):
#     return {
#                 'code' : 200,
#                 'data'  : {
#                     'accessToken' : create_access_token(identity=username)
#                 },
#                 'message' : 'Success'
#             }


# creates a success object with a message and status code
def createSuccessObject(statusCode, message):
    return {
        'code': statusCode,
        'data': {
            'message': message
        },
        'message': 'Success'
    }


# creates a return object for get call of hardware sets
def createHardwareObject(statusCode, hardwareSets, message):
    return {
        'code': statusCode,
        'data': {
            'hardwareSets': hardwareSets,
            'message': message
        },
        'message': 'Success'
    }


# route for getting hardware
@app.route('/api/get-hardware', methods=['GET'])
# TODO:
# @jwt_required()
def getHWSet():
    result = fetchHWSetsFromDB()

    if result['isError']:
        returnObject = createErrorObject(
            statusCode=result['statusCode'], message=result['message'])
        return jsonify(returnObject), result['statusCode']
    else:
        returnObject = createHardwareObject(
            statusCode=result['statusCode'], hardwareSets=result['hardwareSets'], message=result['message'])
        return jsonify(returnObject), result['statusCode']


# fetches data from the DB
# returns the result object or error object
def fetchHWSetsFromDB():
    try:
        # Connect to database
        client = MongoClient(MONGO_URI, tlsCAFile=ca)
        db = client[DB_NAME]
        # getting the collection
        resourcesCollection = db[RESOURCES_COLLECTION]

        # Retrieve data from the database and convert to a list of dictionaries
        hwDataFromDB = list(resourcesCollection.find())

        # check if both the hardwares are present
        if len(hwDataFromDB) > 1:
            # use this empty array for the return object to be sent
            hardwareSets = []
            for hwDataSet in hwDataFromDB:
                # if any of these keys are not present, close client and throw exception
                if not resourcesCollection.find({'capacity': {'$exists': True}}) or not resourcesCollection.find({'availability': {'$exists': True}}):
                    client.close()
                # add these objects in an array for the response
                else:
                    object = {
                        'capacity': hwDataSet['capacity'],
                        'availability': hwDataSet['availability']
                    }
                    hardwareSets.append(object)
        # if both hardwares are not present, throw error
        else:
            client.close()
            resultObject = {
                'isError': True,
                'statusCode': 700,
                'message': 'Database error: Database doesn\'t have enough hardwares.'
            }
            return resultObject

        client.close()
        # result object for the final response
        resultObject = {
            'isError': False,
            'statusCode': 200,
            'hardwareSets': hardwareSets,
            'message': 'Hardware Data fetched successfully!'
        }
        return resultObject

    except PyMongoError as e:
        # Handle database-related errors
        client.close()
        resultObject = {
            'isError': True,
            'statusCode': 700,
            'message': 'Database error: ' + str(e)
        }
        return resultObject
    except Exception as e:
        # Handle other exceptions
        client.close()
        resultObject = {
            'isError': True,
            'statusCode': 500,
            'message': 'Server error: ' + str(e)
        }
        return resultObject


# route for checkin/checkout hardware
@app.route('/api/update-hardware', methods=['POST'])
def updateHWSets():
    # storing the request object
    hwSet1Qty = request.json['hardwareSet1']['quantity']
    hwSet2Qty = request.json['hardwareSet2']['quantity']
    type = request.json['type']

    # filter based on type of request
    if type == HardwareUpdateTyep.CHECK_IN.value:
        result = checkinHardwareSetsToDB(
            hwSet1Qty=hwSet1Qty, hwSet2Qty=hwSet2Qty)
    else:
        result = checkoutHardwareSetsToDB(
            hwSet1Qty=hwSet1Qty, hwSet2Qty=hwSet2Qty)

    # if returns error -> return the response object
    if result['isError']:
        returnObject = createErrorObject(
            statusCode=result['statusCode'], message=result['message'])
        return jsonify(returnObject), result['statusCode']
    # if successful, fetch the HW Sets and return as response
    else:
        getResult = fetchHWSetsFromDB()

        if getResult['isError']:
            returnObject = createErrorObject(
                statusCode=getResult['statusCode'], message=getResult['message'])
            return jsonify(returnObject), getResult['statusCode']
        else:
            returnObject = createHardwareObject(
                statusCode=getResult['statusCode'], hardwareSets=getResult['hardwareSets'], message=result['message'])
            return jsonify(returnObject), getResult['statusCode']


# this method updates the database to reflect new available value of hardware
# when user checks in number of units specified by quantity
def checkinHardwareSetsToDB(hwSet1Qty, hwSet2Qty):
    try:
        # Connect to database
        client = MongoClient(MONGO_URI, tlsCAFile=ca)
        db = client[DB_NAME]
        # getting the collection
        resourcesCollection = db[RESOURCES_COLLECTION]

        # Retrieve data from the database and convert to a list of dictionaries
        hwDataFromDB = list(resourcesCollection.find())

        # check if both the hardwares are present
        if len(hwDataFromDB) > 1:
            for hwDataSet in hwDataFromDB:
                # if any of these keys are not present, close client and throw exception
                if not resourcesCollection.find({'capacity': {'$exists': True}}) or not resourcesCollection.find({'availability': {'$exists': True}}):
                    client.close()
                # check the id and then check the difference between capacity and availability to know max checkin number
                elif hwDataSet['hardwareID'] == '1' and ((hwDataSet['capacity']-hwDataSet['availability']) >= hwSet1Qty):
                    updatedAvailability = hwDataSet['availability'] + hwSet1Qty
                    resourcesCollection.update_one(
                        {'hardwareID': '1'}, {'$set': {'availability': updatedAvailability}})
                elif hwDataSet['hardwareID'] == '2' and ((hwDataSet['capacity']-hwDataSet['availability']) >= hwSet2Qty):
                    updatedAvailability = hwDataSet['availability'] + hwSet2Qty
                    resourcesCollection.update_one(
                        {'hardwareID': '2'}, {'$set': {'availability': updatedAvailability}})
                # if these conditions don't meet then either qty1 or qty2 is wrong; send an error
                else:
                    client.close()
                    resultObject = {
                        'isError': True,
                        'statusCode': 400,
                        'message': 'Trying to checkin more hardware than total capacity! Atleast 1 or more values are entered wrong. Please try again.'
                    }
                    return resultObject
        # if both hardwares are not present, throw error
        else:
            client.close()
            resultObject = {
                'isError': True,
                'statusCode': 700,
                'message': 'Database error: Database doesn\'t have enough hardwares.'
            }
            return resultObject

        client.close()
        # result object for the final response
        resultObject = {
            'isError': False,
            'statusCode': 200,
            'message': 'Hardware Data updated successfully!'
        }
        return resultObject

    except PyMongoError as e:
        # Handle database-related errors
        client.close()
        resultObject = {
            'isError': True,
            'statusCode': 700,
            'message': 'Database error: ' + str(e)
        }
        return resultObject
    except Exception as e:
        # Handle other exceptions
        client.close()
        resultObject = {
            'isError': True,
            'statusCode': 500,
            'message': 'Server error: ' + str(e)
        }
        return resultObject


# this method updates the database to reflect new available value of hardware
# when user checks out number of units specified by quantity
def checkoutHardwareSetsToDB(hwSet1Qty, hwSet2Qty):
    try:
        # Connect to database
        client = MongoClient(MONGO_URI, tlsCAFile=ca)
        db = client[DB_NAME]
        # getting the collection
        resourcesCollection = db[RESOURCES_COLLECTION]

        # Retrieve data from the database and convert to a list of dictionaries
        hwDataFromDB = list(resourcesCollection.find())

        # check if both the hardwares are present
        if len(hwDataFromDB) > 1:
            for hwDataSet in hwDataFromDB:
                # if any of these keys are not present, close client and throw exception
                if not resourcesCollection.find({'capacity': {'$exists': True}}) or not resourcesCollection.find({'availability': {'$exists': True}}):
                    client.close()
                # check the id and then check the availability to know max checkout number
                elif hwDataSet['hardwareID'] == '1' and (hwDataSet['availability'] >= hwSet1Qty):
                    updatedAvailability = hwDataSet['availability'] - hwSet1Qty
                    resourcesCollection.update_one(
                        {'hardwareID': '1'}, {'$set': {'availability': updatedAvailability}})
                elif hwDataSet['hardwareID'] == '2' and (hwDataSet['availability'] >= hwSet2Qty):
                    updatedAvailability = hwDataSet['availability'] - hwSet2Qty
                    resourcesCollection.update_one(
                        {'hardwareID': '2'}, {'$set': {'availability': updatedAvailability}})
                else:
                    # if these conditions don't meet then either qty1 or qty2 is wrong; send an error
                    client.close()
                    resultObject = {
                        'isError': True,
                        'statusCode': 400,
                        'message': 'Trying to checkout more hardware than available! Atleast 1 or more values are entered wrong. Please try again.'
                    }
                    return resultObject
        # if both hardwares are not present, throw error
        else:
            client.close()
            resultObject = {
                'isError': True,
                'statusCode': 700,
                'message': 'Database error: Database doesn\'t have enough hardwares.'
            }
            return resultObject

        client.close()
        # result object for the final response
        resultObject = {
            'isError': False,
            'statusCode': 200,
            'message': 'Hardware Data updated successfully!'
        }
        return resultObject

    except PyMongoError as e:
        # Handle database-related errors
        client.close()
        resultObject = {
            'isError': True,
            'statusCode': 700,
            'message': 'Database error: ' + str(e)
        }
        return resultObject
    except Exception as e:
        # Handle other exceptions
        client.close()
        resultObject = {
            'isError': True,
            'statusCode': 500,
            'message': 'Server error: ' + str(e)
        }
        return resultObject


# API endpoint for adding a new project
@app.route('/api/create-project', methods=['POST'])
def create_project():

    # storing request project
    projectID = request.json['projectId']
    name = request.json['name']
    description = request.json['description']

    result = addproject(projectID=projectID, name=name,
                        description=description)

    if result['isError']:
        returnObject = createErrorObject(
            statusCode=result['statusCode'], message=result['message'])
        return jsonify(returnObject), result['statusCode']
    else:
        returnObject = createSuccessObject(
            statusCode=result['statusCode'], message=result['message'])
        return jsonify(returnObject), result['statusCode']


def addproject(projectID, name, description):
    try:
        # Connect to database
        client = MongoClient(MONGO_URI, tlsCAFile=ca)
        db = client[DB_NAME]
        # getting the project collection
        projectCollection = db['Projects']

        # check if the collection is empty or not -> to avoid the first project registration
        if len(list(projectCollection.find())) != 0:
            # checking for the projectID, if already exists, return an object with an error
            if projectCollection.find_one({'projectID': projectID}):
                resultObject = {
                    'isError': True,
                    'statusCode': 409,
                    'message': 'ProjectID already exists'
                }
                return resultObject

        # create a new project
        newProject = {
            'projectID': projectID,
            'name': name,
            'description': description
        }

        # insert project in the Projects collection
        projectCollection.insert_one(newProject)

        client.close()
        # return the success object
        resultObject = {
            'isError': False,
            'statusCode': 201,
            'message': 'Project added successfully!',
        }
        return resultObject

    except PyMongoError as e:
        # Handle database-related errors
        client.close()
        resultObject = {
            'isError': True,
            'statusCode': 700,
            'message': 'Database error: ' + str(e)
        }
        return resultObject

    except Exception as e:
        # Handle other exceptions
        client.close()
        resultObject = {
            'isError': True,
            'statusCode': 500,
            'message': 'Server error: ' + str(e)
        }
        return resultObject


# Route to check if a ProjectID exists in the MongoDB database
@app.route('/api/join-project', methods=['POST'])
def checkProjectID():
    # storing the request object
    projectID = request.json['projectId']

    result = checkProjectinDB(projectID=projectID)

    if result['isError']:
        returnObject = createErrorObject(
            statusCode=result['statusCode'], message=result['message'])
        return jsonify(returnObject), result['statusCode']
    else:
        returnObject = createSuccessObject(
            statusCode=result['statusCode'], message=result['message'])
        # TODO:
        # returnObject = createLoginSucessObject(username=username)
        return jsonify(returnObject), result['statusCode']


# validates projectID
def checkProjectinDB(projectID):
    try:
        # Connect to database
        client = MongoClient(MONGO_URI, tlsCAFile=ca)
        db = client[DB_NAME]
        # getting the collection
        projectCollection = db['Projects']

        # check if the project collection is empty or not -> avoid checking if project collection is empty
        if len(list(projectCollection.find())) != 0:
            # check if project exixts in db
            project = projectCollection.find_one({'projectID': projectID})

            if project is not None:
                if project['projectID'] == projectID:
                    resultObject = {
                        'isError': False,
                        'statusCode': 200,
                        'message': f'Joined Project: {projectID} successfully!'
                    }
                    return resultObject
            else:
                resultObject = {
                    'isError': True,
                    'statusCode': 404,
                    'message': f'ProjectID {projectID} does not exist! Enter a valid projectID.'
                }
                return resultObject

        else:
            returnObject = {
                'isError': True,
                'statusCode': 404,
                'message': f'There are no projects in the database.'
            }
        return returnObject

    except PyMongoError as e:
        # Handle database-related errors
        client.close()
        resultObject = {
            'isError': True,
            'statusCode': 700,
            'message': 'Database error: ' + str(e)
        }
        return resultObject

    except Exception as e:
        # Handle other exceptions
        client.close()
        resultObject = {
            'isError': True,
            'statusCode': 500,
            'message': 'Server error: ' + str(e)
        }
        return resultObject


# TODO: move in different files
# make utility functions
# make a standard object creation function
# route for login
@app.route('/api/login', methods=['POST'])
def login_user():
    # storing the request object
    username = request.json['username']
    password = request.json['password']

    result = checkUserInDB(username=username, password=password)

    if result['isError']:
        returnObject = createErrorObject(
            statusCode=result['statusCode'], message=result['message'])
        return jsonify(returnObject), result['statusCode']
    else:
        returnObject = createSuccessObject(
            statusCode=result['statusCode'], message=result['message'])
        # TODO:
        # returnObject = createLoginSucessObject(username=username)
        return jsonify(returnObject), result['statusCode']


# validates username and password
def checkUserInDB(username, password):
    try:
        # Connect to database
        client = MongoClient(MONGO_URI, tlsCAFile=ca)
        db = client[DB_NAME]
        # getting the collection
        usersCollection = db[USERS_COLLECTION]

        # check if the collection if empty of not -> avoid checking if collection is empty
        if len(list(usersCollection.find())) != 0:
            # check if user exixts and then validated the encryptedPassword with the one store in db
            if usersCollection.find_one({'username': username}):
                user = usersCollection.find_one({'username': username})
                passwordFromDB = user.get('password')
                if passwordValidation(
                    passwordFromDB=passwordFromDB, passwordFromRequest=password):
                    client.close()
                    resultObject = {
                        'isError': False,
                        'statusCode': 200,
                        'message': 'Logged in successfully!'
                    }
                    return resultObject
                # if password is wrong, return error object
                else:
                    client.close()
                    resultObject = {
                        'isError': True,
                        'statusCode': 401,
                        'message': 'Username or Password is wrong. Please try again!'
                    }
                    return resultObject
            # if username is wrong, return error object
            else:
                client.close()
                resultObject = {
                    'isError': True,
                    'statusCode': 401,
                    'message': 'Username or Password is wrong. Please try again!'
                }
                return resultObject
        # if there is no user in db, return error
        else:
            client.close()
            resultObject = {
                'isError': True,
                'statusCode': 404,
                'message': 'Users not found! Database has no users registered yet.'
            }
            return resultObject
    except PyMongoError as e:
        # Handle database-related errors
        client.close()
        resultObject = {
            'isError': True,
            'statusCode': 700,
            'message': 'Database error: ' + str(e)
        }
        return resultObject
    except Exception as e:
        # Handle other exceptions
        client.close()
        resultObject = {
            'isError': True,
            'statusCode': 500,
            'message': 'Server error: ' + str(e)
        }
        return resultObject


# this function validates the passwords from request and db
def passwordValidation(passwordFromDB, passwordFromRequest):
    # encode the password from request
    passwordFromRequest = passwordFromRequest.encode('utf-8')
    # use checkpw function to validate the two passwords and return a bool a value
    return bcrypt.checkpw(passwordFromRequest, passwordFromDB)


# TODO: move in different files
# make utility functions
# make a standard object creation function
# register user
# route for register
@app.route('/api/register', methods=["POST"])
def register_user():
    # storing the request object
    username = request.json['username']
    password = request.json['password']

    result = addUser(username=username, password=password)

    if result['isError']:
        returnObject = createErrorObject(
            statusCode=result['statusCode'], message=result['message'])
        return jsonify(returnObject), result['statusCode']
    else:
        returnObject = createSuccessObject(
            statusCode=result['statusCode'], message=result['message'])
        return jsonify(returnObject), result['statusCode']


# add user to db
def addUser(username, password):
    try:
        # Connect to database
        client = MongoClient(MONGO_URI, tlsCAFile=ca)
        db = client[DB_NAME]
        # getting the collection
        usersCollection = db['Users']

        # check if the collection if empty of not -> to avoid the first user registration
        if len(list(usersCollection.find())) != 0:
            # checking for the username passed in the request, if already exists, return an object with an error
            if usersCollection.find_one({'username': username}):
                client.close()
                resultObject = {
                    'isError': True,
                    'statusCode': 409,
                    'message': 'User already exists'
                }
                return resultObject

        # create a new user
        newUser = {
            'username': username,
            'password': encrypt(password),
        }

        # insert user in the users collection
        usersCollection.insert_one(newUser)
        client.close()
        # return the success object
        resultObject = {
            'isError': False,
            'statusCode': 201,
            'message': 'User added successfully!',
        }
        return resultObject
    except PyMongoError as e:
        # Handle database-related errors
        client.close()
        resultObject = {
            'isError': True,
            'statusCode': 700,
            'message': 'Database error: ' + str(e)
        }
        return resultObject

    except Exception as e:
        # Handle other exceptions
        client.close()
        resultObject = {
            'isError': True,
            'statusCode': 500,
            'message': 'Server error: ' + str(e)
        }
        return resultObject


# this function ecrypts the text passed to it
# converts into binary
# adds salt
# hashes the text and salt together
def encrypt(text):
    # converting text to array of bytes
    bytes = text.encode('utf-8')
    # generating the salt
    salt = bcrypt.gensalt()
    # Hashing the text
    hash = bcrypt.hashpw(bytes, salt)
    return hash


if __name__ == '__main__':
    app.run(debug=True)
