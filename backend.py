#!/usr/bin/python3
""" Python Backend: all operations with the filesystem are here
"""

class Pasta:
  """
  PYTHON BACKEND
  """

  def __init__(self, configName=None, confirm=None, **kwargs):
    """
    open server and define database

    Args:
        configName (string): name of configuration used; if not given, use the one defined by '-defaultLocal' in config file
        confirm (function): confirm changes to database and file-tree
        kwargs (dict): additional parameters
          - initViews (bool): initialize views at startup
          - initConfig (bool): skip initialization of .pasta.json configuration file
          - resetOntology (bool): reset ontology on database from one on file
    """
    import os, logging, json, sys
    from database import Database
    from miscTools import upIn, upOut
    from commonTools import commonTools as cT
    ## CONFIGURATION FOR DATALAD and GIT: has to move to dictionary
    self.vanillaGit = ['*.md','*.rst','*.org','*.tex','*.py','.id_pasta.json'] #tracked but in git;
    #   .id_pasta.json has to be tracked by git (if ignored: they don't appear on git-status; they have to change by PASTA)
    self.gitIgnore = ['*.log','.vscode/','*.xcf','*.css'] #misc
    self.gitIgnore+= ['*.bcf','*.run.xml','*.synctex.gz','*.aux']#latex files
    self.gitIgnore+= ['*.pdf','*.png','*.svg','*.jpg']           #result figures
    self.gitIgnore+= ['*.hap','*.mss','*.mit','*.mst']   #extractors do not exist yet

    # open configuration file
    self.debug = True
    self.confirm = confirm
    with open(os.path.expanduser('~')+'/.pasta.json','r') as f:
      configuration = json.load(f)
    changed = False
    if kwargs.get('initConfig', True):
      for item in configuration:
        if 'user' in configuration[item] and 'password' in configuration[item]:
          configuration[item]['cred'] = upIn(configuration[item]['user']+':'+configuration[item]['password'])
          del configuration[item]['user']
          del configuration[item]['password']
          changed = True
      if changed:
        with open(os.path.expanduser('~')+'/.pasta.json','w') as f:
          f.write(json.dumps(configuration,indent=2))
    if configName is None:
      configName = configuration['-defaultLocal']
    remoteName= configuration['-defaultRemote']
    n,s       = None,None
    if 'user' in configuration[configName]:
      n,s     = configuration[configName]['user'], configuration[configName]['password']
    else:
      n,s      = upOut(configuration[configName]['cred']).split(':')
    databaseName = configuration[configName]['database']
    self.configName=configName
    # directories
    #    self.basePath (root of directory tree) is root of all projects
    #    self.cwd changes during program
    self.softwarePath = os.path.dirname(os.path.abspath(__file__))
    self.basePath     = configuration[configName]['path']
    self.cwd          = ''
    if not self.basePath.endswith(os.sep):
      self.basePath += os.sep
    if os.path.exists(self.basePath):
      os.chdir(self.basePath)
    else:
      print('**ERROR bin01: Base folder did not exist |'+self.basePath)
      sys.exit(1)
    sys.path.append(self.softwarePath+os.sep+'extractors')  #allow extractors
    # start logging
    logging.basicConfig(filename=self.softwarePath+os.sep+'pasta.log', format='%(asctime)s|%(levelname)s:%(message)s', datefmt='%m-%d %H:%M:%S' ,level=logging.DEBUG)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('datalad').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
    logging.info('\nSTART PASTA '+configName)
    # decipher configuration and store
    self.userID   = configuration['-userID']
    self.remoteDB = configuration[remoteName]
    self.eargs   = configuration['-eargs']
    self.magicTags= configuration['-magicTags'] #"P1","P2","P3","TODO","WAIT","DONE"
    self.tableFormat = configuration['-tableFormat-']
    # start database
    self.db = Database(n, s, databaseName, confirm=self.confirm, softwarePath=self.softwarePath+os.sep, **kwargs)
    res = cT.ontology2Labels(self.db.ontology,self.tableFormat)
    self.dataLabels      = res['dataDict']
    self.hierarchyLabels = res['hierarchyDict']
    if kwargs.get('initViews', False):
      labels = {}  #one line merging / update does not work
      for i in res['dataDict']:
        labels[i]=res['dataDict'][i]
      for i in res['hierarchyDict']:
        labels[i]=res['hierarchyDict'][i]
      self.db.initViews(labels,self.magicTags)
    # internal hierarchy structure
    self.hierStack = []
    self.currentID  = None
    self.alive     = True
    return


  def exit(self, deleteDB=False, **kwargs):
    """
    Shutting down things

    Args:
      deleteDB (bool): remove database
      kwargs (dict): additional parameter
    """
    import os, time, logging
    if deleteDB:
      #uninit / delete everything of git-annex and datalad
      for root, dirs, files in os.walk(self.basePath):
        for momo in dirs:
          os.chmod(os.path.join(root, momo), 0o755)
        for momo in files:
          os.chmod(os.path.join(root, momo), 0o755)
    os.chdir(self.softwarePath)  #where program started
    self.db.exit(deleteDB)
    self.alive     = False
    logging.info('\nEND PASTA')
    logging.shutdown()
    return


  ######################################################
  ### Change in database
  ######################################################
  def addData(self, docType, doc, hierStack=None, localCopy=False, **kwargs):
    """
    Save doc to database, also after edit

    Args:
        docType (string): docType to be stored, subtypes are / separated
        doc (dict): to be stored
        hierStack (list): hierStack from external functions
        localCopy (bool): copy a remote file to local version
        kwargs (dict): additional parameter, i.e. callback for curation
            forceNewImage (bool): create new image in any case

    Returns:
        bool: success
    """
    import logging, sys, os, json
    from urllib import request
    import datalad.api as datalad
    from commonTools import commonTools as cT
    from miscTools import createDirName, generic_hash
    if sys.platform=='win32':
      import win32con, win32api

    if hierStack is None:
      hierStack=[]
    logging.debug('addData beginning doc: '+docType+' | hierStack'+str(hierStack))
    callback = kwargs.get('callback', None)
    forceNewImage=kwargs.get('forceNewImage',False)
    doc['-user']  = self.userID
    childNum     = doc.pop('childNum',None)
    path         = None
    operation    = 'c'  #operation of branch/path
    if docType == '-edit-':
      edit = True
      if '-type' not in doc:
        doc['-type'] = ['x'+str(len(self.hierStack))]
      if len(hierStack) == 0:
        hierStack = self.hierStack
      if '_id' not in doc:
        doc['_id'] = hierStack[-1]
      if len(hierStack)>0 and doc['-type'][0][0]=='x':
        hierStack   = hierStack[:-1]
      elif '-branch' in doc:
        hierStack   = doc['-branch'][0]['stack']
    else:  #new doc
      edit = False
      doc['-type'] = docType.split('/')
      if len(hierStack) == 0:
        hierStack = self.hierStack

    # collect structure-doc and prepare
    if doc['-type'][0][0]=='x' and doc['-type'][0]!='x0' and childNum is None:
      #should not have childnumber in other cases
      thisStack = ' '.join(self.hierStack)
      view = self.db.getView('viewHierarchy/viewHierarchy', startKey=thisStack) #not faster with cT.getChildren
      childNum = 0
      for item in view:
        if item['value'][1][0]=='x0': continue
        if thisStack == ' '.join(item['key'].split(' ')[:-1]): #remove last item from string
          childNum += 1

    # find path name on local file system; name can be anything
    if self.cwd is not None and 'name' in doc:
      if (doc['name'].endswith('_pasta.jpg') or
          doc['name'].endswith('_pasta.svg') or
          doc['name'].endswith('.id_pasta.json') ):
        print("**Warning DO NOT ADD _pasta. files to database")
        return False
      if doc['-type'][0][0]=='x':
        #project, step, task
        if doc['-type'][0]=='x0':
          childNum = 0
        if edit:      #edit: cwd of the project/step/task: remove last directory from cwd (since cwd contains a / at end: remove two)
          parentDirectory = os.sep.join(self.cwd.split(os.sep)[:-2])
          if len(parentDirectory)>2:
            parentDirectory += os.sep
        else:         #new: below the current project/step/task
          parentDirectory = self.cwd
        path = parentDirectory + createDirName(doc['name'],doc['-type'][0],childNum) #update,or create (if new doc, update ignored anyhow)
        operation = 'u'
      else:
        #measurement, sample, procedure
        shasum = ''
        if '://' in doc['name']:                                 #make up name
          if localCopy:
            baseName, extension = os.path.splitext(os.path.basename(doc['name']))
            path = self.cwd + cT.camelCase(baseName)+extension
            request.urlretrieve(doc['name'], self.basePath+path)
            doc['name'] = cT.camelCase(baseName)+extension
          else:
            path = doc['name']
            try:
              shasum  = generic_hash(doc['name'])
            except:
              print('**ERROR bad01: fetch remote content failed. Data not added')
              return False
        elif doc['name']!='' and os.path.exists(self.basePath+doc['name']):          #file exists
          path = doc['name']
          doc['name'] = os.path.basename(doc['name'])
        elif doc['name']!='' and os.path.exists(self.basePath+self.cwd+doc['name']): #file exists
          path = self.cwd+doc['name']
        else:                                                     #make up name
          shasum  = None
        if shasum is not None: # and doc['-type'][0]=='measurement':         #samples, procedures not added to shasum database, getMeasurement not sensible
          if shasum == '':
            shasum = generic_hash(self.basePath+path, forceFile=True)
          view = self.db.getView('viewIdentify/viewSHAsum',shasum)
          if len(view)==0 or forceNewImage:  #measurement not in database: create doc
            while True:
              self.useExtractors(path,shasum,doc)  #create image/content and add to datalad
              if not 'image' in doc and not 'content' in doc:  #did not get valuable data: extractor does not exit
                return False
              if callback is None or not callback(doc):
                # if no more iterations of curation
                if 'ignore' in doc:
                  ignore = doc['ignore']; del doc['ignore']
                  if ignore=='dir':
                    projPath = self.basePath + path.split(os.sep)[0]
                    dirPath =  os.path.relpath(os.path.split(self.basePath+path)[0] , projPath)
                    with open(projPath+os.sep+'.gitignore','a') as fOut:
                      fOut.write(dirPath+os.sep+'\n')
                    if sys.platform=='win32':
                      win32api.SetFileAttributes(projPath+os.sep+'.gitignore',win32con.FILE_ATTRIBUTE_HIDDEN)
                  if ignore!='none':  #ignored images are added to datalad but not to database
                    return False
                break
          if len(view)==1:  #measurement is already in database
            self.useExtractors(path,shasum,doc,exitAfterDataLad=True)
            doc['_id'] = view[0]['id']
            doc['shasum'] = shasum
            edit = True
    # assemble branch information
    if childNum is None:
      childNum=9999
    doc['-branch'] = {'stack':hierStack,'child':childNum,'path':path,'op':operation}
    if edit:
      #update document
      keysNone = [key for key in doc if doc[key] is None]
      doc = cT.fillDocBeforeCreate(doc, '--').to_dict()  #store None entries and save back since js2py gets equalizes undefined and null
      for key in keysNone:
        doc[key]=None
      doc = self.db.updateDoc(doc, doc['_id'])
    else:
      # add doc to database
      doc = cT.fillDocBeforeCreate(doc, doc['-type']).to_dict()
      doc = self.db.saveDoc(doc)

    ## adaptation of directory tree, information on disk: documentID is required
    if self.cwd is not None and doc['-type'][0][0]=='x':
      #project, step, task
      path = doc['-branch'][0]['path']
      if not edit:
        if doc['-type'][0]=='x0':
          ## shell command
          # cmd = ['datalad','create','--description','"'+doc['objective']+'"','-c','text2git',path]
          # _ = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
          # datalad api version: produces undesired output
          try:
            description = doc['objective'] if 'objective' in doc else '_'
            datalad.create(path,description=description)
          except:
            print('**ERROR bad02: Tried to create new datalad folder which did already exist')
            raise
          gitAttribute = '\n* annex.backend=SHA1\n**/.git* annex.largefiles=nothing\n'
          for fileI in self.vanillaGit:
            gitAttribute += fileI+' annex.largefiles=nothing\n'
          gitIgnore = '\n'.join(self.gitIgnore)
          with open(path+os.sep+'.gitattributes','w') as fOut:
            fOut.write(gitAttribute+'\n')
          if sys.platform=='win32':
            win32api.SetFileAttributes(path+os.sep+'.gitattributes',win32con.FILE_ATTRIBUTE_HIDDEN)
          with open(path+os.sep+'.gitignore','w') as fOut:
            fOut.write(gitIgnore+'\n')
          if sys.platform=='win32':
            win32api.SetFileAttributes(path+os.sep+'.gitignore',win32con.FILE_ATTRIBUTE_HIDDEN)
          dlDataset = datalad.Dataset(path)
          dlDataset.save(path='.',message='changed gitattributes')
        else:
          os.makedirs(self.basePath+path, exist_ok=True)   #if exist, create again; moving not necessary since directory moved in changeHierarchy
      projectPath = path.split(os.sep)[0]
      dataset = datalad.Dataset(self.basePath+projectPath)
      if os.path.exists(self.basePath+path+os.sep+'.id_pasta.json'):
        if sys.platform=='win32':
          if win32api.GetFileAttributes(self.basePath+path+os.sep+'.id_pasta.json')==win32con.FILE_ATTRIBUTE_HIDDEN:
            win32api.SetFileAttributes(self.basePath+path+os.sep+'.id_pasta.json',win32con.FILE_ATTRIBUTE_ARCHIVE)
        else:
          dataset.unlock(path=self.basePath+path+os.sep+'.id_pasta.json')
      with open(self.basePath+path+os.sep+'.id_pasta.json','w') as f:  #local path, update in any case
        f.write(json.dumps(doc))
      if sys.platform=='win32':
        win32api.SetFileAttributes(self.basePath+path+os.sep+'.id_pasta.json',win32con.FILE_ATTRIBUTE_HIDDEN)
      # datalad api version
      dataset.save(path=self.basePath+path+os.sep+'.id_pasta.json', message='Added new subfolder with .id_pasta.json')
      ## shell command
      # cmd = ['datalad','save','-m','Added new subfolder with .id_pasta.json', '-d', self.basePath+projectPath ,self.basePath+path+os.sep+'.id_pasta.json']
      # output = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
      # print("datalad save",output.stdout.decode('utf-8'))
    self.currentID = doc['_id']
    logging.debug('addData ending doc '+doc['_id']+' '+doc['-type'][0])
    return True


  ######################################################
  ### Disk directory/folder methods
  ######################################################
  def changeHierarchy(self, docID, dirName=None, **kwargs):
    """
    Change through text hierarchy structure
    change hierarchyStack, change directory, change stored cwd

    Args:
        docID (string): information on how to change
        dirName (string): use this name to change into
        kwargs (dict): additional parameter
    """
    import os, logging
    if docID is None or (docID[0]=='x' and docID[1]!='-'):  # none, 'project', 'step', 'task' are given: close
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
            path = doc['-branch'][0]['path']
            dirName = path.split(os.sep)[-1]
          os.chdir(dirName)     #exception caught
          self.cwd += dirName+os.sep
        self.hierStack.append(docID)
      except:
        print('**ERROR bch01: Could not change into hierarchy. id|'+docID+'  directory:'+dirName+'  cwd:'+self.cwd)
    if self.debug and len(self.hierStack)+1!=len(self.cwd.split(os.sep)):
      logging.error('changeHierarchy error')
    return


  def scanTree(self, **kwargs):
    """ Scan directory tree recursively from project/...
    - find changes on file system and move those changes to DB
    - use .id_pasta.json to track changes of directories, aka projects/steps/tasks
    - use shasum to track changes of measurements etc. (one file=one shasum=one entry in DB)
    - create database entries for measurements in directory
    - move/copy/delete allowed as the doc['path'] = list of all copies
      doc['path'] is adopted once changes are observed

    Args:
      kwargs (dict): additional parameter, i.e. callback

    Raises:
      ValueError: could not add new measurement to database
    """
    import logging, os, shutil
    import datalad.api as datalad
    from datalad.support import annexrepo
    from miscTools import bcolors, generic_hash
    logging.info('scanTree started')
    if len(self.hierStack) == 0:
      print(f'{bcolors.FAIL}**Warning - scan directory: No project selected{bcolors.ENDC}')
      return
    callback = kwargs.get('callback', None)
    while len(self.hierStack)>1:
      self.changeHierarchy(None)

    #git-annex lists all the files at once
    #   datalad and git give the directories, if untracked/random; and datalad status produces output
    #   also, git-annex status is empty if nothing has to be done
    #   git-annex output is nice to parse
    fileList = annexrepo.AnnexRepo('.').status()
    dlDataset = datalad.Dataset('.')
    #create dictionary that has shasum as key and [origin and target] as value
    shasumDict = {}   #clean ones are omitted
    for posixPath in fileList:
      fileName = os.path.relpath(str(posixPath), self.basePath+self.cwd)
      # if fileList[posixPath]['state']=='clean': #for debugging
      #   shasum = generic_hash(fileName)
      #   print(shasum,fileList[posixPath]['prev_gitshasum'],fileList[posixPath]['gitshasum'],fileName)
      if fileList[posixPath]['state']=='untracked':
        shasum = generic_hash(fileName)
        if shasum in shasumDict:
          shasumDict[shasum] = [shasumDict[shasum][0],fileName]
        else:
          shasumDict[shasum] = ['',fileName]
      if fileList[posixPath]['state']=='deleted':
        shasum = fileList[posixPath]['prev_gitshasum']
        if shasum in shasumDict:
          shasumDict[shasum] = [fileName, shasumDict[shasum][1]]
        else:
          shasumDict[shasum] = [fileName, '']
      if fileList[posixPath]['state']=='modified':
        shasum = fileList[posixPath]['gitshasum']
        shasumDict[shasum] = ['', fileName] #new content is same place. No moving necessary, just "new file"

    # loop all entries and separate into moved,new,deleted
    print("Number of changed files:",len(shasumDict))
    for shasum in shasumDict:
      origin, target = shasumDict[shasum]
      print("  File changed:",origin,target)
      # originDir, _ = os.path.split(self.cwd+origin)
      targetDir, _ = os.path.split(self.cwd+target)
      # find hierStack and parentID of new TARGET location: for new and move
      if target != '':
        if not os.path.exists(target): #if dead link
          linkTarget = os.readlink(target)
          for dirI in os.listdir(self.basePath):
            if os.path.isdir(self.basePath+dirI):
              path = self.basePath+dirI+os.sep+linkTarget
              if os.path.exists(path):
                os.unlink(target)
                shutil.copy(path,target)
                logging.info("Repaired broken link "+path+' -> '+target)
                break
        parentID = None
        itemTarget = -1
        while parentID is None:
          view = self.db.getView('viewHierarchy/viewPaths', startKey=targetDir)
          for item in view:
            if item['key']==targetDir:
              parentID = item['id']
              itemTarget = item
          targetDir = os.sep.join(targetDir.split(os.sep)[:-1])
        parentDoc = self.db.getDoc(parentID)
        hierStack = parentDoc['-branch'][0]['stack']+[parentID]
      ### separate into two cases
      # newly created file
      if origin == '':
        logging.info('Info: scanTree file not in database '+target)
        newDoc    = {'name':self.cwd+target}
        _ = self.addData('measurement', newDoc, hierStack, callback=callback)  #saved to datalad in here
      # move or delete file
      else:
        #update to datalad
        if target == '':
          dlDataset.save(path=origin, message='Removed file')
        else:
          dlDataset.save(path=origin, message='Moved file from here to '+self.cwd+target   )
          dlDataset.save(path=target, message='Moved file from '+self.cwd+origin+' to here')
        #get docID
        if origin.endswith('.id_pasta.json'):
          origin = os.path.split(origin)[0]
        if target.endswith('.id_pasta.json'):
          target = os.path.split(target)[0]
        view = self.db.getView('viewHierarchy/viewPaths', preciseKey=self.cwd+origin )
        if len(view)==1:
          docID = view[0]['id']
          if target == '':       #delete
            self.db.updateDoc( {'-branch':{'path':self.cwd+origin, 'oldpath':self.cwd+origin,\
                                          'stack':[None],\
                                          'child':-1,\
                                          'op':'d'}}, docID)
          else:                  #update
            self.db.updateDoc( {'-branch':{'path':self.cwd+target, 'oldpath':self.cwd+origin,\
                                          'stack':hierStack,\
                                          'child':itemTarget['value'][2],\
                                          'op':'u'}}, docID)
        else:
          if not '_pasta.' in origin:
            print("file not in database",self.cwd+origin)
    return


  def backup(self, method='backup', zipFileName=None, **kwargs):
    """
    backup, verify, restore information from/to database
    - documents are named: (docID).json
    - all data is saved to one zip file
    - after restore-to-database, the database changed (new revision)

    Args:
      method (string): backup, restore, compare
      zipFileName (string): specific unique name of zip-file
      kwargs (dict): additional parameter, i.e. callback

    Returns:
        bool: success
    """
    import os, json
    from zipfile import ZipFile, ZIP_DEFLATED
    if zipFileName is None and self.cwd is None:
      print("**ERROR bbu01: Specify zip file name")
      return False
    if zipFileName is None: zipFileName="pasta_backup.zip"
    if os.sep not in zipFileName:
      zipFileName = self.basePath+zipFileName
    if method=='backup':  mode = 'w'
    else:                 mode = 'r'
    print('  '+method.capitalize()+' to file: '+zipFileName)
    with ZipFile(zipFileName, mode, compression=ZIP_DEFLATED) as zipFile:

      # method backup, iterate through all database entries and save to file
      if method=='backup':
        numAttachments = 0
        for doc in self.db.db:
          fileName = doc['_id']+'.json'
          zipFile.writestr(fileName, json.dumps(doc) )
          if '_attachments' in doc:
            numAttachments += len(doc['_attachments'])
            for i in range(len(doc['_attachments'])):
              attachmentName = doc['_id']+'/v'+str(i)+'.json'
              zipFile.writestr(attachmentName, json.dumps(doc.get_attachment('v'+str(i)+'.json')))
        compressed, fileSize = 0,0
        for doc in zipFile.infolist():
          compressed += doc.compress_size
          fileSize   += doc.file_size
        print(f'  File size: {fileSize:,} byte   Compressed: {compressed:,} byte')
        print(f'  Num. documents (incl. ontology and views): {len(self.db.db):,},    num. attachments: {numAttachments:,}\n')
        return True

      # method compare
      if  method=='compare':
        filesInZip = zipFile.namelist()
        print('  Number of documents (incl. ontology and views) in file:',len(filesInZip))
        differenceFound, comparedFiles, comparedAttachments = False, 0, 0
        for doc in self.db.db:
          fileName = doc['_id']+'.json'
          if fileName not in filesInZip:
            print("**ERROR bbu02: document not in zip file |",doc['_id'])
            differenceFound = True
          else:
            filesInZip.remove(fileName)
            zipData = json.loads( zipFile.read(fileName) )
            if doc!=zipData:
              print('  Info: data disagrees database, zipfile ',doc['_id'])
              differenceFound = True
            comparedFiles += 1
          if '_attachments' in doc:
            for i in range(len(doc['_attachments'])):
              attachmentName = doc['_id']+'/v'+str(i)+'.json'
              if attachmentName not in filesInZip:
                print("**ERROR bbu03: revision not in zip file |",attachmentName)
                differenceFound = True
              else:
                filesInZip.remove(attachmentName)
                zipData = json.loads( zipFile.read(attachmentName) )
                if doc.get_attachment('v'+str(i)+'.json')!=zipData:
                  print('  Info: data disagrees database, zipfile ',attachmentName)
                  differenceFound = True
                comparedAttachments += 1
        if len(filesInZip)>0:
          differenceFound = True
          print('Files in zipfile not in database',filesInZip)
        if differenceFound: print("  Difference exists between database and zipfile")
        else:               print("  Database and zipfile are identical.",comparedFiles,'files &',comparedAttachments,'attachments were compared\n')
        return not differenceFound

      # method restore: loop through all files in zip and save to database
      #  - skip design and dataDictionary
      if method=='restore':
        beforeLength, restoredFiles = len(self.db.db), 0
        for fileName in zipFile.namelist():
          if not ( fileName.startswith('_') or fileName.startswith('-') ):  #do not restore design documents and ontology
            restoredFiles += 1
            zipData = json.loads( zipFile.read(fileName) )
            if '/' in fileName:                                             #attachment
              doc = self.db.getDoc(fileName.split('/')[0])
              doc.put_attachment(fileName.split('/')[1], 'application/json', json.dumps(zipData))
            else:                                                           #normal document
              self.db.saveDoc(zipData)
        print('  Number of documents & revisions in file:',restoredFiles)
        print('  Number of documents before and after restore:',beforeLength, len(self.db.db),'\n')
        return True
    return False


  def useExtractors(self, filePath, shasum, doc, **kwargs):
    """
    get measurements from datafile: central distribution point
    - max image size defined here

    Args:
        filePath (string): path to file
        shasum (string): shasum (git-style hash) to store in database (not used here)
        doc (dict): pass known data/measurement type, can be used to create image; This doc is altered
        kwargs (dict): additional parameter
          - maxSize of image
          - extractorTest: test the extractor and show image
          - saveToFile: save data to files
    """
    import logging, os, importlib, base64, shutil, json
    from io import StringIO, BytesIO
    import numpy as np
    import matplotlib.pyplot as plt
    from PIL.Image import Image
    import datalad.api as datalad
    logging.debug('useExtractors started for path '+filePath)
    maxSize = kwargs.get('maxSize', 600)
    extractorTest    = kwargs.get('extractorTest', False)
    exitAfterDataLad = kwargs.get('exitAfterDataLad',False)
    saveToFile       = kwargs.get('saveToFile',False)
    extension = os.path.splitext(filePath)[1][1:]
    if '://' in filePath:
      absFilePath = filePath
      outFile = self.basePath+self.cwd+os.path.basename(filePath).split('.')[0]+'_pasta'
      projectDB = self.cwd.split(os.sep)[0]
      dataset = datalad.Dataset(self.basePath+projectDB)
    else:
      parentPath = filePath.split(os.sep)[0]
      if not extractorTest:
        dataset = datalad.Dataset(self.basePath+parentPath)
        if dataset.id:
          dataset.save(path=self.basePath+filePath, message='Added locked document')
        if exitAfterDataLad:
          return
      absFilePath = self.basePath + filePath
      outFile = self.basePath + filePath.replace('.','_')+'_pasta'
    pyFile = 'extractor_'+extension+'.py'
    pyPath = self.softwarePath+os.sep+'extractors'+os.sep+pyFile
    if len(doc['-type'])==1:
      doc['-type'] += [extension]
    if os.path.exists(pyPath):
      # import module and use to get data
      module = importlib.import_module(pyFile[:-3])
      content, [imgType, docType, metaVendor, metaUser] = module.use(absFilePath, doc)
      # tests whether meta data JSON format
      try:
        for i in metaUser:
          if isinstance(metaUser[i], np.int64):
            metaUser[i] = int(metaUser[i])
          if isinstance(metaUser[i], np.ndarray):
            metaUser[i] = str(list(metaUser[i]))
        _ = json.dumps(metaUser, cls=json.JSONEncoder)
      except:
        print('**ERROR bue01a: metaUSER not json format |',metaUser,'\n')
        metaUser = {'error':str(metaUser)}
      try:
        for i in metaVendor:
          if isinstance(metaVendor[i], np.int64):
            metaVendor[i] = int(metaVendor[i])
          if isinstance(metaVendor[i], np.ndarray):
            metaVendor[i] = str(list(metaVendor[i]))
        _ = json.dumps(metaVendor, cls=json.JSONEncoder)
      except:
        print('**ERROR bue01b: metaVENDOR not json format |',metaVendor,'\n')
        metaVendor = {'error':str(metaVendor)}
      if type(docType)==list:
        document = {'-type': docType, 'metaUser':metaUser, 'metaVendor':metaVendor, 'shasum':shasum}
      elif type(docType)==dict:
        document = docType
        document['metaUser']  = metaUser
        document['metaVendor']= metaVendor
        document['shasum']    = shasum
      else:
        print('**ERROR bue01c: invalid docType type list,dict |',type(docType),'\n')
      # end tests
      if extractorTest:
        if isinstance(content, Image):
          content.show()
        else:
          plt.show()
      # depending on imgType: produce image
      outFileFull = None
      if imgType == 'svg':  #no scaling
        figfile = StringIO()
        plt.savefig(figfile, format='svg')
        content = figfile.getvalue()
        # 'data:image/svg+xml;utf8,<svg' + figfile.getvalue().split('<svg')[1]
        outFileFull = outFile+'.svg'
      elif imgType == 'jpg':
        ratio = maxSize / content.size[np.argmax(content.size)]
        content = content.resize((np.array(content.size)*ratio).astype(int)).convert('RGB')
        figfile = BytesIO()
        content.save(figfile, format='JPEG')
        imageData = base64.b64encode(figfile.getvalue()).decode()
        content = 'data:image/jpg;base64,' + imageData
        outFileFull = outFile+'.jpg'
      elif imgType == 'png':
        ratio = maxSize / content.size[np.argmax(content.size)]
        content = content.resize((np.array(content.size)*ratio).astype(int))
        figfile = BytesIO()
        content.save(figfile, format='PNG')
        imageData = base64.b64encode(figfile.getvalue()).decode()
        content = 'data:image/png;base64,' + imageData
        outFileFull = outFile+'.png'
      #clear figures for next extraction
      plt.cla()
      plt.clf()
      if outFileFull is not None:
        if self.cwd is not None and not extractorTest and saveToFile:
          # write to file
          appendix = ''
          if os.path.exists(outFileFull):
             #all files are by default locked in git-annex
             #  - unlock them
             #  - change them
             #  - save locks them automatically
            dataset.unlock(path=outFileFull)
            appendix = '(was unlocked before)'
          if outFileFull.endswith('svg'):
            with open(outFileFull,'w', encoding="utf-8") as f:
              figfile.seek(0)
              shutil.copyfileobj(figfile, f)
          else:
            with open(outFileFull,'wb') as f:
              figfile.seek(0)
              shutil.copyfileobj(figfile, f)
          dataset.save(path=outFileFull, message='Added document '+appendix)
        document['image'] = content
      else:
        if imgType=='text':
          document['content'] = content
        else:
          document={'-type':None, 'metaUser':None, 'metaVendor':None, 'shasum':None}
    else:
      document={'-type':None, 'metaUser':None, 'metaVendor':None, 'shasum':None}
      logging.warning('useExtractor could not find pyFile to convert '+pyFile)
    #combine into document
    logging.debug('useExtractor: finished')
    doc.update(document)
    if extractorTest:
      print("Info: Measurement type ",document['-type'])
    ##if 'comment' not in doc: doc['comment']=''
    return


  ######################################################
  ### Wrapper for database functions
  ######################################################
  def getDoc(self, docID):
    """
    Wrapper for getting data from database

    Args:
        docID (string): document id

    Returns:
        dict: json of document
    """
    return self.db.getDoc(docID)


  def replicateDB(self, remoteDB=None, removeAtStart=False, **kwargs):
    """
    Replicate local database to remote database

    Args:
        remoteDB (string): if given, use this name for external db
        removeAtStart (bool): remove remote DB before starting new
        kwargs (dict): additional parameter

    Returns:
        bool: replication success
    """
    from miscTools import upOut
    if remoteDB is not None:
      self.remoteDB['database'] = remoteDB
    self.remoteDB['user'],self.remoteDB['password'] = upOut(self.remoteDB['cred']).split(':')
    success = self.db.replicateDB(self.remoteDB, removeAtStart)
    return success


  def checkDB(self, verbose=True, **kwargs):
    """
    Wrapper of check database for consistencies by iterating through all documents

    Args:
        verbose (bool): print more or only issues
        kwargs (dict): additional parameter, i.e. callback

    Returns:
        string: output incl. \n
    """
    import os, logging
    from datalad.support import annexrepo
    ### check database itself for consistency
    output = self.db.checkDB(verbose=verbose, **kwargs)
    ### check if datalad status is clean for all projects
    if verbose:
      output += "--- DataLad status ---\n"
    viewProjects   = self.db.getView('viewDocType/x0')
    viewPaths      = self.db.getView('viewHierarchy/viewPaths')
    listPaths = [item['key'] for item in viewPaths]
    curDirectory = os.path.abspath(os.path.curdir)
    clean, count = True, 0
    for item in viewProjects:
      doc = self.db.getDoc(item['id'])
      dirName =doc['-branch'][0]['path']
      #output += '- '+dirName+' -\n'
      os.chdir(self.basePath+dirName)
      fileList = annexrepo.AnnexRepo('.').status()
      for posixPath in fileList:
        if fileList[posixPath]['state'] != 'clean':
          output += fileList[posixPath]['state']+' '+fileList[posixPath]['type']+' '+str(posixPath)+'\n'
          clean = False
        #test if file exists
        relPath = os.path.relpath(str(posixPath),self.basePath)
        if relPath.endswith('.id_pasta.json'): #if project,step,task
          relPath, _ = os.path.split(relPath)
        if relPath in listPaths:
          listPaths.remove(relPath)
          continue
        if '_pasta.' in relPath or '/.datalad/' in relPath or \
           relPath.endswith('.gitattributes') or os.path.isdir(self.basePath+relPath) or \
           relPath.endswith('.gitignore'):
          continue
        _, extension = os.path.splitext(relPath)
        extension = '*'+extension.lower()
        if extension in self.vanillaGit:
          continue
        logging.info(relPath+' not in database')
        count += 1
    output += 'Number of files on disk that are not in database '+str(count)+' (see log for details)\n'
    listPaths = [i for i in listPaths if not "://" in i ]
    listPaths = [i for i in listPaths if not os.path.exists(self.basePath+i)]
    if len(listPaths)>0:
      output += "These files of database not on filesystem: "+str(listPaths)+'\n'
    if clean:
      output += "** Datalad tree CLEAN **\n"
    else:
      output += "** Datalad tree NOT clean **\n"
    os.chdir(curDirectory)
    return output


  ######################################################
  ### OUTPUT COMMANDS and those connected to it      ###
  ######################################################
  def output(self, docType, printID=False, **kwargs):
    """
    output view to screen
    - length of output 100 character

    Args:
      docType (string): document type to output
      printID (bool):  include docID in output string
      kwargs (dict): additional parameter

    Returns:
        string: output incl. \n
    """
    outString = []
    widthArray = [25,25,25,25]
    if docType in self.tableFormat and '-default-' in self.tableFormat[docType]:
      widthArray = self.tableFormat[docType]['-default-']
    for idx,item in enumerate(self.db.ontology[docType]):
      if not 'name' in item:    #heading
        continue
      if idx<len(widthArray):
        width = widthArray[idx]
      else:
        width = 0
      if width!=0:
        formatString = '{0: <'+str(abs(width))+'}'
        outString.append(formatString.format(item['name']) )
    outString = '|'.join(outString)+'\n'
    outString += '-'*104+'\n'
    for lineItem in self.db.getView('viewDocType/'+docType):
      rowString = []
      for idx, item in enumerate(self.db.ontology[docType]):
        if idx<len(widthArray):
          width = widthArray[idx]
        else:
          width = 0
        if width!=0:
          formatString = '{0: <'+str(abs(width))+'}'
          if isinstance(lineItem['value'][idx], str ):
            contentString = lineItem['value'][idx]
          elif isinstance(lineItem['value'][idx], bool ) or lineItem['value'][idx] is None:
            contentString = str(lineItem['value'][idx])
          else:
            contentString = ' '.join(lineItem['value'][idx])
          contentString = contentString.replace('\n',' ')
          if width<0:  #test if value as non-trivial length
            if lineItem['value'][idx]=='true' or lineItem['value'][idx]=='false':
              contentString = lineItem['value'][idx]
            elif isinstance(lineItem['value'][idx], bool ) or lineItem['value'][idx] is None:
              contentString = str(lineItem['value'][idx])
            elif len(lineItem['value'][idx])>1 and len(lineItem['value'][idx][0])>3:
              contentString = 'true'
            else:
              contentString = 'false'
            # contentString = True if contentString=='true' else False
          rowString.append(formatString.format(contentString)[:abs(width)] )
      if printID:
        rowString.append(' '+lineItem['id'])
      outString += '|'.join(rowString)+'\n'
    return outString


  def outputTags(self, tag='', **kwargs):
    """
    output view to screen
    - length of output 100 character

    Args:
      tag (string): tag to be listed, if empty: print all
      kwargs (dict): additional parameter

    Returns:
        string: output incl. \n
    """
    outString = []
    outString.append( '{0: <10}'.format('Tags') )
    outString.append( '{0: <60}'.format('Name') )
    outString.append( '{0: <10}'.format('ID') )
    outString = '|'.join(outString)+'\n'
    outString += '-'*106+'\n'
    view = None
    if tag=='':
      view = self.db.getView('viewIdentify/viewTags')
    else:
      view = self.db.getView('viewIdentify/viewTags',preciseKey='#'+tag)
    for lineItem in view:
      rowString = []
      rowString.append('{0: <10}'.format(lineItem['key']))
      rowString.append('{0: <60}'.format(lineItem['value']))
      rowString.append('{0: <10}'.format(lineItem['id']))
      outString += '|'.join(rowString)+'\n'
    return outString


  def outputHierarchy(self, onlyHierarchy=True, addID=False, addTags=None, **kwargs):
    """
    output hierarchical structure in database
    - convert view into native dictionary
    - ignore key since it is always the same

    Args:
       onlyHierarchy (bool): only print project,steps,tasks or print all (incl. measurements...)[default print all]
       addID (bool): add docID to output
       addTags (string): add tags, comments, objective to output ['all','tags',None]
       kwargs (dict): additional parameter, i.e. callback

    Returns:
        string: output incl. \n
    """
    import re, logging
    from commonTools import commonTools as cT
    if len(self.hierStack) == 0:
      logging.warning('pasta.outputHierarchy No project selected')
      return 'Warning: pasta.outputHierarchy No project selected'
    hierString = ' '.join(self.hierStack)
    view = self.db.getView('viewHierarchy/viewHierarchy', startKey=hierString)
    nativeView = {}
    for item in view:
      if onlyHierarchy and not item['id'].startswith('x-'):
        continue
      nativeView[item['id']] = [item['key']]+item['value']
    if addTags=='all':
      outString = cT.hierarchy2String(nativeView, addID, self.getDoc, 'all', self.magicTags)
    elif addTags=='tags':
      outString = cT.hierarchy2String(nativeView, addID, self.getDoc, 'tags', self.magicTags)
    else:
      outString = cT.hierarchy2String(nativeView, addID, None, 'none', None)
    #remove superficial * from head of all lines
    minPrefix = len(re.findall(r'^\*+',outString)[0])
    startLine = r'\n\*{'+str(minPrefix)+'}'
    outString = re.sub(startLine,'\n',outString)[minPrefix+1:] #also remove from head of string
    return outString


  def getEditString(self):
    """
    Return Markdown string of hierarchy tree

    Returns:
        string: output incl. \n
    """
    #simple editor style: only this document, no tree
    if self.eargs['style']=='simple':
      doc = self.db.getDoc(self.hierStack[-1])
      return ', '.join(doc['tags'])+' '+doc['comment']
    #complicated style: this document and all its children and grandchildren...
    return self.outputHierarchy(True,True,'tags')


  def setEditString(self, text, callback=None):
    """
    Using Org-Mode string, replay the steps to update the database

    Args:
       text (string): org-mode structured text
       callback (function): function to verify database change

    Returns:
       success of function: true/false
    """
    import re, os, logging, tempfile
    import datalad.api as datalad
    from commonTools import commonTools as cT
    from miscTools import createDirName
    # write backup
    with open(tempfile.gettempdir()+os.sep+'tempSetEditString.txt','w') as fOut:
      fOut.write(text)
    dlDataset = datalad.Dataset(self.basePath+self.cwd.split(os.sep)[0])
    # add the prefix to org-mode structure lines
    prefix = '*'*len(self.hierStack)
    startLine = r'^\*+\ '
    newText = ''
    for line in text.split('\n'):
      if len(re.findall(startLine,line))>0:  #structure line
        newText += prefix+line+'\n'
      else:                                  #other lines, incl. first
        newText += line+'\n'
    newText = prefix+' '+newText
    docList = cT.editString2Docs(newText, self.magicTags)
    del newText; del text
    # initialize iteration
    levelOld = None
    path      = None
    deletedDocs= []
    for doc in docList:  #iterate through all entries

      # deleted items
      if doc['edit'] == '-delete-':
        doc['-user']   = self.userID
        doc = self.db.updateDoc(doc,doc['_id'])
        deletedDocs.append(doc['_id'])
        thisStack = ' '.join(doc['-branch'][0]['stack']+[doc['_id']])
        view = self.db.getView('viewHierarchy/viewHierarchy', startKey=thisStack)
        for item in view:
          subDoc = {'-user':self.userID, 'edit':'-delete-'}
          _ = self.db.updateDoc(subDoc, item['id'])
          deletedDocs.append(item['id'])
        oldPath   = doc['-branch'][0]['path']
        pathArray = oldPath.split(os.sep)
        pathArray[-1]='trash_'+'_'.join(pathArray[-1].split('_')[1:])
        newPath   = os.sep.join(pathArray)
        print('Deleted doc: Path',oldPath,newPath)
        os.rename(self.basePath+oldPath,self.basePath+newPath)
        continue

      # deleted parents
      if doc['_id'] in deletedDocs:
        continue

      # All non-deleted items: identify docType
      docDB    = self.db.getDoc(doc['_id']) if doc['_id']!='' else None
      levelNew = doc['-type']
      if levelOld is None:   #first run-through
        children  = [0]
      else:                   #after first entry
        if levelNew<levelOld:                               #UNCLE, aka SIBLING OF PARENT
          for _ in range(levelOld-levelNew):
            children.pop()
          children[-1] += 1
        elif levelNew>levelOld:                             #CHILD
          children.append(0)
        else:                                               #SIBLING
          children[-1] += 1
      if '_id' not in doc or docDB is None or docDB['-type'][0][0]=='x':
        doc['-type'] = 'x'+str(levelNew)
      else:
        doc['-type'] = docDB['-type']

      # for all non-text types: change children and  childNum in database
      #   and continue with next doc. This makes subsequent code easier
      if doc['-type'][0][0]!='x':
        docDB = dict(docDB)
        docDB.update(doc)
        doc = docDB
        doc['childNum'] = children[-1]
        del doc['edit']
        self.addData('-edit-', doc, self.hierStack)
        levelOld     = levelNew
        continue

      # ONLY TEXT DOCUMENTS
      if doc['edit'] == "-edit-":
        edit = "-edit-"
      else:
        edit = doc['-type']
      del doc['edit']
      # change directories: downward
      if levelOld is None:   #first run-through
        doc['childNum'] = docDB['-branch'][0]['child']
      else:                   #after first entry
        lenPath = len(self.cwd.split('/'))-1 if len(self.cwd.split('/')[-1])==0 else len(self.cwd.split('/'))
        for _ in range(lenPath-levelNew):
          self.changeHierarchy(None)                        #'cd ..'
        #check if directory exists on disk
        #move directory; this is the first point where the non-existence of the folder is seen and can be corrected
        dirName = createDirName(doc['name'],doc['-type'][0],children[-1])
        if not os.path.exists(dirName):                     #if move, deletion or because new
          if doc['_id']=='' or doc['_id']=='undefined':     #if new data
            os.makedirs(dirName)
          else:                                             #if move
            path = docDB['-branch'][0]['path']
            if not os.path.exists(self.basePath+path):      #parent was moved: get 'path' from knowledge of parent
              parentID = docDB['-branch'][0]['stack'][-1]
              pathParent = self.db.getDoc(parentID)['-branch'][0]['path']
              path = pathParent+os.sep+path.split(os.sep)[-1]
            if not os.path.exists(self.basePath+path):        #if still does not exist
              print("**ERROR bse01: doc path was not found and parent path was not found |"+doc)
              return False
            if self.confirm is None or self.confirm(None,"Move directory "+path+" -> "+self.cwd+dirName):
              os.rename(self.basePath+path, self.basePath+self.cwd+dirName)
              dlDataset.save(path=self.basePath+path, message='SetEditString move directory: origin')
              dlDataset.save(path=self.basePath+self.cwd+dirName, message='SetEditString move directory: target')
              logging.info("moved folder "+self.basePath+path+' -> '+self.basePath+self.cwd+dirName)
        if edit=='-edit-':
          self.changeHierarchy(doc['_id'], dirName=dirName)   #'cd directory'
          if path is not None:
            #adopt measurements, samples, etc: change / update path by supplying old path
            view = self.db.getView('viewHierarchy/viewPaths', startKey=path)
            for item in view:
              if item['value'][1][0][0]=='x': continue  #skip since moved by itself
              self.db.updateDoc( {'-branch':{'path':self.cwd, 'oldpath':path+os.sep,\
                                            'stack':self.hierStack,\
                                            'child':item['value'][2],\
                                            'op':'u'}},item['id'])
        doc['childNum'] = children[-1]
      # write change to database
      ## FOR DEBUGGING:
      print(doc['name'].strip()+'|'+str(doc['-type'])+'||'+doc['_id']+' #:',doc['childNum'])
      print('  children:',children,'   levelNew, levelOld',levelNew,levelOld,'   cwd:',self.cwd,'\n')
      if edit=='-edit-':
        docDB = dict(docDB)
        docDB.update(doc)
        doc = docDB
      self.addData(edit, doc, self.hierStack)
      #update variables for next iteration
      if edit!="-edit-" and levelOld is not None:
        self.changeHierarchy(self.currentID)   #'cd directory'
      levelOld     = levelNew

    #----------------------------------------------------
    #at end, go down ('cd  ..') number of children-length
    if '-type' in doc and doc['-type'][0][0]!='x':  #remove one child, if last was not an x-element, e.g. a measurement
      children.pop()
    for _ in range(len(children)-1):
      self.changeHierarchy(None)
    os.unlink(tempfile.gettempdir()+os.sep+'tempSetEditString.txt')
    dataset = datalad.Dataset(self.basePath+self.cwd.split(os.sep)[0])
    dataset.save(message='set-edit-string: update the project structure')
    return True


  def getChildren(self, docID):
    """
    Get children from this parent using outputHierarchy

    Args:
        docID (string): id parent document

    Returns:
        list: list of names, list of document-ids
    """
    from commonTools import commonTools as cT
    hierTree = self.outputHierarchy(True,True,False)
    if hierTree is None:
      print('**ERROR bgc01: No hierarchy tree')
      return None, None
    result = cT.getChildren(hierTree,docID)
    return result['names'], result['ids']

  def outputQR(self):
    """
    output list of sample qr-codes

    Returns:
        string: output incl. \n
    """
    outString = '{0: <36}|{1: <36}|{2: <36}'.format('QR', 'Name', 'ID')+'\n'
    outString += '-'*110+'\n'
    for item in self.db.getView('viewIdentify/viewQR'):
      outString += '{0: <36}|{1: <36}|{2: <36}'.format(item['key'][:36], item['value'][:36], item['id'][:36])+'\n'
    return outString


  def outputSHAsum(self):
    """
    output list of measurement SHA-sums of files

    Returns:
        string: output incl. \n
    """
    outString = '{0: <32}|{1: <40}|{2: <25}'.format('SHAsum', 'Name', 'ID')+'\n'
    outString += '-'*110+'\n'
    for item in self.db.getView('viewIdentify/viewSHAsum'):
      outString += '{0: <32}|{1: <40}|{2: <25}'.format(item['key'], item['value'][-40:], item['id'])+'\n'
    return outString
