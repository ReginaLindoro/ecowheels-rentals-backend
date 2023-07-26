




def createProject(ID, Name, Desc, Client):
    projectDocument = {
        "ProjectID":ID,
        "Name":Name,
        "Description":Desc}

    projects = Client.Projects

    projects.insert_one(projectDocument)

    
    


def checkHWsets(client):
    resources = client.Resources

    mydoc = resources.find({},{"HardwareSet":1, "Capacity":2, "_id":0})

    print("\nList of Resources \n--------------------------")
    for x in mydoc:
        print(x)




def checkInOut(hwSet, Amount, InOut, client):
    resources = client.Resources

    mydoc = resources.find_one({"HardwareSet":hwSet},{"HardwareSet":1, "Capacity":2, "Available":3, "_id":0})

    print("\nList of Resources Before Check-In/Out\n--------------------------")
    for x in mydoc:
        print(x, ": ", mydoc[x])
        
    #Value holder for check in/out (0 = out, 1 = in)\
    if InOut == 1:
        if (mydoc['Capacity']) < (mydoc['Available'] + Amount):
            print("-----ERROR-----")
            print("Cannot check in more than its total capacity\n")

            newValue = mydoc['Capacity'] - mydoc['Available']
            print("Only able to check-in ", newValue)            

            resources.updateOne({"HardwareSet": hwSet}, {$inc:{"Available": 5}})

            print("New Available: ", mydoc['Available'])
            
    
def main():
    import pymongo
    
    #Client call
    from dbClient import getClient
    client = getClient()

    #making calls for collections
    db = client.ADAPdb
    projects = db.Projects
    resources = db.Resources
    users = db.Users


    #Example of create function   
    """createProject("99","Function","Will it or will it not?",db)"""

    #example of query and feeding into mongo FIND function
    myquery = { "ProjectID": "99" }

    mydoc = projects.find(myquery)
    

    print("\nList of Projects \n--------------------------")
    for x in mydoc:
      print(x)

    
    #
    checkHWsets(db)

    #Check values for check in/out function
    #set hwSet value to string so can match db
    testHolder = 1
    checkInOut(str(testHolder), 505050, 1, db)


main()
