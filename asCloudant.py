import traceback, json
from cloudant.client import CouchDB, Cloudant
from cloudant.view import View
from cloudant.design_document import DesignDocument
from cloudant.replicator import Replicator
from commonTools import commonTools as cT


class Database:
  """ Class for interaction with couchDB
  """
  def __init__(self, user, password, databaseName):
    try:
      self.client = CouchDB(user,password,url='http://127.0.0.1:5984',connect=True)
      self.db = self.client[databaseName]
    except Exception:
      print("Something unexpected has happend")
      print(traceback.format_exc())
      self.db = None

    ## check if default document exist
    if "-dataDictionary-" not in self.db:
      print("**WARNING** Data structure not defined. Use default one")
      dataDictionary = json.load(open("dataDictionary.json",'r'))
      reply = self.db.create_document(dataDictionary)
      
    ## check if default views exist #TODO later: Generate from data_dictionary
    ### Old version
    #jsProject = "if (doc.type && doc.type=='project')   {emit(doc.name, [doc.status,doc.objective,doc.tags.length]);}"
    #     if (doc.type && (doc.type=='project'||doc.type=='step'||doc.type=='task')) {emit(doc.project, [doc.type,doc.name,doc.childs]);}
    #function (doc) {\nif (doc.type && (doc.type=='step'||doc.type=='task')) {emit(doc.project, [doc.type,doc.name,doc.childs]);}if (doc.type && doc.type=='project') {emit(doc._id, [doc.type,doc.name,doc.childs]);}\n}
    jsProject= {"viewProjects": "if (doc.type && doc.type=='project') {emit(doc.name, [doc.status,doc.objective,doc.tags.length]);}",
                "viewHierarchy":"if (doc.type && (doc.type=='project'||doc.type=='step'||doc.type=='task')) {emit(doc.project, [doc.type,doc.name,doc.childs]);}" }
    jsMeasurement= "if (doc.type && doc.type=='measurement'){emit(doc.project, [doc.name,doc.alias,doc.comment,doc.image.length>3]);}"
    jsProcedure="if (doc.type && doc.type=='procedure') {emit(doc.project, [doc.name,doc.content]);}"    
    jsSample  = "if (doc.type && doc.type=='sample')    {emit(doc.project, [doc.name,doc.chemistry,doc.comment,doc.qr_code!='']);}"
    jsDefault = "if (doc.type && doc.type=='$docType$') {emit(doc.project, doc.name);}"
    doc = self.db["-dataDictionary-"]
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
    return self.db[id]


  def saveDoc(self,doc):
    """
    Wrapper for save function
    """
    res = self.db.create_document(doc)
    return (res['_id'], res['_rev'])


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
    thePath = thePath.split('/')
    designDoc = self.db.get_design_document(thePath[0])
    v = View(designDoc,thePath[1])
    if key== None:
      return list(v.result)
    else:
      return v(key=key)['rows']


  def saveView(self,designName, viewName, jsCode):
    """
    Adopt the view by defining a new jsCode

    Args:
       designName: name of the design
       viewName: name of the view
       jsCode: new code
    """
    designDoc = DesignDocument(self.db,designName)
    if isinstance(jsCode, str):
      thisJsCode = "function (doc) {" + jsCode +"}"
      designDoc.add_view(viewName,thisJsCode)
    elif isinstance(jsCode, dict):
      for view in jsCode:
        thisJsCode =  "function (doc) {" + jsCode[view] +"}"
        designDoc.add_view(view,thisJsCode)
    try:
      designDoc.save()
    except Exception:
      print("Something unexpected has happend")
      print(traceback.format_exc())
    return


  def replicateDB(self,dbInfo):
    """
    Replication to another instance
    """
    rep = Replicator(self.client)
    client2 = Cloudant(dbInfo['user'], dbInfo['password'], url=dbInfo['url'], connect=True)
    db2 = client2[dbInfo['database']]
    doc = rep.create_replication(self.db, db2)
    print("**INFORMATION** Should be replicated!")
    return
