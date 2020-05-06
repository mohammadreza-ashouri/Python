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
      jsHierarchy  = '''
        if ('type' in doc && !('current_rev' in doc)) {
          doc.branch.forEach(function(branch) {emit(branch.stack.concat([doc._id]).join(' '),[branch.child,doc.type,doc.name]);});
        }
      '''
      jsPath = '''
        if ('branch' in doc && !('current_rev' in doc)){
          if (doc.type === 'project') {emit(doc._id,[doc.branch[0].path,doc.type,'']);}
          else if ('md5sum' in doc){doc.branch.forEach(function(branch){if(branch.path){emit(branch.stack[0],[branch.path,doc.type,doc.md5sum]);}});}
          else                     {doc.branch.forEach(function(branch){if(branch.path){emit(branch.stack[0],[branch.path,doc.type,''        ]);}});}
        }
      '''
      self.saveView('viewHierarchy','.',{"viewHierarchy":jsHierarchy,"viewPaths":jsPath})
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
    #TODO temporary:
    if 'path' in doc or 'inheritance' in doc or 'childNum' in doc:
      print("OLD VERSION saveDoc")
      aa = 4/0
    tracebackString = traceback.format_stack()
    tracebackString = '|'.join([item.split('\n')[1].strip() for item in tracebackString[:-1]])  #| separated list of stack excluding last
    doc['client'] = tracebackString
    del doc['branch']['op']  #remove operation, saveDoc creates and therefore always the same
    doc['branch'] = [doc['branch']]
    res = self.db.create_document(doc)
    return res


  def updateDoc(self, change, docID, callback):
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
        callback: function to move directory if paths suggest that
    """
    #TODO temporary:
    if 'path' in change or 'inheritance' in change or 'childNum' in change:
      print("OLD VERSION updateDoc")
    tracebackString = traceback.format_stack()
    tracebackString = '|'.join([item.split('\n')[1].strip() for item in tracebackString[:-1]])  #| separated list of stack excluding last
    change['client'] = tracebackString
    newDoc = self.db[docID]  #this is the document that stays live
    oldDoc = {}              #this is an older revision of the document
    nothingChanged = True
    # handle branch
    if 'branch' in change and len(change['branch']['stack'])>0:
      op = change['branch']['op']
      del change['branch']['op']
      if not change['branch'] in newDoc['branch']:       #skip if new path already in path
        nothingChanged = False
        oldDoc['branch'] = newDoc['branch'].copy()
        if op=='c':    #create, append
          newDoc['branch'] += [change['branch']]
        elif op=='u':  #update=remove current at zero
          newDoc['branch'][0] = change['branch']
        elif op=='d':  #delete
          aa = 4/0
          newDoc['branch'] = [directory for directory in newDoc['branch'] if directory!=change['branch'][0]]
        else:
          print("I should not be here")
          a = 4/0
    #handle other items
    for item in change:
      if item in ['revisions','_id','_rev','branch']:                #skip items cannot come from change
        continue
      if item=='type' and change['type']=='--':                      #skip non-set type
        continue
      if change[item]!=newDoc[item]:
        if item!='date':      #if only date change, no real change
          nothingChanged = False
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
      res = list(v.result)
      return res
    else:
      res = v(startkey=key, endkey=key+' zz')['rows']
      return res


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
