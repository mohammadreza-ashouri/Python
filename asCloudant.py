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
      logging.error("cloudant:init Something unexpected has happend"+traceback.format_exc())
    self.databaseName = databaseName
    if self.databaseName in self.client.all_dbs():
      self.db = self.client[self.databaseName]
    else:
      self.db = self.client.create_database(self.databaseName)
    # check if default document exist and create
    if "-dataDictionary-" not in self.db:
      logging.warning("cloudant:init Data structure not defined. Use default one")
      dataDictionary = json.load(open("dataDictionary.json", 'r'))
      reply = self.db.create_document(dataDictionary)
    # check if default views exist and create them
    self.dataDictionary = self.db["-dataDictionary-"]
    res = cT.dataDictionary2DataLabels(self.dataDictionary)
    self.dataLabels = list(res['dataList'])
    self.hierarchyLabels = list(res['hierarchyList'])
    jsDefault = "if (doc.type=='$docType$' && !('current_rev' in doc)) {emit($key$, [$outputList$]);}"
    for docType, docLabel in self.dataLabels+self.hierarchyLabels:
      view = "view"+docLabel
      if "_design/"+view not in self.db:
        if docType=='project':
          jsString = jsDefault.replace('$docType$', docType).replace('$key$','doc._id')
        else:
          jsString = jsDefault.replace('$docType$', docType).replace('$key$','doc.inheritance[0]')
        outputList = []
        for item in self.dataDictionary[docType][docLabel]:
          key = list(item.keys())[0]
          if key == 'image':
            outputList.append('(doc.image.length>3).toString()')
          elif key == 'tags':
            outputList.append("doc.tags.join(' ')")
          else:
            outputList.append('doc.'+key)
        outputList = ','.join(outputList)
        jsString = jsString.replace('$outputList$', outputList)
        logging.warning("cloudant:init "+view+" not defined. Use default one:"+jsString)
        self.saveView(view, view, jsString)
    if "_design/viewHierarchy" not in self.db:
      jsString  = "if ('type' in doc && !('current_rev' in doc)) {\n"
      jsString += "if ('childNum' in doc) {emit(doc.inheritance[0], [doc.inheritance.join(' '),doc.childNum,doc.type,doc.name]);}\n"
      jsString += "else                   {emit(doc.inheritance[0], [doc.inheritance.join(' '),9999,doc.type,doc.name]);}\n"
      jsString += "}"
      jsString2 = "if ('path' in doc && !('current_rev' in doc)){\n"
      jsString2+= "if ('md5sum' in doc) {doc.path.forEach(function(thisPath) {emit(doc.inheritance[0], [thisPath,doc.type,doc.md5sum]);});}\n"
      jsString2+= "else                 {doc.path.forEach(function(thisPath) {emit(doc.inheritance[0], [thisPath,doc.type,'']);});}\n"
      jsString2+= "}"
      self.saveView('viewHierarchy','.',{"viewHierarchy":jsString,"viewPaths":jsString2})
    if "_design/viewMD5" not in self.db:
      self.saveView('viewMD5','viewMD5',"if (doc.type==='measurement' && !('current_rev' in doc)){emit(doc.md5sum, doc.name);}")
    if "_design/viewQR" not in self.db:
      jsString = "if (doc.qr_code.length > 0 && !('current_rev' in doc))"
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
    Wrapper for get from database function

    Args:
        id: document id
    """
    return self.db[id]


  def saveDoc(self, doc):
    """
    Wrapper for save to database function

    Args:
        doc: document to save
    """
    res = self.db.create_document(doc)
    return res


  def updateDoc(self, change, docID):
    """
    Update document by
    - saving changes to oldDoc (revision document)
    - updating new-document concurrently
    - create a docID for oldDoc
    - save this docID in list of revisions stored in new-document
    - Bonus: save "_rev" from newDoc to oldDoc in order to track that updates cannot happen by accident

    Args:
        change: dictionary of item to update
                'path' = list: new path list is appended to existing list
                'path' = str : remove this path from path list
        docID:  id of document to change
    """
    newDoc = self.db[docID]  #this is the document that stays live
    oldDoc = {}              #this is an older revision of the document
    nothingChanged = True
    for item in change:
      if item in ['revisions','_id','_rev']:                         #skip items cannot come from change
        continue
      if item=='inheritance' and len(change['inheritance'])==0:      #skip non-set inheritance
        continue
      if item=='type' and change['type']=='--':                      #skip non-set type
        continue
      if item=='path' and change['path'][0] in newDoc['path']:       #skip if new path already in path
        continue
      if change[item]!=newDoc[item]:
        if item!='date':      #if only date change, no real change
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
      logging.warning("cloudant:updateDoc no change of content compared to DB")
      return newDoc

    #produce _id of revDoc
    if len(newDoc['revisions']) > 0:  #if revisions of document exist
      lastID = newDoc['revisions'][-1].split('-')
      oldDoc['_id'] = '-'.join(lastID[:-1])+'-'+str(int(lastID[-1])+1)
    else:                             #if initial document: no copy
      oldDoc['_id'] = docID+'-0'

    #add id to revisions and save
    newDoc['revisions'] = newDoc['revisions']+[oldDoc['_id']]
    newDoc.save()

    #save _rev to backup for verification
    oldDoc['current_rev'] = newDoc['_rev']
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
      logging.error("cloudant:saveView Something unexpected has happend"+traceback.format_exc())
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
    logging.info("cloudant:replicateDB Replication started")
    return
