import couchdb, traceback, json
from commonTools import commonTools as cT

class Database:
  """ Class for interaction with couchDB
  """
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

    ## check if default document exist
    if "-dataDictionary-" not in self.db:
      print("**WARNING** Data structure not defined. Use default one")
      dataDictionary = json.load(open("dataDictionary.json",'r'))
      reply = self.db.save(dataDictionary)
      
    ## check if default views exist #TODO later: Generate from data_dictionary
    ### Old version
    #jsProject = "if (doc.type && doc.type=='project')   {emit(doc.name, [doc.status,doc.objective,doc.tags.length]);}"
    #     if (doc.type && (doc.type=='project'||doc.type=='step'||doc.type=='task')) {emit(doc.project, [doc.type,doc.name,doc.childs]);}
    #function (doc) {\nif (doc.type && (doc.type=='step'||doc.type=='task')) {emit(doc.project, [doc.type,doc.name,doc.childs]);}if (doc.type && doc.type=='project') {emit(doc._id, [doc.type,doc.name,doc.childs]);}\n}
    jsProject= {"viewProjects": {"map": "function (doc) {\nif (doc.type && doc.type=='project') {emit(doc.name, [doc.status,doc.objective,doc.tags.length]);}\n}"},
                "viewHierarchy":{"map": "function (doc) {\nif (doc.type && (doc.type=='project'||doc.type=='step'||doc.type=='task')) {emit(doc.project, [doc.type,doc.name,doc.childs]);}\n}"} }
    jsMeasurement= "if (doc.type && doc.type=='measurement'){emit(doc.project, [doc.name,doc.alias,doc.comment,doc.image.length>3]);}"
    jsProcedure="if (doc.type && doc.type=='procedure') {emit(doc.project, [doc.name,doc.content]);}"    
    jsSample  = "if (doc.type && doc.type=='sample')    {emit(doc.project, [doc.name,doc.chemistry,doc.comment,doc.qr_code!='']);}"
    jsDefault = "if (doc.type && doc.type=='$docType$') {emit(doc.project, doc.name);}"
    doc = self.db.get("-dataDictionary-")
    typeLabels = cT.dataDictionary2Labels(doc)
    for dataType,dataLabel in typeLabels:
      view = "view"+dataLabel
      if "_design/"+view not in self.db:
        print("**WARNING** "+view+" not defined. Use default one")
        if dataType=='project':
          self.saveView(view,view,jsProject)
        elif dataType=='measurement':
          self.saveView(view,view,jsMeasurement)
        elif dataType=='procedure':
          self.saveView(view,view,jsProcedure)
        elif dataType=='sample':
          self.saveView(view,view,jsSample)
        else:
          self.saveView(view,view,jsDefault.replace('$docType$',dataType))
    return


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


  def getView(self,thePath, key=None):
    """
    Wrapper for getting view function
    """
    if key== None:
      return self.db.view(thePath)
    else:
      return self.db.view(thePath, key=key)


  def saveView(self,designName, viewName, jsCode):
    """
    Adopt the view by defining a new jsCode

    Args:
       designName: name of the design
       viewName: name of the view
       jsCode: new code
    """
    if isinstance(jsCode, str):
      jsCode = "function (doc) {\n" + jsCode +"\n}"
      doc = {"_id": "_design/"+designName, "views": { viewName: {
        "map": ""
        } }, "language": "javascript" }
      doc["views"][viewName]['map'] = jsCode
    elif isinstance(jsCode, dict):
      doc = {"_id": "_design/"+designName, "language": "javascript" }
      doc['views'] = jsCode
    try:
      id_, rev_ = self.db.save(doc)
    except Exception:
      doc = self.db.get("_design/"+designName)
      doc["views"][viewName]['map'] = jsCode
      id_, rev_ = self.db.save(doc)
    return
