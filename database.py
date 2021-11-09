"""Class for interaction with couchDB
"""
import traceback, logging

class Database:
  """
  Class for interaction with couchDB
  """

  def __init__(self, user, password, databaseName, confirm, softwarePath=''):
    """
    Args:
        user (string): user name to local database
        password (string): password to local database
        databaseName (string): local database name
        confirm (function): confirm changes to database and file-tree
        softwarePath (string): path to software and default dataDictionary.json
    """
    import json
    from cloudant.client import CouchDB
    self.confirm = confirm
    try:
      self.client = CouchDB(user, password, url='http://127.0.0.1:5984', connect=True)
    except:
      logging.error('database:init Something unexpected has happend\n'+traceback.format_exc())
      print('database:init Something unexpected has happend\n'+traceback.format_exc())
      raise
    self.databaseName = databaseName
    if self.databaseName in self.client.all_dbs():
      self.db = self.client[self.databaseName]
    else:
      self.db = self.client.create_database(self.databaseName)
    # check if default documents exist and create
    if '-ontology-' not in self.db:
      logging.info('database:init ontology not defined. Use default one')
      with open(softwarePath+'ontology.json', 'r') as fIn:
        doc = json.load(fIn)
      _ = self.db.create_document(doc)
    # check if default views exist and create them
    self.ontology    = self.db['-ontology-']
    return


  def initViews(self, docTypesLabels, magicTags=['TODO','v1']):
    """
    initialize all views

    Args:
      docTypesLabels (list): pair of (docType,docLabel) used to create views
      magicTags (list): magic tags used for view creation
    """
    # for the individual docTypes
    jsDefault = "if ($docType$) {emit($key$, [$outputList$]);}"
    viewCode = {}
    for docType, _ in docTypesLabels:
      if docType=='x0':
        jsString = jsDefault.replace('$docType$', "doc['-type']=='x0'").replace('$key$','doc._id')
      else:     #only show first instance in list doc.branch[0]
        jsString = jsDefault.replace('$docType$', "doc['-type'][0]=='"+docType+"'").replace('$key$','doc["-branch"][0].stack[0]')
      outputList = []
      for item in self.ontology[docType]:
        if 'name' not in item:
          continue
        if item['name'] == 'image':
          outputList.append('(doc.image.length>3).toString()')
        elif item['name'] == 'tags':
          outputList.append('doc.tags.join(" ")')
        elif item['name'] == '-type':
          outputList.append('doc["-type"].slice(1).join("/")')
        elif item['name'] == 'content':
          outputList.append('doc.content.slice(0,100)')
        else:
          outputList.append('doc["'+item['name']+'"]')
      outputList = ','.join(outputList)
      jsString = jsString.replace('$outputList$', outputList)
      logging.info('database:init view '+docType+' not defined. Use default one:'+jsString)
      viewCode[docType.replace('/','__')]=jsString
    self.saveView('viewDocType', viewCode)
    # general views: Hierarchy, Identify
    jsHierarchy  = '''
      if ('-type' in doc) {
        doc['-branch'].forEach(function(branch) {emit(branch.stack.concat([doc._id]).join(' '),[branch.child,doc['-type'],doc.name]);});
      }
    '''
    jsPath = '''
      if ('-type' in doc && '-branch' in doc){
        if ('shasum' in doc){doc['-branch'].forEach(function(branch){if(branch.path){emit(branch.path,[branch.stack,doc['-type'],branch.child,doc.shasum]);}});}
        else                {doc['-branch'].forEach(function(branch){if(branch.path){emit(branch.path,[branch.stack,doc['-type'],branch.child,''        ]);}});}
      }
    '''
    self.saveView('viewHierarchy',{'viewHierarchy':jsHierarchy,'viewPaths':jsPath})
    jsSHA= "if (doc['-type'][0]==='measurement'){emit(doc.shasum, doc.name);}"
    jsQR = "if (doc.qrCode.length > 0)"
    jsQR+= '{doc.qrCode.forEach(function(thisCode) {emit(thisCode, doc.name);});}'
    jsTags=str(magicTags)+".forEach(function(tag){if(doc.tags.indexOf('#'+tag)>-1) emit('#'+tag, doc.name);});"
    views = {'viewQR':jsQR, 'viewSHAsum':jsSHA, 'viewTags':jsTags}
    self.saveView('viewIdentify', views)
    return


  def exit(self, deleteDB=False):
    """
    Shutting down things

    Args:
      deleteDB (bool): remove database
    """
    import warnings
    if deleteDB:
      self.db.client.delete_database(self.databaseName)
    warnings.simplefilter("ignore")  #client disconnect triggers ignored ResourceWarning on socket
    self.client.disconnect()
    return


  def getDoc(self, docID):
    """
    Wrapper for get from database function

    Args:
        docID (dict): document id

    Returns:
        string: json representation of document
    """
    return self.db[docID]


  def saveDoc(self, doc):
    """
    Wrapper for save to database function

    Args:
        doc (dict): document to save

    Returns:
        dict: json representation of submitted document
    """
    tracebackString = traceback.format_stack()
    tracebackString = [item for item in tracebackString if 'backend.py' in item or 'database.py' in item or 'Tests' in item or 'pasta' in item]
    tracebackString = '|'.join([item.split('\n')[1].strip() for item in tracebackString])  #| separated list of stack excluding last
    doc['-client'] = tracebackString
    if '-branch' in doc and 'op' in doc['-branch']:
      del doc['-branch']['op']  #remove operation, saveDoc creates and therefore always the same
      doc['-branch'] = [doc['-branch']]
    if self.confirm is None or self.confirm(doc,"Create this document?"):
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
    - Bonus: save '_rev' from newDoc to oldDoc in order to track that updates cannot happen by accident

    Args:
        change (dict): item to update
                'path' = list: new path list is appended to existing list
                'path' = str : remove this path from path list
        docID (string):  id of document to change

    Returns:
        dict: json representation of updated document
    """
    import json
    tracebackString = traceback.format_stack()
    tracebackString = [item for item in tracebackString if 'backend.py' in item or 'database.py' in item or 'Tests' in item or 'pasta' in item]
    tracebackString = '|'.join([item.split('\n')[1].strip() for item in tracebackString])  #| separated list of stack excluding last
    change['-client'] = tracebackString
    newDoc = self.db[docID]  #this is the document that stays live
    if 'edit' in change:     #if delete
      oldDoc = dict(newDoc)
      for item in oldDoc:
        if item not in ('_id', '_rev', '-branch'):
          del newDoc[item]
      newDoc['-client'] = tracebackString
      newDoc['-user']   = change['-user']
    else:                    #if update
      oldDoc = {}            #this is an older revision of the document
      nothingChanged = True
      # handle branch
      if '-branch' in change and len(change['-branch']['stack'])>0: #TODO Remove if not needed by Dec. 2021: and change['-branch']['path'] is not None:
        op = change['-branch'].pop('op')
        oldpath = change['-branch'].pop('oldpath',None)
        if not change['-branch'] in newDoc['-branch']:       #skip if new branch is already in branch
          oldDoc['-branch'] = newDoc['-branch'].copy()
          for branch in newDoc['-branch']:
            if op=='c' and branch['path']==change['-branch']['path']:
              op='u'
          if op=='c':    #create, append
            newDoc['-branch'] += [change['-branch']]
            nothingChanged = False
          elif op=='u':  #update
            if oldpath is not None:
              for branch in newDoc['-branch']:
                if branch['path'].startswith(oldpath):
                  branch['path'] = branch['path'].replace(oldpath ,change['-branch']['path'])
                  branch['stack']= change['-branch']['stack']
                  break
            else:
              newDoc['-branch'][0] = change['-branch'] #change the initial one
            nothingChanged = False
          elif op=='d':  #delete
            originalLength = len(newDoc['-branch'])
            newDoc['-branch'] = [branch for branch in newDoc['-branch'] if branch['path']!=change['-branch']['path']]
            if originalLength!=len(newDoc['-branch']):
              nothingChanged = False
          else:
            logging.error('database:updateDoc: op(eration) unknown, exit update')
            return newDoc
      #handle other items
      # change has to be dict, not Document
      for item in change:
        if item in ['_id','_rev','-branch']:                #skip items cannot do not result in change
          continue
        if item=='-type' and change['-type']=='--':          #skip non-set type
          continue
        if item=='image' and change['image']=='':          #skip if non-change in image
          continue
        if change[item] is None:                             #skip empty entrances
          continue
        ## Discussion: What if content only differs by whitespace changes?
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
          if item not in ['-date','-client']:      #if only date/client change, no significant change
            nothingChanged = False
          if item == 'image':
            oldDoc[item] = 'image changed'       #don't backup images: makes database big and are only thumbnails anyhow
          else:
            oldDoc[item] = newDoc[item]
          newDoc[item] = change[item]
      if nothingChanged:
        logging.info('database:updateDoc no change of content: '+newDoc['name'])
        return newDoc
    #For both cases: delete and update
    if self.confirm is None or self.confirm({'new':newDoc,'old':oldDoc},"Update this document?"):
      newDoc.save()
      attachmentName = 'v0.json'
      if '_attachments' in newDoc:
        attachmentName = 'v'+str(len(newDoc['_attachments']))+'.json'
      newDoc.put_attachment(attachmentName, 'application/json', json.dumps(oldDoc))
    return newDoc


  def addAttachment(self, docID, name, content):
    """
    Update document by adding attachment (no new revision)

    Args:
        docID (string):  id of document to change
        name (string): attachment name to add to
        content (dict): dictionary of content to be added (should include user,date,docID,remark)

    Returns:
        bool: success of method
    """
    try:
      doc = self.db[docID]
      if not '-attachment' in doc:
        doc['-attachment'] = {}
      if name in doc['-attachment']:
        doc['-attachment'][name] += [content]
      else:
        doc['-attachment'][name] = [content]
      doc.save()
      return True
    except:
      return False



  def getView(self, thePath, startKey=None, preciseKey=None):
    """
    Wrapper for getting view function

    Args:
        thePath (string): path to view
        startKey (string): if given, use to filter output, everything that starts with this key
        preciseKey (string): if given, use to filter output. Match precisely

    Returns:
        list: list of documents in this view
    """
    from cloudant.view import View
    thePath = thePath.split('/')
    designDoc = self.db.get_design_document(thePath[0])
    v = View(designDoc, thePath[1])
    try:
      if startKey is not None:
        res = v(startkey=startKey, endkey=startKey+'zzz')['rows']
      elif preciseKey is not None:
        res = v(key=preciseKey)['rows']
      else:
        res = list(v.result)
    except:
      print('Database / Network problem for path',thePath)
      res = []
    return res


  def saveView(self, designName, viewCode):
    """
    Adopt the view by defining a new jsCode

    Args:
        designName (string): name of the design
        viewCode (dict): viewName: js-code
    """
    from cloudant.design_document import DesignDocument
    if '_design/'+designName in self.db:
      designDoc = self.db['_design/'+designName]
      designDoc.delete()
    designDoc = DesignDocument(self.db, designName)
    for view in viewCode:
      thisJsCode = 'function (doc) {' + viewCode[view] + '}'
      designDoc.add_view(view, thisJsCode)
    try:
      designDoc.save()
    except:
      print('**Error** database:saveView something unexpected has happend: log-file has traceback')
      logging.error('database:saveView Something unexpected has happend'+traceback.format_exc())
    return


  def replicateDB(self, dbInfo, removeAtStart=False):
    """
    Replication to another instance

    Args:
        dbInfo (dict): info on the remote database
        removeAtStart (bool): remove remote DB before starting new

    Returns:
        dict: json of document
    """
    import time
    from cloudant.client import CouchDB
    from cloudant.replicator import Replicator
    try:
      rep = Replicator(self.client)
      try:
        client2 = CouchDB(dbInfo['user'], dbInfo['password'], url=dbInfo['url'], connect=True)
      except:
        print('Could not connect to remote server: Abort replication.')
        return False
      try:
        listAllDataBases = client2.all_dbs()
        if dbInfo['database'] in listAllDataBases and removeAtStart:
          client2.delete_database(dbInfo['database'])
        if not dbInfo['database'] in listAllDataBases:
          db2 = client2.create_database(dbInfo['database'])
      except:
        pass
      db2 = client2[dbInfo['database']]
      replResult = rep.create_replication(self.db, db2, create_target=False, continuous=False)
      print('Start replication '+replResult['_id']+'.')
      logging.info('database:replicateDB Replication started '+replResult['_id'])
      #try every 10sec whether replicaton success. Do that for max. of 5min
      startTime = time.time()
      while True:
        if (time.time()-startTime)/60.>5.:
          print("Waited for 5min. No replication success in that time")
          logging.info("Waited for 5min. No replication success in that time")
          return True
        replResult.fetch()        # get updated, latest version from the server
        if '_replication_state' in replResult:
          print("Replication success state: "+replResult['_replication_state'])
          logging.info("Replication success state: "+replResult['_replication_state'])
          return True
        time.sleep(10)
    except:
      print("**ERROR** replicate\n",traceback.format_exc())
      return False
    return False  #should not reach here


  def historyDB(self):
    """
    Collect last modification days of documents
    """
    from datetime import datetime
    import numpy as np
    collection = {}
    for doc in self.db:
      if doc['_id'][1]=='-' and len(doc['_id'])==34:
        if '-type' in doc and '-date' in doc:
          docType = doc['-type'][0]
          date = doc['-date'][:-1]
          if len(date)==22:
            date += '0'
          date    = datetime.fromisoformat( date ).timestamp()
          if docType in collection:
            collection[docType] = collection[docType] + [date]
          else:
            collection[docType] = [date]
    #determine bins for histogram
    firstSubmit = datetime.now().timestamp()
    for key in collection:
      if np.min(collection[key]) < firstSubmit:
        firstSubmit = np.min(collection[key])
    bins = np.linspace(firstSubmit, datetime.now().timestamp(), 100 )
    #calculate histgram and save it
    for key in collection:
      hist, _ = np.histogram(collection[key], bins)
      collection[key] = hist
    collection['-bins-'] = (bins[:-1]+bins[1:])/2
    #calculate score
    bias = np.exp(( collection['-bins-']-collection['-bins-'][-1] ) / 1.e7)
    score = {}
    for key in collection:
      score[key] = np.sum(collection[key]*bias)
    #reformat dates into string
    collection['-bins-'] = [datetime.fromtimestamp(i).isoformat() for i in collection['-bins-']]
    collection['-score-']= score
    return collection


  def checkDB(self, verbose=True, **kwargs):
    """
    Check database for consistencies by iterating through all documents
    - slow since no views used
    - check views
    - only reporting, no repair
    - custom changes are possible with normal scan
    - no interaction with harddisk

    Args:
        verbose (bool): print more or only issues
        kwargs (dict): additional parameter

    Returns:
        bool: success of check
    """
    import os, re, base64, io
    from PIL import Image
    from miscTools import bcolors
    if verbose:
      outstring = f'{bcolors.UNDERLINE}**** LEGEND ****{bcolors.ENDC}\n'
      outstring+= f'{bcolors.OKGREEN}Green: perfect and as intended{bcolors.ENDC}\n'
      outstring+= f'{bcolors.OKBLUE}Blue: ok-ish, can happen: empty files for testing, strange path for measurements{bcolors.ENDC}\n'
      outstring+= f'{bcolors.HEADER}Pink: unsure if bug or desired (e.g. move step to random path-name){bcolors.ENDC}\n'
      outstring+= f'{bcolors.WARNING}Yellow: WARNING should not happen (e.g. procedures without project){bcolors.ENDC}\n'
      outstring+= f'{bcolors.FAIL}Red: FAILURE and ERROR: NOT ALLOWED AT ANY TIME{bcolors.ENDC}\n'
      outstring+= 'Normal text: not understood, did not appear initially\n'
      outstring+= f'{bcolors.UNDERLINE}**** List all DOCUMENTS ****{bcolors.ENDC}\n'
    else:
      outstring = ''
    ## loop all documents
    for doc in self.db:
      try:
        if '_design' in doc['_id']:
          if verbose:
            outstring+= f'{bcolors.OKGREEN}..info: Design document '+doc['_id']+f'{bcolors.ENDC}\n'
          continue
        if doc['_id'] == '-ontology-':
          if verbose:
            outstring+= f'{bcolors.OKGREEN}..info: ontology exists{bcolors.ENDC}\n'
          continue
        #only normal documents after this line

        ###custom temporary changes: keep few as examples;
        # BE CAREFUL: PRINT FIRST, delete second run
        # if 'revisions' in doc:
        #   del doc['revisions']
        #   doc.save()
        # if len(doc['_id'].split('-'))==3:
        #   print('id',doc['_id'])
        #   doc.delete()
        #   continue
        ## output size of document
        # print('Name: {0: <16.16}'.format(doc['name']),'| id:',doc['_id'],'| len:',len(json.dumps(doc)))

        #branch test
        if '-branch' not in doc:
          outstring+= f'{bcolors.FAIL}**ERROR branch does not exist '+doc['_id']+f'{bcolors.ENDC}\n'
          continue
        if len(doc['-branch'])>1 and doc['-type'] =='x':                 #text elements only one branch
          outstring+= f'{bcolors.FAIL}**ERROR branch length >1 for text'+doc['_id']+' '+str(doc['-type'])+f'{bcolors.ENDC}\n'
        for branch in doc['-branch']:
          for item in branch['stack']:
            if not item.startswith('x-'):
              outstring+= f'{bcolors.FAIL}**ERROR non-text in stack '+doc['_id']+f'{bcolors.ENDC}\n'

          if len(branch['stack'])==0 and doc['-type']!=['x','project']: #if no inheritance
            if doc['-type'][0] == 'measurement' or  doc['-type'][0] == 'x':
              if verbose:
                outstring+= f'{bcolors.WARNING}**warning branch stack length = 0: no parent '+doc['_id']+f'{bcolors.ENDC}\n'
            else:
              if verbose:
                outstring+= f'{bcolors.OKBLUE}**ok-ish branch stack length = 0: no parent for procedure/sample '+doc['_id']+'|'+doc['name']+f'{bcolors.ENDC}\n'
          if '-type' in doc and doc['-type'][0]=='x':
            try:
              dirNamePrefix = branch['path'].split(os.sep)[-1].split('_')[0]
              if dirNamePrefix.isdigit() and branch['child']!=int(dirNamePrefix): #compare child-number to start of directory name
                outstring+= f'{bcolors.FAIL}**ERROR child-number and dirName dont match '+doc['_id']+f'{bcolors.ENDC}\n'
            except:
              pass  #handled next lines
          if branch['path'] is None:
            if doc['-type'][0] == 'x':
              outstring+= f'{bcolors.FAIL}**ERROR branch path is None '+doc['_id']+f'{bcolors.ENDC}\n'
            elif doc['-type'][0] == 'measurement':
              if verbose:
                outstring+= f'{bcolors.OKBLUE}**warning measurement branch path is None=no data '+doc['_id']+' '+doc['name']+f'{bcolors.ENDC}\n'
            else:
              if verbose:
                outstring+= f'{bcolors.OKGREEN}..info: procedure/sample with empty path '+doc['_id']+f'{bcolors.ENDC}\n'
          else:                                                            #if sensible path
            if len(branch['stack'])+1 != len(branch['path'].split(os.sep)):#check if length of path and stack coincide
              if verbose:
                outstring+= f'{bcolors.OKBLUE}**ok-ish branch stack and path lengths not equal: '+doc['_id']+'|'+branch['path']+f'{bcolors.ENDC}\n'
            if branch['child'] != 9999:
              for parentID in branch['stack']:                              #check if all parents in doc have a corresponding path
                parentDocBranches = self.getDoc(parentID)['-branch']
                onePathFound = False
                for parentBranch in parentDocBranches:
                  if parentBranch['path'] is not None and parentBranch['path'] in branch['path']:
                    onePathFound = True
                if not onePathFound:
                  outstring+= f'{bcolors.FAIL}**ERROR parent does not have corresponding path '+doc['_id']+'| parentID '+parentID+f'{bcolors.ENDC}\n'

        #doc-type specific tests
        if '-type' in doc and doc['-type'][0] == 'sample':
          if 'qrCode' not in doc:
            outstring+= f'{bcolors.FAIL}**ERROR qrCode not in sample '+doc['_id']+f'{bcolors.ENDC}\n'
        elif '-type' in doc and doc['-type'][0] == 'measurement':
          if 'shasum' not in doc:
            outstring+= f'{bcolors.FAIL}**ERROR: shasum not in measurement '+doc['_id']+f'{bcolors.ENDC}\n'
          if 'image' not in doc:
            outstring+= f'{bcolors.FAIL}**ERROR: image not in measurement '+doc['_id']+f'{bcolors.ENDC}\n'
          else:
            if doc['image'].startswith('data:image'):  #for jpg and png
              try:
                imgdata = base64.b64decode(doc['image'][22:])
                Image.open(io.BytesIO(imgdata))  #can convert, that is all that needs to be tested
              except:
                outstring+= f'{bcolors.FAIL}**ERROR: jpg-image not valid '+doc['_id']+f'{bcolors.ENDC}\n'
            elif doc['image'].startswith('<?xml'):
              #from https://stackoverflow.com/questions/63419010/check-if-an-image-file-is-a-valid-svg-file-in-python
              SVG_R = r'(?:<\?xml\b[^>]*>[^<]*)?(?:<!--.*?-->[^<]*)*(?:<svg|<!DOCTYPE svg)\b'
              SVG_RE = re.compile(SVG_R, re.DOTALL)
              if SVG_RE.match(doc['image']) is None:
                outstring+= f'{bcolors.FAIL}**ERROR: svg-image not valid '+doc['_id']+f'{bcolors.ENDC}\n'
            elif doc['image']=='':
              outstring+= f'{bcolors.OKBLUE}**warning: image not valid '+doc['_id']+' '+doc['image']+f'{bcolors.ENDC}\n'
            else:
              outstring+= f'{bcolors.FAIL}**ERROR: image not valid '+doc['_id']+' '+doc['image']+f'{bcolors.ENDC}\n'

      except: #if test of document fails
        outstring+= f'{bcolors.FAIL}**ERROR** critical error in '+doc['_id']+f'{bcolors.ENDC}\n'
        outstring+= traceback.format_exc()

    ##TEST views
    if verbose:
      outstring+= f'{bcolors.UNDERLINE}**** List problematic VIEWS ****{bcolors.ENDC}\n'
    view = self.getView('viewIdentify/viewSHAsum')
    shasumKeys = []
    for item in view:
      if item['key']=='':
        if verbose:
          outstring+= f'{bcolors.OKBLUE}**warning: measurement without shasum: '+item['id']+' '+item['value']+f'{bcolors.ENDC}\n'
      else:
        if item['key'] in shasumKeys:
          outstring+= f'{bcolors.FAIL}**ERROR: shasum twice in view: '+item['key']+' '+item['id']+' '+item['value']+f'{bcolors.ENDC}\n'
        shasumKeys.append(item['key'])
    return outstring
