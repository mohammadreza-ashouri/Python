import couchdb, traceback

class Database:

  def __init__(self, user, password, databaseName):
    couch = couchdb.Server("http://"+user+":"+password+"@localhost:5984/")
    try:
      self.db = couch[databaseName]
    except Exception:
      outString = traceback.format_exc().split("\n")
      if outString[-2]=="couchdb.http.ResourceNotFound":
          print("Database did not exist. Create it.")
          self.db = couch.create(databaseName)
      else:
          print("Something unexpected has happend")
          print("\n".join(outString))
          self.db = None
    if not "-hierarchyRoot-" in self.db:  #create root
        self.db.save( {"_id":"-hierarchyRoot-", "childs":[],"name":"root","type":""} )
    if not "-dataDictionary-" in self.db:
      print("**ERROR** Data structure not defined. Use default one")
      dataDictionary = json.load(open("dataDictionary.json",'r'))
      reply = self.db.save(dataDictionary)
    if not "-userInterface-" in self.db:
      print("**ERROR** User interaction not defined. Use default one")
      dataDictionary = json.load(open("userInterface.json",'r'))
      reply = self.db.save(dataDictionary)


  def get(self,id):
    """
    Wrapper for get function
    """
    return self.db.get(id)


  def save(self,doc):
    """
    Wrapper for save function
    """
    return self.db.save(doc)


  def getView(self,thePath):
    """
    Wrapper for getting view function
    """
    return self.db.view(thePath)


  def setView(self,designName, viewName, jsCode):
    """
    Adopt the view by defining a new jsCode

    Args:
       designName: name of the design
       viewName: name of the view
       jsCode: new code
    """
    jsCode = "function (doc) {\n" + jsCode +"\n}"
    doc = {"_id": "_design/"+designName, "views": { viewName: {
      "map": ""
      } }, "language": "javascript" }
    doc["views"]['viewMeasurements']['map'] = jsCode
    try:
      id_, rev_ = self.db.save(jsonObj)
    except Exception:
      doc = self.db.get("_design/viewMeasurements")
      doc["views"]['viewMeasurements']['map'] = jsCode
      id_, rev_ = self.db.save(doc)
    return