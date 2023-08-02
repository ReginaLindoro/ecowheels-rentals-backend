# app.py
from flask import Flask, jsonify, request
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import bson.json_util as json_util
import certifi
import json
from flask_cors import CORS
import bcrypt

app = Flask(__name__)
CORS(app)
ca = certifi.where()

#TODO: take configurations outside
# MongoDB configuration
DB_USER = 'ADAP'
DB_USER_PASS = 'ADAP'
MONGO_URI = f'mongodb+srv://{DB_USER}:{DB_USER_PASS}@adapdb.g2igjno.mongodb.net/?retryWrites=true&w=majority'
DB_NAME = 'ADAPdb'

# variables
err = {
    "error": {
        "code":100,
    "message": "Error!"
        }
}

# This method gets hardware information from the database
@app.route('/api/getHardware', methods=['GET'])
def getHWSet():
    try:
        # Connect to database
        client = MongoClient(MONGO_URI, tlsCAFile=ca)
        db = client[DB_NAME]
        collection = db['Resources']

        # Retrieve data from the database and convert to a list of dictionaries
        hwSetData = list(collection.find())

        # Close the databse connection
        client.close()

        # Convert the data to a JSON string and return data
        return json_util.dumps(hwSetData)
    except PyMongoError as e:
        # Handle database-related errors
        client.close()
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        # Handle other exceptions
        client.close()
        return err

#TODO: move in different files
#make utility functions
#make a standard object creation function


@app.route('/api/signin', methods=["POST"])
def login_user():
    #storing the request object
    object = request.json
    username = object['username']
    password = object['password']

    returnObject = checkUserInDB(username=username, password=password) 
    return jsonify(returnObject)

def checkUserInDB(username, password):
    try:
        # Connect to database
        client = MongoClient(MONGO_URI, tlsCAFile=ca)
        db = client[DB_NAME]
        #getting the collection
        usersCollection = db['Users']

        #check if the collection if empty of not -> avoid checking if collection is empty
        if len(list(usersCollection.find())) != 0:
            #check if user exixts and then validated the encryptedPassword with the one store in db
            if usersCollection.find_one({'username' : username}):
                user = usersCollection.find_one({'username' : username})
                passwordFromDB = user.get('password')
                print(passwordFromDB)
                if passwordValidation(passwordFromDB=passwordFromDB, passwordFromRequest=password):
                    returnObject = {
                        'code' : 200,
                        'data'  : {
                            'message' : 'Logged in successfully!'
                        },
                        'message' : 'Success'
                    }
                    return returnObject
            #if any of those two fail, return error object
            else:
                returnObject = {
                    'code' : 401,
                    'data'  : {
                        'message' : 'Username or Password is wrong. Please try again!'
                    },
                    'message' : 'Failure'
                }
                return returnObject
    except PyMongoError as e:
        # Handle database-related errors
        client.close()
        #return the faiure object
        returnObject = {
                    'code' : 500,
                    'data'  : {
                        'message' : 'Database error: ' + str(e)
                    },
                    'message' : 'Failure'
                }
        return returnObject
    except Exception as e:
        # Handle other exceptions
        client.close()
        #return the faiure object
        returnObject = {
                    'code' : 500,
                    'data'  : {
                        'message' : 'Server error: ' + str(e)
                    },
                    'message' : 'Failure'
                }
        return returnObject

def passwordValidation(passwordFromDB, passwordFromRequest):
    #encode the password from request
    passwordFromRequest = passwordFromRequest.encode('utf-8')
    #use checkpw function to validate the two passwords and return a bool a value
    return bcrypt.checkpw(passwordFromRequest, passwordFromDB) 

#TODO: move in different files
#make utility functions
#make a standard object creation function

#register user
#route for register
@app.route('/api/register', methods=["POST"])
def register_user():
    #storing the request object
    object = request.json
    username = object['username']
    password = object['password']

    returnObject = addUser(username=username, password=encrypt(password))
    return jsonify(returnObject)

