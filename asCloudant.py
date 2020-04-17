"""Class for interaction with couchDB
"""
import traceback, json, logging
from cloudant.client import CouchDB, Cloudant
from cloudant.document import Document
from cloudant.view import View
from cloudant.design_document import DesignDocument
from cloudant.replicator import Replicator
from commonTools import commonTools as cT


class Database:
  """
  Class for interaction with couchDB
  """

  def __init__(self, user, password, databaseName):
    """
    Args:
        user: user name to local database
        password: password to local database
        databaseName: local database name
    """
    try:
      self.client = CouchDB(user, password, url='http://127.0.0.1:5984', connect=True)
    except Exception:
      logging.error("Something unexpected has happend"+traceback.format_exc())
    self.databaseName = databaseName
    if self.databaseName in self.client.all_dbs():
      self.db = self.client[self.databaseName]
    else:
      self.db = self.client.create_database(self.databaseName)
    # check if default document exist and create
    if "-dataDictionary-" not in self.db:
      logging.warning("**WARNING** Data structure not defined. Use default one")
      dataDictionary = json.load(open("dataDictionary.json", 'r'))
      reply = self.db.create_document(dataDictionary)
    # check if default views exist and create them
    self.dataDictionary = self.db["-dataDictionary-"]
    res = cT.dataDictionary2DataLabels(self.dataDictionary)
    self.dataLabels = list(res['dataList'])
    self.hierarchyLabels = list(res['hierarchyList'])
    jsDefault = "if ('type' in doc && doc.type=='$docType$') {emit($key$, [$outputList$]);}"
    for docType, docLabel in self.dataLabels+self.hierarchyLabels:
      view = "view"+docLabel
      if "_design/"+view not in self.db:
        if docType=='project':
          jsString = jsDefault.replace('$docType$', docType).replace('$key$','doc._id')
        else:
          jsString = jsDefault.replace('$docType$', docType).replace('$key$','doc.inheritance[0]')
        outputList = []
        for item in self.dataDictionary[docType][0][docLabel]:
          key = list(item.keys())[0]
          if key == 'image':
            outputList.append('(doc.image.length>3).toString()')
          elif key == 'tags':
            outputList.append("doc.tags.join(' ')")
          else:
            outputList.append('doc.'+key)
        outputList = ','.join(outputList)
        jsString = jsString.replace('$outputList$', outputList)
        logging.warning("**WARNING** "+view+" not defined. Use default one:"+jsString)
        self.saveView(view, view, jsString)
    if "_design/viewHierarchy" not in self.db:
      jsString  = "if ('type' in doc) {\n"
      jsString += "if ('childNum' in doc)    {emit(doc.inheritance[0], [doc.inheritance.join(' '),doc.childNum,doc.type,doc.name]);}\n"
      jsString += "else {emit(doc.inheritance[0], [doc.inheritance.join(' '),9999,doc.type,doc.name]);}\n"
      jsString += "}"
      jsString2 = "if ('path' in doc){\n"
      jsString2+= "if ('md5sum' in doc) {doc.path.forEach(function(thisPath) {emit(doc.inheritance[0], [thisPath,doc.type,doc.md5sum]);});}\n"
      jsString2+= "else                 {doc.path.forEach(function(thisPath) {emit(doc.inheritance[0], [thisPath,doc.type,'']);});}\n"
      jsString2+= "}"
      self.saveView('viewHierarchy','.',{"viewHierarchy":jsString,"viewPaths":jsString2})
    if "_design/viewMD5" not in self.db:
      self.saveView('viewMD5','viewMD5',"if ('type' in doc && doc.type==='measurement'){emit(doc.md5sum, doc.name);}")
    if "_design/viewQR" not in self.db:
      jsString = "if ('type' in doc && doc.type === 'sample' && doc.qr_code[0] !== '')"
      jsString+=   "{doc.qr_code.forEach(function(thisCode) {emit(thisCode, doc.name);});}"
      self.saveView('viewQR','viewQR', jsString )
    return


  def exit(self, deleteDB=False):
    """
    Shutting down things

    Args:
      deleteDB: remove database
    """
    if deleteDB:
      self.db.client.delete_database(self.databaseName)
    return


  def getDoc(self, id):
    """
    Wrapper for get function

    Args:
        id: document id
    """
    return self.db[id]


  def saveDoc(self, doc):
    """
    Wrapper for save function

    Args:
        doc: document to save
    """
    res = self.db.create_document(doc)
    return res


  def updateDoc(self, change, docID):
    """
    Update document by
    - saving changes to revDoc (revision document)
    - updating document concurrently
    - create a docID for revision document
    - save this docID also in list of revisions
    - Bonus: save "_rev" to revDoc in order to track that updates cannot happen by accident

    Args:
        change: updated items: TODO exaplain path
        docID:  id of document to change
    """
    newDoc = self.db[docID]  #this is the document that stays live
    oldDoc = {}              #this is an older revision of the document
    nothingChanged = True
    for item in change:
      if item in ['type','revisions','inheritance','_id','_rev']:    #skip items cannot come from change
        continue
      if change[item]!=newDoc[item]:
        nothingChanged = False
        if item in ['path']:
          if isinstance(change[item], list): #append to existing
            oldDoc[item] = newDoc[item].copy()
            newDoc[item]+= change[item]
          else:                              #remove from existing
            oldDoc[item] = newDoc[item].copy()
            newDoc[item] = [directory for directory in newDoc[item] if directory!=change[item]]
        else:                         #replace existing
          oldDoc[item] = newDoc[item]
          newDoc[item] = change[item]
    if nothingChanged:
      logging.warning("asCloudant:update content the same on DB")
      return newDoc
    #produce _id of revDoc
    idParts = docID.split('-')
    if len(idParts)==2:   #if initial document: no copy
      oldDoc['_id'] = docID+'-0'
    else:                 #if revisions of document exist
      oldDoc['_id'] = '-'.join(idParts[:-1])+'-'+str(int(idParts[-1])+1)
    #add id to revisions and save
    if newDoc['revisions']==['']:
      newDoc['revisions'] = [oldDoc['_id']]
    else:
      newDoc['revisions'] = newDoc['revisions']+[oldDoc['_id']]
    newDoc.save()
    oldDoc['revisionCurrent'] = newDoc['_rev']
    res = self.db.create_document(oldDoc)
    return newDoc


  def getView(self, thePath, key=None):
    """
    Wrapper for getting view function

    Args:
        thePath: path to view
        key: if given, use to filter output
    """
    thePath = thePath.split('/')
    designDoc = self.db.get_design_document(thePath[0])
    v = View(designDoc, thePath[1])
    if key is None:
      return list(v.result)
    else:
      return v(key=key)['rows']


  def saveView(self, designName, viewName, jsCode):
    """
    Adopt the view by defining a new jsCode

    Args:
        designName: name of the design
        viewName: name of the view (ignored if jsCode==dictionary)
        jsCode: new code (string or dict of multiple)
    """
    designDoc = DesignDocument(self.db, designName)
    if isinstance(jsCode, str):
      thisJsCode = "function (doc) {" + jsCode + "}"
      designDoc.add_view(viewName, thisJsCode)
    elif isinstance(jsCode, dict):
      for view in jsCode:
        thisJsCode = "function (doc) {" + jsCode[view] + "}"
        designDoc.add_view(view, thisJsCode)
    try:
      designDoc.save()
    except Exception:
      logging.error("Something unexpected has happend"+traceback.format_exc())
    return


  def replicateDB(self, dbInfo, removeAtStart=False):
    """
    Replication to another instance

    Args:
        dbInfo: info on the remote database
        removeAtStart: remove remote DB before starting new
    """
    rep = Replicator(self.client)
    client2 = Cloudant(dbInfo['user'], dbInfo['password'], url=dbInfo['url'], connect=True)
    if dbInfo['database'] in client2.all_dbs() and removeAtStart:
        client2.delete_database(dbInfo['database'])
    if dbInfo['database'] in client2.all_dbs():
      db2 = client2[dbInfo['database']]
    else:
      db2 = client2.create_database(dbInfo['database'])
    doc = rep.create_replication(self.db, db2, create_target=True)
    logging.info("Should have been replicated!")
    return
