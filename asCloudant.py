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
    if self.databaseName in self.client:
      self.db = self.client[self.databaseName]
    else:
      self.db = self.client.create_database(self.databaseName)
    # check if default document exist and create
    if "-dataDictionary-" not in self.db:
      logging.warning("**WARNING** Data structure not defined. Use default one")
      dataDictionary = json.load(open("dataDictionary.json", 'r'))
      reply = self.db.create_document(dataDictionary)
    # check if default views exist and create them
    jsDefault = "if ('type' in doc && doc.type=='$docType$') {emit($key$, [$outputList$]);}"
    self.dataDictionary = self.db["-dataDictionary-"]
    res = cT.dataDictionary2DataLabels(self.dataDictionary)
    self.dataLabels = list(res['dataList'])
    self.hierarchyLabels = list(res['hierarchyList'])
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
    jsString  = "if ('type' in doc) {\n"
    jsString += "if (doc.type==='project') {emit(doc._id, [doc.inheritance.join(' '),9999,doc.type,doc.name]);}\n"
    jsString += "else if ('childNum' in doc)    {emit(doc.inheritance[0], [doc.inheritance.join(' '),doc.childNum,doc.type,doc.name]);}\n"
    jsString += "else {emit(doc.inheritance[0], [doc.inheritance.join(' '),9999,doc.type,doc.name]);}\n"
    jsString += "}"
    self.saveView('viewHierarchy','viewHierarchy',jsString)
    self.saveView('viewMD5','viewMD5',"if ('type' in doc && doc.type==='measurement'){emit(doc.md5sum, doc.name);}")
    self.saveView('viewQR','viewQR',  "if ('type' in doc && doc.type === 'sample' && doc.qr_code[0] !== '') {doc.qr_code.forEach(function (thisCode) {emit(thisCode, doc.name);});}")
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
    return (res['_id'], res['_rev'])


  def updateDoc(self, change, docID):
    """
    Update document by
    - saving changes to revDoc (revision document)
    - updating document concurrently
    - create a docID for revision document
    - save this docID also in list of revisions
    - Bonus: save "_rev" to revDoc in order to track that updates cannot happen by accident

    Args:
        change: updated items
        docID:  id of document to change
    """
    doc = self.db[docID]
    revDoc = {}
    for item in change:
      if item in ['type','revisions','inheritance','_id','_rev']:    #remove items cannot come from change
        continue
      if change[item]!=doc[item]:
        revDoc[item] = doc[item]
        doc[item]    = change[item]
    #produce _id of revDoc
    idParts = docID.split('-')
    if len(idParts)==2:   #if initial document: no copy
      revDoc['_id'] = docID+'-0'
    else:                 #if revisions of document exist
      revDoc['_id'] = '-'.join(idParts[:-1])+'-'+str(int(idParts[-1])+1)
    #add id to revisions and save
    if doc['revisions']==['']:
      doc['revisions'] = [revDoc['_id']]
    else:
      doc['revisions'] = doc['revisions']+[revDoc['_id']]
    doc.save()
    revDoc['revisionCurrent'] = doc['_rev']
    res = self.db.create_document(revDoc)
    return doc['_id'], doc['_rev']


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
        viewName: name of the view
        jsCode: new code
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
