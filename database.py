"""Class for interaction with couchDB
"""
import traceback, json, logging, os, warnings
from cloudant.client import CouchDB, Cloudant
from cloudant.document import Document
from cloudant.view import View
from cloudant.design_document import DesignDocument
from cloudant.replicator import Replicator
from pprint import pprint
from miscTools import bcolors
from commonTools import commonTools as cT

class Database:
  """
  Class for interaction with couchDB
  """

  def __init__(self, user, password, databaseName, confirm):
    """
    Args:
        user: user name to local database
        password: password to local database
        databaseName: local database name
        confirm: confirm changes to database and file-tree
    """
    self.confirm = confirm
    try:
      self.client = CouchDB(user, password, url='http://127.0.0.1:5984', connect=True)
    except Exception:
      logging.error('database:init Something unexpected has happend\n'+traceback.format_exc())
      print('database:init Something unexpected has happend\n'+traceback.format_exc())
      exit()
    self.databaseName = databaseName
    if self.databaseName in self.client.all_dbs():
      self.db = self.client[self.databaseName]
    else:
      self.db = self.client.create_database(self.databaseName)
    # check if default document exist and create
    if '-dataDictionary-' not in self.db:
      logging.info('database:init Data structure not defined. Use default one')
      with open('dataDictionary.json', 'r') as fIn:
        dataDictionary = json.load(fIn)
      reply = self.db.create_document(dataDictionary)
    # check if default views exist and create them
    self.dataDictionary = self.db['-dataDictionary-']
    res = cT.dataDictionary2DataLabels(self.dataDictionary)
    self.dataLabels = list(res['dataList'])
    self.hierarchyLabels = list(res['hierarchyList'])
    jsDefault = "if ($docType$ && !('current_rev' in doc)) {emit($key$, [$outputList$]);}"
    for docType, docLabel in self.dataLabels+self.hierarchyLabels:
      view = 'view'+docLabel
      if '_design/'+view not in self.db:
        if docType=='project':
          jsString = jsDefault.replace('$docType$', "doc.type[1]=='"+docType+"'").replace('$key$','doc._id')
        else:     #only show first instance in list doc.branch[0]
          jsString = jsDefault.replace('$docType$', "doc.type[0]=='"+docType+"'").replace('$key$','doc.branch[0].stack[0]')
        outputList = []
        for item in self.dataDictionary[docType]['default']:
          if item['name'] == 'image':
            outputList.append('(doc.image.length>3).toString()')
          elif item['name'] == 'tags':
            outputList.append('doc.tags.join(' ')')
          elif item['name'] == 'type':
            outputList.append('doc.type.slice(1).join("/")')
          elif item['name'] == 'content':
            outputList.append('doc.content.slice(0,100)')
          else:
            outputList.append('doc.'+item['name'])
        outputList = ','.join(outputList)
        jsString = jsString.replace('$outputList$', outputList)
        logging.info('database:init '+view+' not defined. Use default one:'+jsString)
        self.saveView(view, view, jsString)
    if '_design/viewHierarchy' not in self.db:
      jsHierarchy  = '''
        if ('type' in doc && !('current_rev' in doc)) {
          doc.branch.forEach(function(branch) {emit(branch.stack.concat([doc._id]).join(' '),[branch.child,doc.type,doc.name]);});
        }
      '''
      jsPath = '''
        if ('branch' in doc && !('current_rev' in doc)){
          if ('md5sum' in doc){doc.branch.forEach(function(branch){if(branch.path){emit(branch.path,[branch.stack,doc.type,branch.child,doc.md5sum]);}});}
          else                {doc.branch.forEach(function(branch){if(branch.path){emit(branch.path,[branch.stack,doc.type,branch.child,''        ]);}});}
        }
      '''
      self.saveView('viewHierarchy','.',{'viewHierarchy':jsHierarchy,'viewPaths':jsPath})
    if '_design/viewMD5' not in self.db:
      self.saveView('viewMD5','viewMD5',"if (doc.type[0]==='measurement' && !('current_rev' in doc)){emit(doc.md5sum, doc.name);}")
    if '_design/viewQR' not in self.db:
      jsString = "if (doc.qrCode.length > 0 && !('current_rev' in doc))"
      jsString+=   '{doc.qrCode.forEach(function(thisCode) {emit(thisCode, doc.name);});}'
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
    warnings.simplefilter("ignore")  #client disconnect triggers ignored ResourceWarning on socket
    self.client.disconnect()
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
    tracebackString = traceback.format_stack()
    tracebackString = '|'.join([item.split('\n')[1].strip() for item in tracebackString[:-1]])  #| separated list of stack excluding last
    doc['client'] = tracebackString
    del doc['branch']['op']  #remove operation, saveDoc creates and therefore always the same
    doc['branch'] = [doc['branch']]
    if self.confirm is None or self.confirm(doc,"Write this doc?"):
      res = self.db.create_document(doc)
    else:
      res = doc
    return res


  def updateDoc(self, change, docID):
    """
    Update document by
    - saving changes to oldDoc (revision document)
    - updating new-document concurrently
    - create a docID for oldDoc
    - save this docID suffix in nextRevision stored in new-document
    - Bonus: save '_rev' from newDoc to oldDoc in order to track that updates cannot happen by accident

    Args:
        change: dictionary of item to update
                'path' = list: new path list is appended to existing list
                'path' = str : remove this path from path list
        docID:  id of document to change
    """
    tracebackString = traceback.format_stack()
    tracebackString = '|'.join([item.split('\n')[1].strip() for item in tracebackString[:-1]])  #| separated list of stack excluding last
    change['client'] = tracebackString
    newDoc = self.db[docID]  #this is the document that stays live
    oldDoc = {}              #this is an older revision of the document
    nothingChanged = True
    # handle branch
    if 'branch' in change and len(change['branch']['stack'])>0 and change['branch']['path'] is not None:
      op = change['branch']['op']
      del change['branch']['op']
      if not change['branch'] in newDoc['branch']:       #skip if new path already in path
        oldDoc['branch'] = newDoc['branch'].copy()
        if op=='c':    #create, append
          newDoc['branch'] += [change['branch']]
          nothingChanged = False
        elif op=='u':  #update=remove current at zero
          if 'oldpath' in change['branch']:
            for branch in newDoc['branch']:
              if branch['path'].startswith(change['branch']['oldpath']):
                branch['path'] = branch['path'].replace(change['branch']['oldpath'] ,change['branch']['path'])
                branch['stack']= change['branch']['stack']
                del change['branch']['oldpath']
                break
          else:
            newDoc['branch'][0] = change['branch'] #change the initial one
          nothingChanged = False
        elif op=='d':  #delete
          originalLength = len(newDoc['branch'])
          newDoc['branch'] = [branch for branch in newDoc['branch'] if branch['path']!=change['branch']['path']]
          if originalLength!=len(newDoc['branch']):
            nothingChanged = False
        else:
          logging.error('database:updateDoc: op(eration) unknown, exit update')
          return newDoc
    #handle other items
    for item in change:
      if item in ['nextRevision','_id','_rev','branch']:                #skip items cannot come from change
        continue
      if item=='type' and change['type']=='--':                      #skip non-set type
        continue
      if item=='image' and change['image']=='':
        continue
      ## What if content only differs by whitespace changes?
      # These changes should occur in the database, the user wanted it so
      # Do these changes justify a new revision?
      # Hence one could update the doc and previous-revision(with the current _rev)
      #  - but that would lead to special cases, more code, chaos
      #  - also not sure how often simple white space changes occur, how important
      # To identify these cases use the following
      # if (isinstance(change[item], str) and " ".join(change[item].split())!=" ".join(newDoc[item].split()) ) or \
      #    (isinstance(change[item], list) and change[item]!=newDoc[item] ):
      # Add to testBasic to test for it:
      #       myString = myString.replace('A long comment','A long   comment')
      if change[item]!=newDoc[item]:
        if item not in ['date','client']:      #if only date/client change, no real change
          nothingChanged = False
        oldDoc[item] = newDoc[item]
        newDoc[item] = change[item]
    if nothingChanged:
      logging.info('database:updateDoc no change of content: '+newDoc['name'])
      print('database:updateDoc no change of content: '+newDoc['name'])
      return newDoc
    #produce _id of revDoc
    oldDoc['_id'] = docID+'-'+str( newDoc['nextRevision'] )
    newDoc['nextRevision'] += 1
    #add id to revisions and save
    if self.confirm is None or self.confirm(newDoc,"Update this doc?"):
      newDoc.save()  #TODO: exception (update) occurred sometimes: try to find example and debug
    #save _rev to backup for verification
    oldDoc['current_rev'] = newDoc['_rev']
    if self.confirm is None or self.confirm(oldDoc,"Keep this as revision?"):
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
      res = v(startkey=key, endkey=key+'zzz')['rows']
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
      thisJsCode = 'function (doc) {' + jsCode + '}'
      designDoc.add_view(viewName, thisJsCode)
    elif isinstance(jsCode, dict):
      for view in jsCode:
        thisJsCode = 'function (doc) {' + jsCode[view] + '}'
        designDoc.add_view(view, thisJsCode)
    try:
      designDoc.save()
    except Exception:
      logging.error('database:saveView Something unexpected has happend'+traceback.format_exc())
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
    logging.info('database:replicateDB Replication started')
    return


  def checkDB(self,basepath=None, mode=None, **kwargs):
    """
    Check database for consistencies by iterating through all documents
    - slow since no views used
    - check views
    - only reporting, no repair
    - custom changes are possible with normal scan
    - no interaction with harddisk

    Args:
        basepath: basepath of database on local directory; None: ignore those checks
    """
    outstring = f'{bcolors.UNDERLINE}**** LEGEND ****{bcolors.ENDC}\n'
    outstring+= f'{bcolors.OKGREEN}Green: perfect and as intended{bcolors.ENDC}\n'
    outstring+= f'{bcolors.OKBLUE}Blue: ok-ish, can happen: empty files for testing, strange path for measurements{bcolors.ENDC}\n'
    outstring+= f'{bcolors.HEADER}Pink: unsure if bug or desired (e.g. move step to random path-name){bcolors.ENDC}\n'
    outstring+= f'{bcolors.WARNING}Yellow: WARNING should not happen (e.g. procedures without project){bcolors.ENDC}\n'
    outstring+= f'{bcolors.FAIL}Red: FAILURE and ERROR: NOT ALLOWED AT ANY TIME{bcolors.ENDC}\n'
    outstring+= 'Normal text: not understood, did not appear initially\n'
    outstring+= f'{bcolors.UNDERLINE}**** List all DOCUMENTS ****{bcolors.ENDC}\n'
    ## loop all documents
    for doc in self.db:
      if '_design' in doc['_id']:
        outstring+= f'{bcolors.OKGREEN}..info: Design document '+doc['_id']+f'{bcolors.ENDC}\n'
        continue
      if '-dataDictionary-' == doc['_id']:
        outstring+= f'{bcolors.OKGREEN}..info: Data dictionary exists{bcolors.ENDC}\n'
        continue

      # old revisions of document. Test
      # - id has correct shape and original does exist
      # - current_rev is correct
      if 'current_rev' in doc:
        if mode=='delRevisions':
          if self.confirm is None or self.confirm(doc,"Delete this doc?"):
            doc.delete()
          continue
        if len(doc['_id'].split('-'))!=3:
          outstring+= f'{bcolors.FAIL}**ERROR current_rev length not 3 '+doc['_id']+f'{bcolors.ENDC}\n'
          continue
        currentID = '-'.join(doc['_id'].split('-')[:-1])
        try:
          currentDoc= self.getDoc(currentID)
        except:
          outstring+= f'{bcolors.FAIL}**ERROR current_rev current does not exist in db '+doc['_id']+' '+currentID+f'{bcolors.ENDC}\n'
          continue
        if 'branch' in doc:
          for branch in doc['branch']:
            dirNamePrefix = branch['path'].split(os.sep)[-1].split('_')[0]
            if dirNamePrefix.isdigit() and branch['child']!=int(dirNamePrefix): #compare child-number to start of directory name
              outstring+= f'{bcolors.FAIL}**ERROR child-number and dirName dont match '+doc['_id']+f'{bcolors.ENDC}\n'
        if currentDoc['_rev']!=doc['current_rev']:
          docIDarray = doc['_id'].split('-')
          nextRevision = '-'.join(docIDarray[:-1])+'-'+str(int(docIDarray[-1])+1)
          if nextRevision not in self.db:
            outstring+= f'{bcolors.FAIL}**ERROR current_rev has different value than current rev '+doc['_id']+' '+currentID+f'{bcolors.ENDC}\n'
          continue

      # current revision. Test branch and doc-type specific tests
      else:
        #branch test
        if 'branch' not in doc:
          outstring+= f'{bcolors.FAIL}**ERROR branch does not exist '+doc['_id']+f'{bcolors.ENDC}\n'
          continue
        else:
          if len(doc['branch'])>1 and doc['type'] =='text':                 #text elements only one branch
            outstring+= f'{bcolors.FAIL}**ERROR branch length >1 for text'+doc['_id']+' '+str(doc['type'])+f'{bcolors.ENDC}\n'
          for branch in doc['branch']:
            if len(branch['stack'])==0 and doc['type']!=['text','project']: #if no inheritance
              if doc['type'][0] == 'procedure' or  doc['type'][0] == 'sample':
                outstring+= f'{bcolors.OKBLUE}**ok-ish branch stack length = 0: no parent for procedure '+doc['_id']+f'{bcolors.ENDC}\n'
              else:
                outstring+= f'{bcolors.WARNING}**WARNING branch stack length = 0: no parent '+doc['_id']+f'{bcolors.ENDC}\n'
            if doc['type'][0]=='text':
              try:
                dirNamePrefix = branch['path'].split(os.sep)[-1].split('_')[0]
                if dirNamePrefix.isdigit() and branch['child']!=int(dirNamePrefix): #compare child-number to start of directory name
                  outstring+= f'{bcolors.FAIL}**ERROR child-number and dirName dont match '+doc['_id']+f'{bcolors.ENDC}\n'
              except:
                pass  #handled next lines
            if branch['path'] is None:
              if doc['type'][0] == 'procedure' or doc['type'][0] == 'sample':
                outstring+= f'{bcolors.OKGREEN}..info: procedure/sample with empty path '+doc['_id']+f'{bcolors.ENDC}\n'
              elif doc['type'][0] == 'measurement':
                outstring+= f'{bcolors.OKBLUE}**warning measurement branch path is None=no data '+doc['_id']+' '+doc['name']+f'{bcolors.ENDC}\n'
              else:
                outstring+= f'{bcolors.FAIL}**ERROR branch path is None '+doc['_id']+f'{bcolors.ENDC}\n'
            else:                                                            #if sensible path
              if len(branch['stack'])+1 != len(branch['path'].split(os.sep)):#check if length of path and stack coincide
                if '://' not in branch['path']:
                  if doc['type'][0] == 'procedure' or doc['type'][0] == 'measurement':
                    outstring+= f'{bcolors.OKBLUE}**ok-ish branch stack and path lengths do not match for procedure '+doc['_id']+f'{bcolors.ENDC}\n'
                  else:
                    outstring+= f'{bcolors.HEADER}**UNSURE branch stack and path lengths do not match '+doc['_id']+f'{bcolors.ENDC}\n'
              if branch['child'] != 9999:
                for parentID in branch['stack']:                              #check if all parents in doc have a corresponding path
                  parentDocBranches = self.getDoc(parentID)['branch']
                  onePathFound = False
                  for parentBranch in parentDocBranches:
                    if parentBranch['path'] is not None and parentBranch['path'] in branch['path']:
                      onePathFound = True
                  if not onePathFound:
                    outstring+= f'{bcolors.FAIL}**ERROR parent does not have corresponding path '+doc['_id']+'| parentID '+parentID+f'{bcolors.ENDC}\n'
        #doc-type specific tests
        if doc['type'][0] == 'sample':
          if 'qrCode' not in doc:
            outstring+= f'{bcolors.FAIL}**ERROR qrCode not in sample '+doc['_id']+f'{bcolors.ENDC}\n'
        elif doc['type'][0] == 'measurement':
          if 'md5sum' not in doc:
            outstring+= f'{bcolors.FAIL}**ERROR md5sum not in measurement '+doc['_id']+f'{bcolors.ENDC}\n'
        elif doc['type'][0] == 'procedure':
          pass
        elif doc['type'][0] == 'text':
          pass
        elif doc['type'][0] == 'step':
          pass
        elif doc['type'][0] == 'task':
          pass
        else:
          outstring+= f'{bcolors.FAIL}**ERROR unknown doctype '+doc['_id']+' '+str(doc['type'])+f'{bcolors.ENDC}\n'

        ###custom temporary changes: keep few as examples
        # if 'revisions' in doc:
        #   del doc['revisions']
        #   doc.save()
        # if "nextRevision" not in doc:
        #   doc['nextRevision'] = 0
        #   doc.save()

        ## output size of document
        # print('Name: {0: <16.16}'.format(doc['name']),'| id:',doc['_id'],'| len:',len(json.dumps(doc)))

    ##TEST views
    outstring+= f'{bcolors.UNDERLINE}**** List problematic VIEWS ****{bcolors.ENDC}\n'
    view = self.getView('viewMD5/viewMD5')
    md5keys = []
    for item in view:
      if item['key']=='':
        outstring+= f'{bcolors.OKBLUE}**warning: measurement without md5sum: '+item['id']+' '+item['value']+f'{bcolors.ENDC}\n'
      else:
        if item['key'] in md5keys:
          outstring+= f'{bcolors.FAIL}**ERROR: md5sum twice in view: '+item['key']+' '+item['id']+' '+item['value']+f'{bcolors.ENDC}\n'
        md5keys.append(item['key'])
    return outstring
