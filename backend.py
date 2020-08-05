#!/usr/bin/python3
""" Python Backend
"""
import os, json, base64, hashlib, shutil, re, sys
import importlib, tempfile
import numpy as np
import matplotlib.pyplot as plt
import PIL
import logging
from io import StringIO, BytesIO
from urllib import request
from pprint import pprint
from database import Database
from commonTools import commonTools as cT
from miscTools import bcolors


class JamDB:
  """
  PYTHON BACKEND
  """

  def __init__(self, localName=None, confirm=None):
    """
    open server and define database

    Args:
        localName: name of local database, otherwise taken from config file
        confirm: confirm changes to database and file-tree
    """
    # open configuration file and define database
    self.debug = True
    self.confirm = confirm
    logging.basicConfig(filename='jamDB.log', format='%(asctime)s|%(levelname)s:%(message)s', datefmt='%m-%d %H:%M:%S' ,level=logging.DEBUG)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
    with open(os.path.expanduser('~')+'/.jamDB.json','r') as f:
      configuration = json.load(f)
    if localName is None:
      localName = configuration['-defaultLocal']
    logging.info('\nSTART JAMS '+localName)
    remoteName= configuration['-defaultRemote']
    user         = configuration[localName]['user']
    password     = configuration[localName]['password']
    databaseName = configuration[localName]['database']
    self.db = Database(user, password, databaseName, confirm=self.confirm)
    self.userID   = configuration['-userID']
    self.remoteDB = configuration[remoteName]
    self.eargs   = configuration['-eargs']
    # open basePath (root of directory tree) as current working directory
    # self.cwd is the addition to basePath
    self.softwarePath = os.path.abspath(os.getcwd())
    self.basePath     = os.path.expanduser('~')+os.sep+configuration[localName]['path']
    self.cwd          = ''
    if not self.basePath.endswith(os.sep):
        self.basePath += os.sep
    if os.path.exists(self.basePath):
        os.chdir(self.basePath)
    else:
        logging.warning('Base folder did not exist. No directory saving\n'+self.basePath)
        self.cwd   = None
    sys.path.append(self.softwarePath+os.sep+'filter')  #allow filters
    # hierarchy structure
    self.dataDictionary = self.db.getDoc('-dataDictionary-')
    self.hierList = self.dataDictionary['-hierarchy-']
    self.hierStack = []
    self.currentID  = None
    self.alive     = True
    return


  def exit(self, deleteDB=False, **kwargs):
    """
    Shutting down things

    Args:
      deleteDB: remove database
      kwargs: additional parameter
    """
    os.chdir(self.softwarePath)  #where program started
    self.db.exit(deleteDB)
    self.alive     = False
    logging.info('\nEND JAMS')
    logging.shutdown()
    return


  ######################################################
  ### Change in database
  ######################################################
  def addData(self, docType, doc, hierStack=[], localCopy=False, forceNewImage=False, **kwargs):
    """
    Save doc to database, also after edit

    Args:
        docType: docType to be stored
        doc: to be stored
        hierStack: hierStack from external functions
        localCopy: copy a remote file to local version
        forceNewImage: create new image in any case
        kwargs: additional parameter, i.e. callback for curation
    """
    logging.debug('addData beginning doc: '+docType+' | hierStack'+str(hierStack))
    callback = kwargs.get('callback', None)
    doc['user']   = self.userID
    childNum       = 9999
    path           = None
    operation      = 'c'
    if docType == '-edit-':
      edit = True
      if 'type' not in doc:
        doc['type'] = ['text',self.hierList[len(self.hierStack)-1]]
      if len(hierStack) == 0:  hierStack = self.hierStack
      if '_id' not in doc:
        doc['_id'] = hierStack[-1]
      if len(hierStack)>0:
        hierStack   = hierStack[:-1]
      elif 'branch' in doc:
        hierStack   = doc['branch'][0]['stack']
    else:  #new doc
      edit = False
      if docType in self.hierList:
        doc['type'] = ['text',docType]
      else:
        doc['type'] = [docType]
      if len(hierStack) == 0:  hierStack = self.hierStack

    # collect text-doc and prepare
    if doc['type'][0] == 'text' and ( doc['type'][1]!='project' or 'childNum' in doc):
      if 'childNum' in doc:
        childNum = doc['childNum']
        del doc['childNum']
      else:
        #should not have childnumber in other cases
        thisStack = ' '.join(self.hierStack)
        view = self.db.getView('viewHierarchy/viewHierarchy', key=thisStack) #not faster with cT.getChildren
        childNum = 0
        for item in view:
          if item['value'][1]=='project': continue
          if thisStack == ' '.join(item['key'].split(' ')[:-1]): #remove last item from string
            childNum += 1
    prefix = doc['type'][0][0]

    # find path name on local file system; name can be anything
    if self.cwd is not None and 'name' in doc:
      if doc['type'][0] == 'text':
        #project, step, task
        if doc['type'][0]=='project': childNum = 0
        if edit:      #edit: cwd of the project/step/task: remove last directory from cwd (since cwd contains a / at end: remove two)
          parentDirectory = os.sep.join(self.cwd.split(os.sep)[:-2])
          if len(parentDirectory)>2: parentDirectory += os.sep
        else:         #new: below the current project/step/task
          parentDirectory = self.cwd
        path = parentDirectory + self.createDirName(doc['name'],doc['type'][1],childNum) #update,or create (if new doc, update ignored anyhow)
        operation = 'u'
      else:
        #measurement, sample, procedure
        md5sum = ''
        if '://' in doc['name']:                                 #make up name
          if localCopy:
            baseName, extension = os.path.splitext(os.path.basename(doc['name']))
            path = self.cwd + cT.camelCase(baseName)+extension
            request.urlretrieve(doc['name'], self.basePath+path)
            doc['name'] = cT.camelCase(baseName)+extension
          else:
            path = doc['name']
            try:
              md5sum  = hashlib.md5(request.urlopen(doc['name']).read()).hexdigest()
            except:
              print('addData: fetch remote content failed. Data not added')
              return
        elif os.path.exists(self.basePath+doc['name']):          #file exists
          path = doc['name']
          doc['name'] = os.path.basename(doc['name'])
        elif os.path.exists(self.basePath+self.cwd+doc['name']): #file exists
          path = self.cwd+doc['name']
        else:                                                     #make up name
          md5sum  = None
        if md5sum is not None and doc['type'][0]=='measurement':         #samples, procedures not added to md5 database, getMeasurement not sensible
          if md5sum == '':
            with open(self.basePath+path,'rb') as fIn:
              md5sum = hashlib.md5(fIn.read()).hexdigest()
          view = self.db.getView('viewMD5/viewMD5',md5sum)
          if len(view)==0 or forceNewImage:  #measurement not in database: create doc
            while True:
              self.getMeasurement(path,md5sum,doc)
              if len(doc['metaVendor'])==0 and len(doc['metaUser'])==0 and \
                doc['image']=='' and len(doc['type'])==1:  #did not get valuable data: filter does not exit
                return
              if callback is None or callback(doc):
                break
          if len(view)==1:
            doc['_id'] = view[0]['id']
            doc['md5sum'] = md5sum
            edit = True
        elif doc['type'][0]=='procedure' and path is not None:
          with open(self.basePath+path,'r') as fIn:
            doc['content'] = fIn.read()
    # assemble branch information
    doc['branch'] = {'stack':hierStack,'child':childNum,'path':path,'op':operation}
    if edit:
      #update document
      doc = cT.fillDocBeforeCreate(doc, '--', '--').to_dict()
      doc = self.db.updateDoc(doc, doc['_id'])
    else:
      # add doc to database
      doc = cT.fillDocBeforeCreate(doc, doc['type'], prefix).to_dict()
      doc = self.db.saveDoc(doc)

    ## adaptation of directory tree, information on disk: documentID is required
    if self.cwd is not None and doc['type'][0]=='text':
      #project, step, task
      path = doc['branch'][0]['path']
      os.makedirs(self.basePath+path, exist_ok=True)   #if exist, create again; moving not necessary since directory moved in changeHierarchy
      with open(self.basePath+path+'/.id_jamDB.json','w') as f:  #local path, update in any case
        f.write(json.dumps(doc))
    self.currentID = doc['_id']
    logging.debug('addData ending doc '+doc['_id']+' '+doc['_rev']+' '+doc['type'][0])
    return


  def createDirName(self,name,docType,thisChildNumber):
    """ create directory-name by using camelCase and a prefix

    Args:
       name: name with spaces etc.
       docType: document type used for prefix
       thisChildNumber: number of myself
    """
    if docType == 'project':
      return cT.camelCase(name)
    else:  #steps, tasks
      if isinstance(thisChildNumber, str):
        thisChildNumber = int(thisChildNumber)
      return ('{:03d}'.format(thisChildNumber))+'_'+cT.camelCase(name)


  ######################################################
  ### Disk directory/folder methods
  ######################################################
  def changeHierarchy(self, docID, dirName=None, **kwargs):
    """
    Change through text hierarchy structure
    change hierarchyStack, change directory, change stored cwd

    Args:
        docID: information on how to change
        dirName: use this name to change into
        kwargs: additional parameter
    """
    if docID is None or docID in self.hierList:  # none, 'project', 'step', 'task' are given: close
      self.hierStack.pop()
      if self.cwd is not None:
        os.chdir('..')
        self.cwd = os.sep.join(self.cwd.split(os.sep)[:-2])+os.sep
        if self.cwd==os.sep: self.cwd=''
    else:  # existing ID is given: open that
      try:
        if self.cwd is not None:
          if dirName is None:
            doc = self.db.getDoc(docID)
            path = doc['branch'][0]['path']
            dirName = path.split(os.sep)[-1]
          os.chdir(dirName)     #exception caught
          self.cwd += dirName+os.sep
        self.hierStack.append(docID)
      except:
        print('Could not change into hierarchy. id:'+docID+'  directory:'+dirName+'  cwd:'+self.cwd)
    if self.debug and len(self.hierStack)+1!=len(self.cwd.split(os.sep)):
      logging.error('changeHierarchy error')
    return


  def scanTree(self, method=None, **kwargs):
    """ Scan directory tree recursively from project/...
    - find changes on file system and move those changes to DB
    - use .id_jamDB.json to track changes of directories, aka projects/steps/tasks
    - use MD5sum to track changes of measurements etc. (one file=one md5sum=one entry in DB)
    - create database entries for measurements in directory
    - move/copy/delete allowed as the doc['path'] = list of all copies
      doc['path'] is adopted once changes are observed

    Args:
      method: 'produceData' copy database entry to file system; for backup: '_jamDB.json'
              'compareToDB' compare database entry to file system backup to observe accidental changes anyplace
        kwargs: additional parameter, i.e. callback
    """
    logging.info('scanTree started with method '+str(method))
    if len(self.hierStack) == 0:
      print(f'{bcolors.FAIL}Warning - scan directory: No project selected{bcolors.ENDC}')
      return
    if   method == 'produceData': produceData, compareToDB = True, False
    elif method == 'compareToDB': produceData, compareToDB = False, True
    else                        : produceData, compareToDB = False, False
    callback = kwargs.get('callback', None)

    # get information from database
    if logging.root.level<15 and self.cwd[-1]!=os.sep:  #check if debug mode
      logging.error("scanTree cwd does not end with /")
      print("scanTree cwd does not end with /")
    view = self.db.getView('viewHierarchy/viewPaths', key=self.cwd[:-1]) #remove trailing /; assuming that it is there
    database = {} #path as key for lookup, required later
    for item in view:
      database[item['key']] = [item['id'], item['value'][1], item['value'][2],item['value'][3]]

    # iterate directory-tree and compare
    parentID = None
    toDelete = []
    for path, dirs, files in os.walk('.'):
      #compare path: project/step/task
      path = os.path.normpath(self.cwd+path)
      if path in database:
        parentID = database[path][0]
        #database and directory agree regarding project/step/task
        #check id-file
        try:
          with open(self.basePath+path+'/.id_jamDB.json', 'r') as fIn:
            idFile  = json.load(fIn)
          if idFile['branch'][0]['path']==path and idFile['_id']==database[path][0] and idFile['type']==database[path][1]:
            logging.debug(path+' id-test successful on project/step/task')
          else:
            if idFile['_id']==database[path][0] and idFile['type']==database[path][1]:
              logging.warning('produce new .id_jamDB.json after move of directory '+path)
              doc = self.db.getDoc(database[path][0])
              with open(self.basePath+path+'/.id_jamDB.json','w') as f:
                f.write(json.dumps(doc))
            else:
              logging.error(path+' id-test NOT successful on project/step/task')
              logging.error(idFile['branch'][0]['path']+' | '+idFile['_id']+' | '+idFile['type'])
              logging.error(path+' | '+str(database[path]))
          if produceData:
            #if you have to produce
            doc = self.db.getDoc(database[path][0])
            with open(self.basePath+path+'/data_jamDB.json','w') as fOut:
              fOut.write(json.dumps(doc))
          elif compareToDB:
            #if you have to compare
            with open(self.basePath+path+'/data_jamDB.json') as fIn:
              docFile = json.load(fIn)
            docDB = self.db.getDoc(docFile['_id'])
            if docDB==docFile:
              logging.debug(path+' test _jamDB.json successful on project/step/task')
            else:
              logging.warning(path+' test _jamDB.json NOT successful on project/step/task')
              logging.warning(docDB)
              logging.warning(docFile)
        except:
          logging.error('scanTree: .id_jamDB.json file deleted from '+path)
      else:
        if os.path.exists(self.basePath+path+'/.id_jamDB.json'):
          #update .id_jamDB.json file and database with new path information
          with open(self.basePath+path+'/.id_jamDB.json') as fIn:
            idFile  = json.load(fIn)
          onDB = self.getDoc(idFile['_id'])
          onRecordPath = onDB['branch'][0]['path']
          if os.path.exists(self.basePath+onRecordPath):
            logging.info('Remove path in directory '+self.basePath+path)
            toDelete.append(self.basePath+path)
          else:
            logging.info('Updated path in directory and database '+idFile['branch'][0]['path']+' to '+path)
            doc = self.db.updateDoc( {'branch':{'path':path,\
                                                'stack':idFile['branch'][0]['stack'],\
                                                'child':idFile['branch'][0]['child'],\
                                                'op':'u'}}, idFile['_id'])
            with open(self.basePath+path+'/.id_jamDB.json','w') as f:
              f.write(json.dumps(doc))
        else:
          if os.path.exists(self.basePath+path+os.sep+"exclude_scan.txt"):
            dirs[:] = []
            logging.warning(path+' directory (project/step/task) not in database: Exclude it')
            continue
          else:
            logging.warning(path+' directory (project/step/task) not in database: did user create misc. directory')
      # FILES
      # compare data=files in each path (in each project, step, ..)
      for file in files:
        if '_jamDB.' in file: continue
        fileName = path+os.sep+file
        jsonFileName = fileName.replace('.','_')+'_jamDB.json'
        if fileName in database:
          #test if MD5 value did not change
          with open(self.basePath+fileName,'rb') as fIn:
            md5File = hashlib.md5(fIn.read()).hexdigest()
          if md5File==database[fileName][3]:
            logging.debug(fileName+' md5-test successful on measurement/etc.')
          else:
            logging.error(fileName+' md5-test NOT successful on measurement/etc. '+md5File+' '+database[fileName][3])
          if produceData:
            #if you have to produce
            doc = self.db.getDoc(database[fileName][0])
            with open(self.basePath+jsonFileName,'w') as f:
              f.write(json.dumps(doc))
            if doc['image'].startswith('data:image/jpg'):  #jpg and png
              image = base64.b64decode( doc['image'][22:].encode() )
              ending= doc['image'][11:14]
              with open(self.basePath+jsonFileName[:-4]+ending,'wb') as fOut:
                fOut.write(image)
            else:                                           #svg
              with open(self.basePath+jsonFileName[:-4]+'svg','w') as fOut:
                fOut.write(doc['image'])
          elif compareToDB:
            #database and directory agree regarding measurement/etc.
            try:
              with open(self.basePath+jsonFileName) as fIn:
                docFile = json.load(fIn)  #exception handled
              docDB = self.db.getDoc(docFile['_id'])
              if docDB==docFile:
                logging.debug(fileName+' slow test successful on measurement/etc.')
              else:
                logging.error(fileName+' slow test NOT successful on measurement/etc.')
                logging.error(docDB)
                logging.error(docFile)
            except:
              logging.error(jsonFileName+' json file does not exist')
          del database[fileName]
        else:
          #not in database, create database entry: if it already exists, self.addData takes care of it
          logging.info(file+' file not in database. Create/Update in database')
          newDoc    = {'name':path+os.sep+file}
          parentDoc = self.db.getDoc(parentID)
          hierStack = parentDoc['branch'][0]['stack']+[parentID]
          self.addData('measurement', newDoc, hierStack, callback=callback)
      if path in database:
        del database[path]

    ## if path remains, delete it
    for item in toDelete:
      if os.path.exists(item):
        if self.confirm is None or self.confirm(item,"Delete this directory?"):
          shutil.rmtree(item)
    for key in database:
      if self.confirm is None or self.confirm(key,"Yes: Remove directory from database; No: Add directory to file-tree"):
        logging.warning('Remove branch from database '+key)
        doc = {'_id':database[key][0], 'type':database[key][1]}
        doc['branch'] = {'path':key, 'op':'d', 'stack':[None]}
        doc = self.db.updateDoc(doc, doc['_id'])
      else:
        if database[key][1][0] == "text":  #create directory
          os.makedirs(self.basePath+key)
          with open(self.basePath+key+'/.id_jamDB.json','w') as f:  #local path, update in any case
            f.write(json.dumps(self.getDoc( database[key][0] )))
        else:
          print("**ERROR** should not be here ",database[key][1])
          return
    logging.info('scanTree finished')
    return


  def cleanTree(self, all=True):
    """
    clean all _jamDB.json files from directories
    - id files in directories are kept

    Args:
       all: remove files in all projects/steps/tasks
            else: only remove in this directory recursively
    """
    if all:
      directory = self.basePath
    else:
      directory = self.cwd
    for path, _, files in os.walk(directory):
      for file in files:
        if file.endswith('_jamDB.json') and file!='.id_jamDB.json':
          filePath = os.path.normpath(path+os.sep+file)
          os.remove(filePath)


  def getMeasurement(self, filePath, md5sum, doc, **kwargs):
    """
    get measurements from datafile: central distribution point
    - max image size defined here

    Args:
        filePath: path to file
        md5sum: md5sum to store in database (not used here)
        doc: pass known data/measurement type, can be used to create image; This doc is altered
        kwargs: additional parameter, i.e. maxSize, show

    Return:
        void
    """
    logging.debug('getMeasurement started for path '+filePath)
    maxSize = kwargs.get('maxSize', 600)
    show    = kwargs.get('show', False)
    extension = os.path.splitext(filePath)[1][1:]
    if '://' in filePath:
      absFilePath = filePath
      outFile = self.basePath+self.cwd+os.path.basename(filePath).split('.')[0]+'_jamDB'
    else:
      absFilePath = self.basePath + filePath
      outFile = absFilePath.replace('.','_')+'_jamDB'
    pyFile = 'jamDB_'+extension+'.py'
    pyPath = self.softwarePath+os.sep+'filter'+os.sep+pyFile
    if os.path.exists(pyPath):
      # import module and use to get data
      module = importlib.import_module(pyFile[:-3])
      image, imgType, meta = module.getMeasurement(absFilePath, doc)
      if show:
        if isinstance(image, PIL.Image.Image):
          image.show()
        else:
          plt.show()
      # depending on imgType: produce image
      if imgType == 'svg':  #no scaling
        figfile = StringIO()
        plt.savefig(figfile, format='svg')
        image = figfile.getvalue()
        # 'data:image/svg+xml;utf8,<svg' + figfile.getvalue().split('<svg')[1]
        if self.cwd is not None:
          with open(outFile+'.svg','w') as f:
            figfile.seek(0)
            shutil.copyfileobj(figfile, f)
      elif imgType == 'jpg':
        ratio = maxSize / image.size[np.argmax(image.size)]
        image = image.resize((np.array(image.size)*ratio).astype(np.int)).convert('RGB')
        figfile = BytesIO()
        image.save(figfile, format='JPEG')
        imageData = base64.b64encode(figfile.getvalue()).decode()
        image = 'data:image/jpg;base64,' + imageData
        if self.cwd is not None:
          with open(outFile+'.jpg','wb') as f:
            figfile.seek(0)
            shutil.copyfileobj(figfile, f)
      elif imgType == 'png':
        ratio = maxSize / image.size[np.argmax(image.size)]
        image = image.resize((np.array(image.size)*ratio).astype(np.int))
        figfile = BytesIO()
        image.save(figfile, format='PNG')
        imageData = base64.b64encode(figfile.getvalue()).decode()
        image = 'data:image/png;base64,' + imageData
        if self.cwd is not None:
          with open(outFile+'.png','wb') as f:
            figfile.seek(0)
            shutil.copyfileobj(figfile, f)
      else:
        image = ''
        meta  = {'measurementType':[],'metaVendor':{},'metaUser':{}}
        logging.debug('getMeasurement should not read data; returned data void '+str(imgType))
    else:
      image = ''
      meta  = {'measurementType':[],'metaVendor':{},'metaUser':{}}
      logging.warning('getMeasurement could not find pyFile to convert '+pyFile)
    #combine into document
    measurementType = meta['measurementType']
    metaVendor      = meta['metaVendor']
    metaUser        = meta['metaUser']
    document = {'image': image, 'type': ['measurement']+measurementType,
            'metaUser':metaUser, 'metaVendor':metaVendor, 'md5sum':md5sum}
    logging.debug('getMeasurement: finished')
    doc.update(document)
    if show:
      print("Measurement type:",document['type'])
    if 'comment' not in doc: doc['comment']=''
    return


  ######################################################
  ### Wrapper for database functions
  ######################################################
  def getDoc(self, id):
    """
    Wrapper for getting data from database

    Args:
        id: document id
    """
    return self.db.getDoc(id)


  def replicateDB(self, remoteDB=None, removeAtStart=False, **kwargs):
    """
    Replicate local database to remote database

    Args:
        remoteDB: if given, use this name for external db
        removeAtStart: remove remote DB before starting new
        kwargs: additional parameter
    """
    if remoteDB is not None:
      self.remoteDB['database'] = remoteDB
    self.db.replicateDB(self.remoteDB, removeAtStart)
    return


  def checkDB(self,  mode=None, **kwargs):
    """
    Wrapper of check database for consistencies by iterating through all documents

    Args:
        mode: mode for checking database, e.g. delete revisions
        kwargs: additional parameter, i.e. callback
    """
    return self.db.checkDB(self.basePath, mode, **kwargs)


  ######################################################
  ### OUTPUT COMMANDS and those connected to it      ###
  ######################################################
  def output(self, docLabel, printID=False, **kwargs):
    """
    output view to screen
    - length of output 110 character

    Args:
      docLabel: document label to output
      printID:  include docID in output string
      kwargs: additional parameter
    """
    view = 'view'+docLabel
    outString = []
    docList = self.db.dataLabels+self.db.hierarchyLabels
    idx     = list(dict(docList).values()).index(docLabel)
    docType = list(dict(docList).keys())[idx]
    for item in self.db.dataDictionary[docType]['default']:
      if item['length']!=0:
        formatString = '{0: <'+str(abs(item['length']))+'}'
        outString.append(formatString.format(item['name']) )
    outString = '|'.join(outString)+'\n'
    outString += '-'*110+'\n'
    for lineItem in self.db.getView(view+os.sep+view):
      rowString = []
      for idx, item in enumerate(self.db.dataDictionary[docType]['default']):
        if item['length']!=0:
          formatString = '{0: <'+str(abs(item['length']))+'}'
          if isinstance(lineItem['value'][idx], str ):
            contentString = lineItem['value'][idx]
          else:
            contentString = ' '.join(lineItem['value'][idx])
          contentString = contentString.replace('\n',' ')
          if item['length']<0:  #test if value as non-trivial length
            if lineItem['value'][idx]=='true' or lineItem['value'][idx]=='false':
              contentString = lineItem['value'][idx]
            elif len(lineItem['value'][idx])>1 and len(lineItem['value'][idx][0])>3:
              contentString = 'true'
            else:
              contentString = 'false'
            # contentString = True if contentString=='true' else False
          rowString.append(formatString.format(contentString)[:abs(item['length'])] )
      if printID:
        rowString.append(' '+lineItem['id'])
      outString += '|'.join(rowString)+'\n'
    return outString


  def outputHierarchy(self, onlyHierarchy=True, addID=False, addTags=None, **kwargs):
    """
    output hierarchical structure in database
    - convert view into native dictionary
    - ignore key since it is always the same

    Args:
       onlyHierarchy: only print project,steps,tasks or print all (incl. measurements...)[default print all]
       addID: add docID to output
       addTags: add tags, comments, objective to output
       kwargs: additional parameter, i.e. callback
    """
    if len(self.hierStack) == 0:
      logging.warning('jams.outputHierarchy No project selected')
      return 'Warning: jams.outputHierarchy No project selected'
    hierString = ' '.join(self.hierStack)
    view = self.db.getView('viewHierarchy/viewHierarchy', key=hierString)
    nativeView = {}
    for item in view:
      if onlyHierarchy and not item['id'].startswith('t-'):
        continue
      nativeView[item['id']] = [item['key']]+item['value']
    if addTags=='all':
      outString = cT.hierarchy2String(nativeView, addID, self.getDoc, 'all')
    elif addTags=='tags':
      outString = cT.hierarchy2String(nativeView, addID, self.getDoc, 'tags')
    else:  #why native view has extra "  " in StepFour?
      outString = cT.hierarchy2String(nativeView, addID, None, 'none')
    minPrefix = len(re.findall('^\*+',outString)[0])
    startLine = '\n\*{'+str(minPrefix)+'}'
    outString = re.sub(startLine,'\n',outString)[minPrefix+1:] #also remove from head of string
    return outString


  def getEditString(self):
    """
    Return Markdown string of hierarchy tree
    """
    #simple style
    if self.eargs['style']=='simple':
      doc = self.db.getDoc(self.hierStack[-1])
      return ', '.join([tag for tag in doc['tags']])+' '+doc['comment']
    #complicated style
    return self.outputHierarchy(True,True,'tags')


  def setEditString(self, text, callback=None):
    """
    Using Org-Mode string, replay the steps to update the database

    Args:
       text: org-mode structured text
       callback: function to verify database change
    """
    with open(tempfile.gettempdir()+os.sep+'tempSetEditString.txt','w') as fOut:
      fOut.write(text)
    # add the prefix to org-mode structure lines
    prefix = '*'*len(self.hierStack)
    startLine = '^\*+\ '
    newText = ''
    for line in text.split('\n'):
      if len(re.findall(startLine,line))>0:  #structure line
        newText += prefix+line+'\n'
      else:                                  #other lines, incl. first
        newText += line+'\n'
    newText = prefix+' '+newText
    docList = cT.editString2Docs(newText)
    # initialize iteration
    hierLevel = None
    children  = [0]
    path      = None
    for doc in docList:
      # identify docType
      levelID     = doc['type']
      doc['type'] = ['text',self.hierList[levelID]]
      if doc['edit'] == "-edit-":
        edit = "-edit-"
      else:
        edit = doc['type'][-1]
      del doc['edit']
      # change directories: downward
      if hierLevel is None:   #first run through
        docDB = self.db.getDoc(doc['_id'])
        doc['childNum'] = docDB['branch'][0]['child']
      else:                   #after first entry
        if levelID<hierLevel:
          children.pop()
          self.changeHierarchy(None)                        #'cd ..'
          self.changeHierarchy(None)                        #'cd ..'
          children[-1] += 1
        elif levelID>hierLevel:
          children.append(0)
        else:
          self.changeHierarchy(None)                        #'cd ..'
          children[-1] += 1
        #check if directory exists on disk
        #move directory; this is the first point where the non-existence of the folder is seen and can be corrected
        dirName = self.createDirName(doc['name'],doc['type'][0],children[-1])
        if not os.path.exists(dirName):                     #after move, deletion or because new
          if doc['_id']=='':                                #because new data
            os.makedirs(dirName)
            edit = doc['type'][-1]
          else:                                             #after move
            docDB = self.db.getDoc(doc['_id'])
            path = docDB['branch'][0]['path']
            if not os.path.exists(self.basePath+path):        #parent was moved: get 'path' from knowledge of parent
              parentID = docDB['branch'][0]['stack'][-1]
              pathParent = self.db.getDoc(parentID)['branch'][0]['path']
              path = pathParent+os.sep+path.split(os.sep)[-1]
            if not os.path.exists(self.basePath+path):        #if still does not exist
              print("**ERROR** doc path was not found and parent path was not found\nReturn")
              return
            if self.confirm is None or self.confirm(None,"Move directory "+self.basePath+path+" -> "+dirName):
              shutil.move(self.basePath+path, dirName)
            logging.info('setEditSting cwd '+self.cwd+'| non-existant directory '+dirName+'. Moved old one to here')
        if edit=='-edit-':
          self.changeHierarchy(doc['_id'], dirName=dirName)   #'cd directory'
          if path is not None:
            #adopt measurements, samples, etc: change / update path by supplying old path
            view = self.db.getView('viewHierarchy/viewPaths', key=path)
            for item in view:
              if item['value'][1][0]=='text': continue  #skip since moved by itself
              self.db.updateDoc( {'branch':{'path':self.cwd, 'oldpath':path+os.sep,\
                                            'stack':self.hierStack,\
                                            'child':item['value'][2],\
                                            'op':'u'}},item['id'])
        doc['childNum'] = children[-1]
      # add information to doc and save to database
      #   path and hierStack are added in self.addData
      if doc['objective']=='':
        del doc['objective']
      self.addData(edit, doc, self.hierStack)
      #update variables for next iteration
      if edit!="-edit-" and hierLevel is not None:
        self.changeHierarchy(self.currentID)   #'cd directory'
      hierLevel = levelID
    #at end, go down ('cd  ..') number of children-length
    for i in range(len(children)-1):
      self.changeHierarchy(None)
    os.unlink(tempfile.gettempdir()+os.sep+'tempSetEditString.txt')
    return


  def getChildren(self, docID):
    hierTree = self.outputHierarchy(True,True,False)
    if hierTree is None:
      print('No hierarchy tree')
      return None, None
    result = cT.getChildren(hierTree,docID)
    return result['names'], result['ids']


  def outputQR(self):
    """
    output list of sample qr-codes
    """
    outString = '{0: <36}|{1: <36}|{2: <36}'.format('QR', 'Name', 'ID')+'\n'
    outString += '-'*110+'\n'
    for item in self.db.getView('viewQR/viewQR'):
      outString += '{0: <36}|{1: <36}|{2: <36}'.format(item['key'][:36], item['value'][:36], item['id'][:36])+'\n'
    return outString


  def outputMD5(self):
    """
    output list of measurement md5-sums of files
    """
    outString = '{0: <32}|{1: <40}|{2: <25}'.format('MD5 sum', 'Name', 'ID')+'\n'
    outString += '-'*110+'\n'
    for item in self.db.getView('viewMD5/viewMD5'):
      outString += '{0: <32}|{1: <40}|{2: <25}'.format(item['key'], item['value'][-40:], item['id'])+'\n'
    return outString
