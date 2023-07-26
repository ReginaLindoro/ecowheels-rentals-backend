#File with function to return client on command instead of calling every time
def getClient():
    import pymongo
    from pymongo.mongo_client import MongoClient
    from pymongo.server_api import ServerApi


    uri = "mongodb+srv://ADAP:ADAP@adapdb.g2igjno.mongodb.net/?retryWrites=true&w=majority"

    # Create a new client and connect to the server
    client = MongoClient(uri, server_api=ServerApi('1'))

    # Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)



    client = pymongo.MongoClient("mongodb+srv://ADAP:ADAP@adapdb.g2igjno.mongodb.net/?retryWrites=true&w=majority")
    return client
    


