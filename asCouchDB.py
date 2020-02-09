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
    ## check if default documents exist
    if "-hierarchyRoot-" not in self.db:  #create root
        self.db.save( {"_id":"-hierarchyRoot-", "childs":[],"name":"root","type":"root"} )
    if "-dataDictionary-" not in self.db:
      print("**ERROR** Data structure not defined. Use default one")
      dataDictionary = json.load(open("dataDictionary.json",'r'))
      reply = self.db.save(dataDictionary)
    if "-userInterface-" not in self.db:
      print("**ERROR** User interaction not defined. Use default one")
      dataDictionary = json.load(open("userInterface.json",'r'))
      reply = self.db.save(dataDictionary)
    ## check if default views exist
    jsCode = "if (doc.type && doc.type=='$docType$') {\n    emit(doc._id, doc.name);\n  }"
    if "_design/viewMeasurements" not in self.db:
      print("**ERROR** Measurement view not defined. Use default one")
      self.setView("viewMeasurements","viewMeasurements",jsCode.replace('$docType$','measurement'))
    if "_design/viewSamples" not in self.db:
      print("**ERROR** Samples view not defined. Use default one")
      self.setView("viewSamples","viewSamples",jsCode.replace('$docType$','sample'))
    if "_design/viewProcedures" not in self.db:
      print("**ERROR** Procedure view not defined. Use default one")
      self.setView("viewProcedures","viewProcedures",jsCode.replace('$docType$','procedure'))
    if "_design/viewHierarchy" not in self.db:
      print("**ERROR** Hierarchy view not defined. Use default one")
      self.setView("viewHierarchy","viewHierarchy","if (doc.type) {\n emit(doc._id, doc.childs);\n }")


  def getDoc(self,id):
    """
    Wrapper for get function
    """
    return self.db.get(id)


  def saveDoc(self,doc):
    """
    Wrapper for save function
    """
    return self.db.save(doc)


  def updateDoc(self,doc):
    """
    Wrapper for update
    """
    self.db[doc.id] = doc
    return


  def getView(self,thePath):
    """
    Wrapper for getting view function
    """
    return self.db.view(thePath)


  def saveView(self,designName, viewName, jsCode):
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
    doc["views"][viewName]['map'] = jsCode
    try:
      id_, rev_ = self.db.save(doc)
    except Exception:
      doc = self.db.get("_design/"+designName)
      doc["views"][viewName]['map'] = jsCode
      id_, rev_ = self.db.save(doc)
    return
