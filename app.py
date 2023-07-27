# app.py
from flask import Flask, jsonify, request
from pymongo import MongoClient
import bson.json_util as json_util
import certifi
import json

app = Flask(__name__)

ca = certifi.where()

#TODO: take configurations outside
# MongoDB configuration
MONGO_URI = 'mongodb+srv://{DB_USER}:{DB_USER_PASS}@adapdb.g2igjno.mongodb.net/?retryWrites=true&w=majority'
DB_NAME = 'ADAPdb'
DB_USER = 'ADAP'
DB_USER_PASS = 'ADAP'

# Connect to database
client = MongoClient(MONGO_URI, tlsCAFile=ca)
db = client[DB_NAME]
collection = db['Resources']

# This method gets hardware information from the database
def getHWSet():
    hwSetData = collection.find()
    return json_util.dumps(hwSetData)
        
# This method updates the database to reflect new available value of hardware
# when user checks in/checks out number of units specified by quantity
@app.route('/placeorder/<user_hw_request>', methods=['POST'])
def handleResources(user_hw_request):
    # user_hw_request = { #for testing. remove
    #     "hardwareSet1": {
    #         "quantity": 5
    #     },
    #     "hardwareSet2": {
    #         "quantity": 5
    #     },
    #     "type": "checkout"
    # }
    type = user_hw_request['type']
    err = {
        "error": {
            "code":100,
            "message": "Error!"
        }
    }

    data = getHWSet()
    db_hardware_sets = json.loads(data)
    # set hardwareSets variables
    capacity_hwSet1 = db_hardware_sets[0]['Capacity']
    capacity_hwSet2 = db_hardware_sets[1]['Capacity']
    availability_hwSet1 = db_hardware_sets[0]['Available']
    availability_hwSet2 = db_hardware_sets[1]['Available']
    checkedOut_hwSet1 = capacity_hwSet1 - availability_hwSet1
    checkedOut_hwSet2 = capacity_hwSet2 - availability_hwSet2

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
    
    return 'Success' 

# This method updates the database with new Availability values
def updateDB(availability, hwSet):
    try:
        newValues = { '$set': { 'Available': availability } }
        inserted_data = collection.update_one({'HardwareSet': hwSet}, newValues)
        return str(inserted_data)
    except:
        print("An exception occurred :", e)
        return e

if __name__ == '__main__':
    app.run(debug=True)