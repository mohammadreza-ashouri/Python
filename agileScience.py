#!/usr/bin/python3
""" Python Backend
"""
import os, json, base64, hashlib, shutil, re
import importlib
import numpy as np
import matplotlib.pyplot as plt
import logging
from io import StringIO, BytesIO
from urllib import request
from pprint import pprint
from asTools import imageToString, stringToImage
from asCloudant import Database
from commonTools import commonTools as cT


class AgileScience:
  """
  PYTHON BACKEND
  """

  def __init__(self, localName=None):
    """
    open server and define database

    Args:
        localName: name of local database, otherwise taken from config file
    """
    # open configuration file and define database
    self.debug = True
    logging.basicConfig(filename='jams.log', filemode='w', format='%(levelname)s:%(message)s', level=logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("matplotlib.font_manager").setLevel(logging.WARNING)
    logging.info("\nSTART JAMS")
    with open(os.path.expanduser('~')+'/.agileScience.json','r') as f:
      configuration = json.load(f)
    if localName is None:
      localName = configuration["-defaultLocal"]
    remoteName= configuration["-defaultRemote"]
    user         = configuration[localName]["user"]
    password     = configuration[localName]["password"]
    databaseName = configuration[localName]["database"]
    self.db = Database(user, password, databaseName)
    self.userID   = configuration["-userID"]
    self.remoteDB = configuration[remoteName]
    self.eargs   = configuration["-eargs"]
    # open basePath (root of directory tree) as current working directory
    # self.cwd is the addition to basePath
    self.softwarePath = os.path.abspath(os.getcwd())
    self.basePath     = os.path.expanduser('~')+"/"+configuration[localName]["path"]
    self.cwd          = ""
    if not self.basePath.endswith("/"):
        self.basePath += "/"
    if os.path.exists(self.basePath):
        os.chdir(self.basePath)
    else:
        logging.warning("Base folder did not exist. No directory saving\n"+self.basePath)
        self.cwd   = None
    # hierarchy structure
    self.dataDictionary = self.db.getDoc("-dataDictionary-")
    self.hierList = self.dataDictionary["-hierarchy-"]
    self.hierStack = []
    self.currentID  = None
    self.alive     = True
    return


  def exit(self, deleteDB=False):
    """
    Shutting down things

    Args:
      deleteDB: remove database
    """
    os.chdir(self.softwarePath)  #where program started
    self.db.exit(deleteDB)
    self.alive     = False
    logging.info("\nEND JAMS")
    logging.shutdown()
    return


  ######################################################
  ### Change in database
  ######################################################
  def addData(self, docType, data, hierStack=[], localCopy=False):
    """
    Save data to data base, also after edit

    Args:
        docType: docType to be stored
        data: to be stored
        hierStack: hierStack from external functions
        localCopy: copy a remote file to local version
    """
    logging.debug('addData beginning data: '+docType+' | hierStack'+str(hierStack))
    data['user']   = self.userID
    childNum       = 9999
    path           = None
    operation      = 'c'
    if docType == '-edit-':
      edit = True
      if 'type' not in data:
        data['type'] = self.hierList[len(self.hierStack)-1]
      if len(hierStack) == 0:  hierStack = self.hierStack
      data['_id'] = hierStack[-1]
      hierStack   = hierStack[:-1]
    else:  #new data
      edit = False
      data['type'] = docType
      if len(hierStack) == 0:  hierStack = self.hierStack

    # collect data and prepare
    if data['type'] in self.hierList and data['type']!='project':
      if 'childNum' in data:
        childNum = data['childNum']
        del data['childNum']
      else:
        #should not have childnumber in other cases
        thisStack = ' '.join(self.hierStack)
        view = self.db.getView('viewHierarchy/viewHierarchy', key=thisStack) #not faster with cT.getChildren
        childNum = 0
        for item in view:
          if item['value'][1]=='project': continue
          if thisStack == ' '.join(item['key'].split(' ')[:-1]): #remove last item from string
            childNum += 1
    if data['type'] in self.hierList:
      prefix = 't'
    else:
      prefix = data['type'][0]

    # find path name on local file system; name can be anything
    if self.cwd is not None and 'name' in data:
      if data['type'] in self.hierList:
        #project, step, task
        if data['type']=='project': childNum = 0
        if edit:      #edit: cwd of the project/step/task: remove last directory from cwd (since cwd contains a / at end: remove two)
          parentDirectory = os.sep.join(self.cwd.split(os.sep)[:-2])
          if len(parentDirectory)>2: parentDirectory += os.sep
        else:         #new: below the current project/step/task
          parentDirectory = self.cwd
        path = parentDirectory + self.createDirName(data['name'],data['type'],childNum) #update,or create (if new data, update ignored anyhow)
        operation = 'u'
      else:
        #measurement, sample, procedure
        md5sum = ""
        if '://' in data['name']:                                 #make up name
          if localCopy:
            path = self.cwd + cT.camelCase( os.path.basename(data['name']))
            request.urlretrieve(data['name'], self.basePath+data['path'])
          else:
            try:
              md5sum  = hashlib.md5(request.urlopen(data['name']).read()).hexdigest()
            except:
              print("addData: fetch remote content failed. Data not added")
              return
        elif os.path.exists(self.basePath+data['name']):          #file exists
          path = data['name']
          data['name'] = os.path.basename(data['name'])
        elif os.path.exists(self.basePath+self.cwd+data['name']): #file exists
          path = self.cwd+data['name']
        else:                                                     #make up name
          md5sum  = None
        if md5sum is not None:
          if md5sum == "":
            md5sum = hashlib.md5(open(self.basePath+path,'rb').read()).hexdigest()
          view = self.db.getView('viewMD5/viewMD5',md5sum)
          if len(view)==0:  #measurement not in database: create data
            data.update( self.getImage(path,md5sum) )
    # assemble branch information
    data['branch'] = {'stack':hierStack,'child':childNum,'path':path,'op':operation}
    if edit:
      #update document
      data = cT.fillDocBeforeCreate(data, '--', '--').to_dict()
      data = self.db.updateDoc(data, data['_id'])
    else:
      # add data to database
      data = cT.fillDocBeforeCreate(data, data['type'], prefix).to_dict()
      data = self.db.saveDoc(data)

    ## adaptation of directory tree, information on disk: documentID is required
    if self.cwd is not None and data['type'] in self.hierList:
      #project, step, task
      path = data['branch'][0]['path']
      os.makedirs(self.basePath+path, exist_ok=True)
      with open(self.basePath+path+'/.id_jams.json','w') as f:  #local path, update in any case
        f.write(json.dumps(data))
    self.currentID = data['_id']
    logging.debug("addData ending data"+data['_id']+' '+data['_rev']+' '+data['type'])
    return


  def createDirName(self,name,docType,thisChildNumber):
    """ create directory-name by using camelCase and a prefix

    Args:
       name: name with spaces etc.
       docType: document type used for prefix
       thisChildNumber: number of myself
    """
    if 'project' in docType:
      return cT.camelCase(name)
    else:  #steps, tasks
      if isinstance(thisChildNumber, str):
        thisChildNumber = int(thisChildNumber)
      return ("{:03d}".format(thisChildNumber))+'_'+cT.camelCase(name)


  ######################################################
  ### Disk directory/folder methods
  ######################################################
  def changeHierarchy(self, docID, childNum=None):
    """
    Change through text hierarchy structure

    Args:
        id: information on how to change
    """
    if docID is None or docID in self.hierList:  # none, "project", "step", "task" are given: close
      self.hierStack.pop()
      if self.cwd is not None:
        os.chdir('..')
        self.cwd = '/'.join(self.cwd.split('/')[:-2])+'/'
        if self.cwd=='/': self.cwd=''
    else:  # existing ID is given: open that
      try:
        if self.cwd is not None:
          doc = self.db.getDoc(docID)
          path = doc['branch'][0]['path']
          dirName = path.split('/')[-1]
          if childNum is not None:
            dirName = self.createDirName(doc['name'],doc['type'],childNum)
          if not os.path.exists(dirName):
            #should only happen during complex edit: should not get None as childNum
            #move directory
            parentID = doc['branch'][0]['stack'][-1]  #exception is caught correctly
            pathParent = self.db.getDoc(parentID)['branch'][0]['path']
            path = pathParent+os.sep+path.split(os.sep)[-1]
            shutil.move(self.basePath+path, dirName)
            logging.warning('changeHierarchy '+self.cwd+": Could not change into non-existant directory "+dirName+" Moved old one to here")
          os.chdir(dirName)
          self.cwd += dirName+'/'
        self.hierStack.append(docID)
      except:
        print("Could not change into hierarchy. id:"+docID+"  directory:"+dirName+"  cwd:"+self.cwd)
    if self.debug and len(self.hierStack)==len(self.cwd.split(os.sep)):
      logging.error("changeHierarchy error")
    return


  def scanTree(self, method=None):
    """ Scan directory tree recursively from project/...
    - find changes on file system and move those changes to DB
    - use .id_jams.json to track changes of directories, aka projects/steps/tasks
    - use MD5sum to track changes of measurements etc. (one file=one md5sum=one entry in DB)
    - create database entries for measurements in directory
    - move/copy/delete allowed as the doc['path'] = list of all copies
      doc['path'] is adopted once changes are observed

    Args:
      method: 'produceData' copy database entry to file system; for backup: "_jams.json"
              'compareToDB' compare database entry to file system backup to observe accidental changes anyplace
    """
    logging.info("scanTree started with method "+str(method))
    if len(self.hierStack) == 0:
      logging.warning('scanTree: No project selected')
      return
    if   method == "produceData": produceData, compareToDB = True, False
    elif method == "compareToDB": produceData, compareToDB = False, True
    else                        : produceData, compareToDB = False, False

    # get information from database
    view = self.db.getView('viewHierarchy/viewPaths', key=self.hierStack[0])
    database = {} #path as key for lookup, required later
    for item in view:
      thisPath = item['value'][0]
      if thisPath.startswith(self.cwd[:-1]):
        database[thisPath] = [item['id'], item['value'][1], item['value'][2]]

    # iterate directory-tree and compare
    parentID = None
    for path, _, files in os.walk('.'):
      #compare path: project/step/task
      path = os.path.normpath(self.cwd+path)
      if path in database:
        parentID = database[path][0]
        #database and directory agree regarding project/step/task
        #check id-file
        try:
          idFile  = json.load(open(self.basePath+path+'/.id_jams.json'))
          if idFile['branch'][0]['path']==path and idFile['_id']==database[path][0] and idFile['type']==database[path][1]:
            logging.debug(path+' id-test successful on project/step/task')
          else:
            if idFile['_id']==database[path][0] and idFile['type']==database[path][1]:
              logging.warning('produce new .id_jams.json after move of directory')
              data = self.db.getDoc(database[path][0])
              with open(self.basePath+path+'/.id_jams.json','w') as f:
                f.write(json.dumps(data))
            else:
              logging.error(path+' id-test NOT successful on project/step/task')
              logging.error(idFile['branch'][0]['path']+' | '+idFile['_id']+' | '+idFile['type'])
              logging.error(path+' | '+str(database[path]))
          if produceData:
            #if you have to produce
            data = self.db.getDoc(database[path][0])
            with open(self.basePath+path+'/data_jams.json','w') as f:
              f.write(json.dumps(data))
          elif compareToDB:
            #if you have to compare
            docFile = json.load(open(self.basePath+path+'/data_jams.json'))
            docDB = self.db.getDoc(docFile['_id'])
            if docDB==docFile:
              logging.debug(path+' test _jams.json successful on project/step/task')
            else:
              logging.warning(path+' test _jams.json NOT successful on project/step/task')
              logging.warning(docDB)
              logging.warning(docFile)
        except:
          logging.error("scanTree: .id_jams.json file deleted from "+path)
      else:
        if os.path.exists(self.basePath+path+'/.id_jams.json'):
          #update .id_jams.json file and database with new path information
          idFile  = json.load(open(self.basePath+path+'/.id_jams.json'))
          logging.info('Updated path in directory and database '+idFile['branch'][0]['path']+' to '+path)
          data = self.db.updateDoc( {'branch':{'path':path,\
                                               'stack':idFile['branch'][0]['stack'],\
                                               'child':idFile['branch'][0]['child'],\
                                               'op':'u'}}, idFile['_id'])
          with open(self.basePath+path+'/.id_jams.json','w') as f:
            f.write(json.dumps(data))
        else:
          logging.warning(path+' directory (project/step/task) not in database: did user create misc. directory')

      # FILES
      # compare data=files in each path (in each project, step, ..)
      for file in files:
        if '_jams.' in file: continue
        fileName = path+os.sep+file
        jsonFileName = fileName.replace('.','_')+'_jams.json'
        if fileName in database:
          md5File = hashlib.md5(open(self.basePath+fileName,'rb').read()).hexdigest()
          if md5File==database[fileName][2]:
            logging.debug(fileName+'md5-test successful on measurement/etc.')
          else:
            logging.error(fileName+'md5-test NOT successful on measurement/etc.')
          if produceData and not fileName.endswith('_jams.json'):
            #if you have to produce
            data = self.db.getDoc(database[fileName][0])
            with open(self.basePath+jsonFileName,'w') as f:
              f.write(json.dumps(data))
          elif compareToDB:
            #database and directory agree regarding measurement/etc.
            docFile = json.load(open(self.basePath+jsonFileName))
            docDB = self.db.getDoc(docFile['_id'])
            if docDB==docFile:
              logging.debug(fileName+' slow test successful on measurement/etc.')
            else:
              logging.error(fileName+' slow test NOT successful on measurement/etc.')
              logging.error(docDB)
              logging.error(docFile)
          del database[fileName]
        else:
          #not in database, create database entry: if it already exists, self.addData takes care of it
          logging.info(file+' file not in database. Create in database')
          newDoc    = {'name':path+os.sep+file}
          parentDoc = self.db.getDoc(parentID)
          hierStack = []
          for branch in parentDoc['branch']:
            if path in branch['path']:
              hierStack = branch['stack']+[parentID]
          self.addData('measurement', newDoc, hierStack)
      if path in database:
        del database[path]

    ## if path remains, delete it
    for key in database:
      logging.debug("Still in database "+key)
    logging.info("scanTree finished")
    return


  def cleanTree(self, all=True):
    """
    clean all _jams.json files from directories
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
        if file.endswith('_jams.json') and file!='.id_jams.json':
          filePath = os.path.normpath(path+os.sep+file)
          os.remove(filePath)


  def getImage(self, filePath, md5sum, maxSize=600):
    """
    get image from datafile: central distribution point
    - max image size defined here

    Args:
        filePath: path to file
        md5sum: md5sum to store in database (not used here)
        maxSize: maximum size of jpeg images
    """
    logging.info("getImage started for path "+filePath)
    extension = os.path.splitext(filePath)[1][1:]
    if '://' in filePath:
      absFilePath = filePath
      outFile = self.basePath+self.cwd+os.path.basename(filePath).split('.')[0]+'_jams'
    else:
      absFilePath = self.basePath + filePath
      outFile = absFilePath.replace('.','_')+'_jams'
    pyFile = "image_"+extension+".py"
    pyPath = self.softwarePath+'/'+pyFile
    if os.path.exists(pyPath):
      # import module and use to get data
      module = importlib.import_module(pyFile[:-3])
      image, imgType, metaMeasurement = module.getImage(absFilePath)
      # depending on imgType: produce image
      if imgType == "line":  #no scaling
        figfile = StringIO()
        plt.savefig(figfile, format='svg')
        image = figfile.getvalue()
        # 'data:image/svg+xml;utf8,<svg' + figfile.getvalue().split('<svg')[1]
        if self.cwd is not None:
          with open(outFile+'.svg','w') as f:
            figfile.seek(0)
            shutil.copyfileobj(figfile, f)
      elif imgType == "waves":
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
      elif imgType == "contours":
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
        image, metaMeasurement = '', {'measurementType':''}
        logging.error('getImage Not implemented yet 1'+str(imgType))
    else:
      image, metaMeasurement = '', {'measurementType':''}
      logging.warning("getImage: could not find pyFile to convert "+pyFile)
    #produce meta information
    measurementType = metaMeasurement.pop('measurementType')
    meta = {'image': image, 'name': filePath, 'type': 'measurement', 'comment': '',
            'measurementType':measurementType, 'meta':metaMeasurement, 'md5sum':md5sum}
    logging.info("getImage: Image successfully created")
    return meta


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


  def replicateDB(self, remoteDB=None, removeAtStart=False):
    """
    Replicate local database to remote database

    Args:
        remoteDB: if given, use this name for external db
        removeAtStart: remove remote DB before starting new
    """
    if remoteDB is not None:
      self.remoteDB['database'] = remoteDB
    self.db.replicateDB(self.remoteDB, removeAtStart)
    return


  def checkDB(self):
    """
    Wrapper of check database for consistencies by iterating through all documents
    """
    self.db.checkDB(self.basePath)
    return


  ######################################################
  ### OUTPUT COMMANDS and those connected to it      ###
  ######################################################
  def output(self, docLabel, printID=False):
    """
    output view to screen
    - length of output 110 character

    Args:
        docLabel: document label to output
        printID:  include docID in output string
    """
    view = 'view'+docLabel
    outString = []
    docList = self.db.dataLabels+self.db.hierarchyLabels
    idx     = list(dict(docList).values()).index(docLabel)
    docType = list(dict(docList).keys())[idx]
    for item in self.db.dataDictionary[docType][docLabel]:
      key = list(item.keys())[0]
      if item['length']!=0:
        outputString = '{0: <'+str(abs(item['length']))+'}'
        outString.append(outputString.format(key) )
    outString = "|".join(outString)+'\n'
    outString += '-'*110+'\n'
    for lineItem in self.db.getView(view+'/'+view):
      rowString = []
      for idx, item in enumerate(self.db.dataDictionary[docType][docLabel]):
        key = list(item.keys())[0]
        if item['length']!=0:
          outputString = '{0: <'+str(abs(item['length']))+'}'
          if isinstance(lineItem['value'][idx], str ):
            formatString = lineItem['value'][idx]
          else:
            formatString = ' '.join(lineItem['value'][idx])
          if item['length']<0:  #test if value as non-trivial length
            if lineItem['value'][idx]=='true' or lineItem['value'][idx]=='false':
              formatString = lineItem['value'][idx]
            elif len(lineItem['value'][idx])>1 and len(lineItem['value'][idx][0])>3:
              formatString = 'true'
            else:
              formatString = 'false'
            # formatString = True if formatString=='true' else False
          rowString.append(outputString.format(formatString)[:abs(item['length'])] )
      if printID:
        rowString.append(' '+lineItem['id'])
      outString += "|".join(rowString)+'\n'
    return outString


  def outputHierarchy(self, onlyHierarchy=True, addID=False, addTags=None):
    """
    output hierarchical structure in database
    - convert view into native dictionary
    - ignore key since it is always the same

    Args:
       onlyHierarchy: only print project,steps,tasks or print all (incl. measurements...)[default print all]
       addID: add docID to output
       addTags: add tags, comments, objective to output
    """
    if addTags==True or addTags==False:
      print("I AM NOT HERE")
    if len(self.hierStack) == 0:
      logging.warning('jams.outputHierarchy No project selected')
      return "Warning: jams.outputHierarchy No project selected"
    hierString = ' '.join(self.hierStack)
    view = self.db.getView('viewHierarchy/viewHierarchy', key=hierString)
    nativeView = {}
    for item in view:
      if onlyHierarchy and not item['id'].startswith('t-'):
        continue
      nativeView[item['id']] = [item['key']]+item['value']
    if addTags=="all":
      outString = cT.hierarchy2String(nativeView, addID, self.getDoc, 'all')
    elif addTags=="tags":
      outString = cT.hierarchy2String(nativeView, addID, self.getDoc, 'tags')
    else:
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
      return ", ".join([tag for tag in doc['tags']])+' '+doc['comment']
    #complicated style
    return self.outputHierarchy(True,True,'tags')


  def setEditString(self, text):
    """
    Using Org-Mode string, replay the steps to update the database

    Args:
       text: org-mode structured text
    """
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
    children   = [-1]
    for doc in docList:
      #use variables to change directories
      if hierLevel is not None and doc['type']<hierLevel:
        children.pop()
      elif hierLevel is not None and doc['type']>hierLevel:
        children.append(-1)
      children[-1] += 1
      # add elements to doc
      edit = doc['edit'];  del doc['edit']
      doc['type'] = self.hierList[doc['type']]
      if hierLevel is not None and doc['type'] != 'project':
        doc['childNum'] = children[-1]
      if doc['objective']=='': del doc['objective']
      #use variables to change directories
      if hierLevel is not None and self.hierList.index(doc['type'])<hierLevel:
        self.changeHierarchy(None)          #"cd .."
        self.changeHierarchy(None)          #"cd .."
        self.changeHierarchy(doc['_id'],children[-1])    #"cd directory"
      elif hierLevel is not None and self.hierList.index(doc['type'])>hierLevel:
        self.changeHierarchy(doc['_id'],children[-1])    #"cd directory"
      elif hierLevel is not None:
        self.changeHierarchy(None)          #"cd ../directory"
        self.changeHierarchy(doc['_id'],children[-1])
      if edit=='-edit-':
        self.addData(edit, doc, self.hierStack)
      else:
        self.addData(doc['type'], doc)
      #update variables for next iteration
      hierLevel = self.hierList.index(doc['type'])
    #at end, go down ('cd  ..') number of children-length
    for i in range(len(children)-1):
      self.changeHierarchy(None)
    return


  def getChildren(self, docID):
    hierTree = self.outputHierarchy(True,True,False)
    if hierTree is None:
      print("No hierarchy tree")
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


#### Main function when command-line commands used
if __name__ == '__main__':
  import argparse,textwrap
  argparser = argparse.ArgumentParser(usage='''agileScience.py <command> <item>

Possible commands are:
    print: 'Projects', 'Samples', 'Measurements', 'Procedures'
    clean, scan, produce, compare, hierarchy: documentID. To be identified by printing first
        cleaning: docID=all cleans all
    newDB: add/update database configuration. E.g.
        '{"test":{"user":"Peter","password":"Parker",...}}' ''')
  argparser.add_argument("command", help="print, clean, scan, produce, compare, hierarchy, newDB")
  argparser.add_argument("item",    help="'Projects', 'Samples', 'Measurements', 'Procedures', 'documentID'")
  argparser.add_argument("-db","--database", help="name of database configuration")
  args = argparser.parse_args()
  if args.command=="newDB":
    #use new database configuration and store in local-config file
    # no need to touch default databases since database can be chosen by -db
    newDB = json.loads(args.item)
    label = list(newDB.keys()).pop()
    with open(os.path.expanduser('~')+'/.agileScience.json','r') as f:
      configuration = json.load(f)
    configuration[label] = newDB[label]
    with open(os.path.expanduser('~')+'/.agileScience.json','w') as f:
      f.write(json.dumps(configuration, indent=2))
  else:
    #other commands
    try:
      be = AgileScience(args.database)
      if args.command=="print":
        print(be.output(args.item,True))
      elif args.command=='clean' and args.item=='all':
        be.cleanTree(all=True)
      else:
        be.changeHierarchy(args.item)
        if args.command=='clean':
          be.cleanTree(all=False)
        elif args.command=='scan':
          be.scanTree()
        elif args.command=='produce':
          be.scanTree('produceData')
        elif args.command=='compare':
          be.scanTree('compareToDB')
        elif args.command=='hierarchy':
          print(be.outputHierarchy(True,True))
        else:
          print("Wrong command:",args.command)
      be.exit()
    except:
      argparser.print_help()
      exit(1)