#add user to db
def addUser(username, password):
    try:
        # Connect to database
        client = MongoClient(MONGO_URI, tlsCAFile=ca)
        db = client[DB_NAME]
        #getting the collection
        usersCollection = db['Users']

        #check if the collection if empty of not -> to avoid the first user registration
        if len(list(usersCollection.find())) != 0:
            #checking for the username passed in the request, if already exists, return an object with an error
            if usersCollection.find_one({'username' : username}):
                returnObject = {
                    'code' : 409,
                    'data'  : {
                        'message' : 'User already exists'
                    },
                    'message' : 'Failure'
                }
                return returnObject
            
        #create a new user
        newUser = {
            'username' : username, 
            'password' : password,
        }

        #insert user in the users collection
        usersCollection.insert_one(newUser)
        client.close()
        #print acknowledgement      
        print('User added successfully!')
        #return the success object
        returnObject = {
                    'code' : 200,
                    'data'  : {
                        'message' : 'User added successfully!'
                    },
                    'message' : 'Success'
                }
        return returnObject
    except PyMongoError as e:
        # Handle database-related errors
        client.close()
        #return the faiure object
        returnObject = {
                    'code' : 500,
                    'data'  : {
                        'message' : 'Database error: ' + str(e)
                    },
                    'message' : 'Failure'
                }
        return returnObject
    except Exception as e:
        # Handle other exceptions
        client.close()
        #return the faiure object
        returnObject = {
                    'code' : 500,
                    'data'  : {
                        'message' : 'Server error: ' + str(e)
                    },
                    'message' : 'Failure'
                }
        return returnObject
    
def encrypt(text):
    # converting text to array of bytes
    bytes = text.encode('utf-8')
    # generating the salt
    salt = bcrypt.gensalt()
    # Hashing the text
    hash = bcrypt.hashpw(bytes, salt)
    return hash

        
# This method updates the database to reflect new available value of hardware
# when user checks in/checks out number of units specified by quantity
@app.route('/api/placeorder/<user_hw_request>', methods=['GET', 'POST'])
def handleResources(user_hw_request):
    data = getHWSet()
    db_hardware_sets = json.loads(data)

    # set hardwareSets variables
    capacity_hwSet1 = db_hardware_sets[0]['Capacity']
    capacity_hwSet2 = db_hardware_sets[1]['Capacity']
    availability_hwSet1 = db_hardware_sets[0]['Available']
    availability_hwSet2 = db_hardware_sets[1]['Available']
    checkedOut_hwSet1 = capacity_hwSet1 - availability_hwSet1
    checkedOut_hwSet2 = capacity_hwSet2 - availability_hwSet2
    
    type = user_hw_request['type']
    hw_new_data = {}

    # loop through user hardware request information
    for key, value in user_hw_request.items():
        if isinstance(value, dict) and "quantity" in value:
            # if hardware quantity is greater than 0, set variables for the hardware
            if value['quantity'] > 0:
                quantity = value['quantity']
                hwSet = key[-1]
                if hwSet == '1':
                    availability = availability_hwSet1
                    checkedOut = checkedOut_hwSet1
                elif hwSet == '2':
                    availability = availability_hwSet2
                    checkedOut = checkedOut_hwSet2

                # If user requests to check in, they can only check in hardware quantity that is 
                # less than or equal to checked out. Then add quantity to availability
                # If user requests to check out, they can only check out hardware quantity that is 
                # less than or equal to availability. Then subtract availability from quantity
                if type == "checkin":
                    if quantity <= int(checkedOut):
                        availability += quantity
                    else:
                        return err
                elif type == "checkout":
                    if quantity <= int(availability):
                        availability -= quantity
                    else:
                        return err 
                    
                # call method to update the database    
                updateDB(availability, hwSet)

                # update hw_new_data dictionary to return as a response
                hw_new_data.update( {f"HardwareSet{hwSet}": {"available": availability} })
    
    hw_new_data.update({"code": "Success"})
    return str(hw_new_data)

# This method updates the database with new Availability values
def updateDB(availability, hwSet):
    try:
        # Connect to database
        client = MongoClient(MONGO_URI, tlsCAFile=ca)
        db = client[DB_NAME]
        collection = db['Resources']

        # Update the 'Available' field
        newValues = { '$set': { 'Available': availability } }
        collection.update_one({'HardwareSet': hwSet}, newValues)

        # Close the database connection
        client.close()
    except PyMongoError as e:
        # Handle database-related errors
        client.close()
        return {'error': str(e)}
    except Exception as e:
        # Handle other exceptions
        client.close()
        return err

if __name__ == '__main__':
    app.run(debug=True)