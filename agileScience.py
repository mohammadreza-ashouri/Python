""" Python Backend
"""
import os, json, base64, hashlib, shutil
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

  def __init__(self, databaseName=None):
    """
    open server and define database

    Args:
        databaseName: name of database, otherwise taken from config file
    """
    # open configuration file and define database
    logging.basicConfig(filename='jams.log', filemode='w', format='%(asctime)s %(levelname)s:%(message)s', level=logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("matplotlib.font_manager").setLevel(logging.WARNING)
    logging.info("\nSTART JAMS")
    jsonFile = open(os.path.expanduser('~')+'/.agileScience.json')
    configuration = json.load(jsonFile)
    user         = configuration["user"]
    password     = configuration["password"]
    if databaseName is None:
        databaseName = configuration["database"]
    else:  # if test
        configuration['baseFolder'] = databaseName
    self.db = Database(user, password, databaseName)
    self.userID   = configuration["userID"]
    self.remoteDB = configuration["remote"]
    self.eargs   = configuration["eargs"]
    # open basePath (root of directory tree) as current working directory
    # self.cwd is the addition to basePath
    self.softwarePath = os.path.abspath(os.getcwd())
    self.basePath     = os.path.expanduser('~')+"/"+configuration["baseFolder"]
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
    data['client'] = 'python version 0.1'
    if len(hierStack) == 0:
      hierStack = list(self.hierStack)
    # collect data and prepare
    if docType != '-edit-':

      #new document: basic items
      data['type'] = docType
      if docType in self.hierList and docType!='project':
        #should not have childnumber in other cases for debugging
        thisStack = ' '.join(self.hierStack)
        view = self.db.getView('viewHierarchy/viewHierarchy', key=self.hierStack[0]) #not faster with cT.getChildren
        thisChildNumber = 0
        for item in view:
          if item['value'][2]=='project': continue
          if item['value'][0] == thisStack:
            thisChildNumber += 1
        data['childNum'] = thisChildNumber
      if docType in self.hierList:
        prefix = 't'
      else:
        prefix = docType[0]

      # find path name on local file system; name can be anything
      if self.cwd is not None:
        if docType in self.hierList:
          #project, step, task
          if docType=='project': thisChildNumber = -1
          data['path'] = [self.cwd + self.createDirName(data['name'],data['type'],thisChildNumber)]
        else:
          #measurement, sample, procedure
          md5sum = ""
          if '://' in data['name']:                                 #make up name
            if localCopy:
              data['path'] = [self.cwd + cT.camelCase( os.path.basename(data['name']))]
              request.urlretrieve(data['name'], self.basePath+data['path'])
            else:
              md5sum  = hashlib.md5(request.urlopen(data['name']).read()).hexdigest()            #TODO what to do when request fails: try: except:
          elif os.path.exists(self.basePath+data['name']):          #file exists
            data['path'] = [data['name']]
            data['name'] = os.path.basename(data['name'])
          elif os.path.exists(self.basePath+self.cwd+data['name']): #file exists
            data['path'] = [self.cwd+data['name']]
          else:                                                     #make up name
            md5sum  = None
          if md5sum is not None:
            if md5sum == "":
              md5sum = hashlib.md5(open(self.basePath+data['path'][0],'rb').read()).hexdigest()
            view = self.db.getView('viewMD5/viewMD5',md5sum)
            if len(view)>0:
              #update only path, no addition
              self.db.updateDoc(data,view[0]['id'])
              return
            if 'path' in data and len(data['path'])>0:
              data.update( self.getImage(data['path'][0],md5sum) )
            else:
              data.update( self.getImage(data['name'],md5sum) )

      # add data to database
      data = cT.fillDocBeforeCreate(data, docType, hierStack, prefix).to_dict()
      data = self.db.saveDoc(data)
    else:
      #update document
      data = cT.fillDocBeforeCreate(data, '--', hierStack[:-1], '--').to_dict()
      data = self.db.updateDoc(data,self.hierStack[-1])

    ## adaptation of directory tree, information on disk: documentID is required
    if self.cwd is not None:
      if data['type'] in self.hierList:
        #project, step, task
        os.makedirs(self.basePath+data['path'][0], exist_ok=True)
        with open(self.basePath+data['path'][0]+'/.id_jams.json','w') as f:  #local path
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
  def changeHierarchy(self, id):
    """
    Change through text hierarchy structure

    Args:
        id: information on how to change
    """
    if id is None or id in self.hierList:  # "project", "step", "task" are given: close
      self.hierStack.pop()
      if self.cwd is not None:
        os.chdir('..')
        self.cwd = '/'.join(self.cwd.split('/')[:-2])+'/'
        if self.cwd=='/': self.cwd=''
    else:  # existing project ID is given: open that
      if self.cwd is not None:
        path = self.db.getDoc(id)['path'][0]
        dirName = path.split('/')[-1]
        if os.path.exists(dirName):
          os.chdir(dirName)
          self.cwd += dirName+'/'
        else:
          logging.warning('changeHierarchy '+self.cwd+": Cannot change into non-existant directory "+dirName+" Nothing done")
          return
      self.hierStack.append(id)
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
    database = {}
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
          if idFile['path'][0]==path and idFile['_id']==database[path][0] and idFile['type']==database[path][1]:
            logging.debug(path+'id-test successful on project/step/task')
          else:
            logging.error(path+'id-test NOT successful on project/step/task')
            logging.error(idFile['path'][0],idFile['_id'],idFile['type'])
            logging.error(path, database[path])
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
              logging.debug(path+'test _jams.json successful on project/step/task')
            else:
              logging.warning(path+'test _jams.json NOT successful on project/step/task')
              logging.warning(docDB)
              logging.warning(docFile)
        except:
          logging.error("scanTree: .id_jams.json file deleted from "+path)
      else:
        if os.path.exists(self.basePath+path+'/.id_jams.json'):
          #update .id_jams.json file and database with new path information
          idFile  = json.load(open(self.basePath+path+'/.id_jams.json'))
          logging.info('Updated path in directory and database '+idFile['path'][0]+' to '+path)
          data = self.db.updateDoc( {'path':[path]}, idFile['_id'])
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
          hierStack = parentDoc['inheritance']+[parentID]
          self.addData('measurement', newDoc, hierStack)
      if path in database:
        del database[path]

    ## if path remains, delete it
    for key in database:
      logging.debug("Remove path "+key+" from database id "+database[key][0])
      data = self.db.updateDoc( {'path':key}, database[key][0])
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
  ### Get data from database
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


  ######################################################
  ### OUTPUT COMMANDS ###
  ######################################################
  def output(self, docLabel):
    """
    output view to screen
    - length of output 110 character

    Args:
        docLabel: document label to output
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
            elif len(lineItem['value'][idx])>1 or len(lineItem['value'][idx][0])>3:
              formatString = 'true'
            else:
              formatString = 'false'
            # formatString = True if formatString=='true' else False
          rowString.append(outputString.format(formatString)[:abs(item['length'])] )
      outString += "|".join(rowString)+'\n'
    return outString


  def outputHierarchy(self, onlyHierarchy=True, addID=False):
    """
    output hierarchical structure in database
    - convert view into native dictionary
    - ignore key since it is always the same

    Args:
       onlyHierarchy: only print project,steps,tasks or print all (incl. measurements...)[default print all]
       addID: add docID to output
    """
    if len(self.hierStack) == 0:
      logging.warning('jams.outputHierarchy No project selected')
      return
    projectID = self.hierStack[0]
    view = self.db.getView('viewHierarchy/viewHierarchy', key=projectID)
    nativeView = {}
    for item in view:
      if onlyHierarchy and not item['id'].startswith('t-'):
        continue
      nativeView[item['id']] = item['value']
    outString = cT.hierarchy2String(nativeView, addID)
    outString = outString.replace(': undefined',': -1')
    return outString


  def getEditString(self):
    """ Return Markdown string of hierarchy tree
    """
    if self.eargs['style']=='simple':
      doc = self.db.getDoc(self.hierStack[-1])
      return ", ".join([tag for tag in doc['tags']])+' '+doc['comment']
    #complicated style
    outString = ""
    for line in self.outputHierarchy(True,True).split('\n'):
      arrayLine = line.split(': ')
      prefix  = arrayLine[0].split()[0]
      body    = ': '.join(arrayLine[1:-1])
      doc     = self.getDoc(arrayLine[2])
      tagString=' '.join(doc['tags'])
      comments= doc['comment']
      outString += prefix+' '+body+'\n'
      if 'objective' in doc:
        outString += "Objective: "+doc['objective']+'\n'
      outString += 'Tags: '+tagString+'\n'+comments+'\n'
    return outString


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
