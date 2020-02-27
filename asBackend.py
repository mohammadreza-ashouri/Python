import os, json
from asTools import imageToString, stringToImage
from asCouchDB import Database
from commonTools import commonTools as cT

class AgileScience:
  """ PYTHON BACKEND 
  """
  def __init__(self):
    """
    open server and define database
    """
    # open configuration file and define database
    jsonFile = open(os.path.expanduser('~')+'/.agileScience.json')
    configuration = json.load(jsonFile)
    user         = configuration["user"]
    password     = configuration["password"]
    databaseName = configuration["database"]
    self.db = Database(user,password,databaseName)
    self.eargs   = configuration["eargs"]
    # open basePath as current working directory
    self.softwareDirectory = os.path.abspath(os.getcwd())
    self.cwd     = os.path.expanduser('~')+"/"+configuration["baseFolder"]
    self.baseDirectory = os.path.expanduser('~')+"/"+configuration["baseFolder"]
    if not self.cwd.endswith("/"):
      self.cwd += "/"
    if os.path.exists(self.cwd):
      os.chdir(self.cwd)
    else:
      print("Base folder did not exist. No directory saving\n",self.cwd)
      self.cwd   = None
    # hierarchy structure
    self.hierList = self.db.getDoc("-dataDictionary-")["-hierarchy-"]
    self.hierStack = []
    self.view      = None   #current view
    return
  

  ######################################################
  ### prepare questions for next user interaction
  ######################################################
  def getQuestions(self):
    """
    executed after database is intialized: create all questions
    - based on data dictionary stored in DB
    - add output, default questions

    Keep default questions separate since all questions are only needed by CLI, not by ReactJS versions
    """
    doc = self.db.getDoc("-dataDictionary-")
    allNewQuestions = json.load(open(self.softwareDirectory+"/userInterfaceCLI.json",'r'))
    self.typeLabels = cT.dataDictionary2Labels(doc)
    for item in allNewQuestions:  #make cleaner: go to options directly (no iterations): i.e. change output
      if ('choices' in allNewQuestions[item][0]) and \
         (allNewQuestions[item][0]['choices'] == '$docLabels$'):
        allNewQuestions[item][0]['choices'] = [j for i,j in self.typeLabels] + ['Hierarchy']
    for docType in doc:            #iterate through each docType: e.g. measurement
      if docType.startswith("_") or docType.startswith("-"):
        continue
      newQuestions = []
      for question in doc[docType]: #iterate over all data stored within this docType
        if isinstance(question, str):
          continue
        ### convert question into json-string that PyInquirer understands
        # decode incoming json
        keywords = {"list":None,"generate":None}
        for item in keywords:
          if item in question:
            keywords[item] = question[item]
            del question[item]
        if len(question)>1: 
          print("**ERROR** QUESTION ILLDEFINED",question)
        name, questionString = question.popitem()
        # encode outgoing json
        if keywords['generate'] is not None:
          continue  #it is generated, no need to ask
        newQuestion = {"type":"input","name": name,"message": questionString}
        if keywords['list'] is not None:
          newQuestion['type']='list'
          if isinstance(keywords['list'], list):
            newQuestion['choices'] = keywords['list']
        newQuestions.append(newQuestion)
      newQuestions.append({"type":"input","name":"comment","message":"#tags, :field:value: comments"})
      if docType not in self.hierList:  #those are anyhow linked
        newQuestions.append({'type':'confirm','name':'flagLinked','message':'Link to hierarchy?'})
      allNewQuestions[docType] = newQuestions
    return allNewQuestions


  def questionCleaner(self,questions):
    """
    Clean questions to go into interface
    - fill the required lists
    - remove choices that are insensible
    - add default content

    Args:
       questions: to be cleaned
    """
    if self.hierList[-1] != "--marker--":
      self.hierList = self.hierList+["--marker--"]
    jsonString = json.dumps(questions)
    jsonString = jsonString.replace("$thisLevel$",self.hierList[len(self.hierStack)-1])
    jsonString = jsonString.replace("$nextLevel$",self.hierList[len(self.hierStack)])
    jsonObjects= json.loads(jsonString)    
    for jsonObj in jsonObjects:
      ## changes based on next question
      if 'choices' in jsonObj:          #clean list choices
        choices = jsonObj['choices']
        choice  = [i for i in choices if '$docLabel$' in i] #find a first choice that has docLabels
        if len(choice)>0:
          choice  = choice[0]
          iChoice = choices.index(choice)
          for dataType,dataLabel in self.typeLabels:
            if dataType=='project': continue
            choices.insert(iChoice+1, choice.replace("$docLabel$",dataLabel))
          del choices[iChoice]
        choices = [i for i in choices if '--marker--' not in i]
        jsonObj['choices'] = choices
      ## create list of sub-hierarchy: list of projects, list of steps, ...
      if jsonObj['type'] == 'list' and len(jsonObj['choices'])==0:
        if len(self.hierStack)==0: #no element in list: look for projects
          self.thisDoc = self.db.getView('viewProjects/viewProjects')
          self.nextChoicesID = [i.id for i in self.thisDoc]   #first of matching list: ids
          self.nextChoices   = [i.key for i in self.thisDoc]  #second of matching list: names
        else:
          self.thisDoc = self.db.getDoc(self.hierStack[-1])
          self.nextChoicesID  = [id for id in self.thisDoc['childs'] if id.startswith('t')]
          self.nextChoices    = [self.db.getDoc(id)['name'] for id in self.thisDoc['childs'] if id.startswith('t')]
        jsonObj['choices'] = self.nextChoices
        if len(jsonObj['choices'])==0:  #if nothing in list
          print("**WARNING** Nothing to change to")
          return None
      if jsonObj['type']  == 'editor':
        jsonObj['eargs']   = self.eargs
        doc = self.db.getDoc(self.hierStack[-1])
        jsonObj['default'] = ", ".join(['#'+tag for tag in doc['tags']])+' '+doc['comment']
    return jsonObjects


  ######################################################
  ### Change in database
  ######################################################
  def addData(self,question,data, projectID='', parentID=None):
    """
    Save data to data base, also after edit

    Args:
       question: what question triggered the answer
       data: answer of question
    """
    if len(self.hierStack)>0 and projectID=='':
      projectID = self.hierStack[0]
    flagLinked = parentID is None
    if 'flagLinked' in data:
      flagLinked = data['flagLinked'] and len(self.hierStack)>0
      del  data['flagLinked']
    if question == '-edit-':
      temp = self.db.getDoc(self.hierStack[-1])      
      temp.update(data)
      data = temp
      question = data['type']
      flagLinked = False    #should not change
    elif self.cwd is not None and data['type'] in self.hierList:  #create directory for projects,steps,tasks
      os.makedirs( cT.camelCase(data['name']), exist_ok=True )
    print(data)
    data = cT.fillDocBeforeCreate(data, question,projectID).to_dict()
    if data['type']=='measurement':
      #TODO PRIO-1 add image
      data['image'] = ''
    print("Data saved",data)
    _id, _rev = self.db.saveDoc(data)
    if (question in self.hierList or flagLinked or parentID is not None) \
      and data['type']!='project':
      if parentID is None:
        parent = self.db.getDoc(self.hierStack[-1])
      else:
        parent = self.db.getDoc(parentID)
      parent['childs'].append(_id)
      print("Parent updated",parent)
      self.db.updateDoc(parent)
    return
  

  ######################################################
  ### Get data from database
  ######################################################
  def getDoc(self,id):
    """
    Wrapper for getting data from database
    """
    return self.db.getDoc(id)


  def changeHierarchy(self, choice):
    """
    Change through text hierarchy structure

    Args:
       document: information on how to change
    """
    if choice == "-close-":
      self.hierStack.pop()
      if self.cwd is not None:
        os.chdir('..')
        self.cwd = '/'.join(self.cwd.split('/')[:-2])+'/'
    else:
      idx = self.nextChoices.index(choice)
      id  = self.nextChoicesID[idx]
      self.hierStack.append(id)
      if self.cwd is not None:
        os.chdir( cT.camelCase(choice) )
        self.cwd += cT.camelCase(choice)+'/'
    return


  def scanDirectory(self):
    """ Recursively scan directory tree for new files and print
    """
    for root,_,fNames in os.walk(self.cwd):
      if len(fNames)==0:
        continue
      relpath = os.path.relpath(root,start=self.baseDirectory)
      if len(relpath.split('/'))==3:
        project,step,task = relpath.split('/')
      elif len(relpath.split('/'))==2:
        project,step = relpath.split('/')
        task = None
      elif len(relpath.split('/'))==1:
        project,step,task = relpath.split('/')[0], None, None
      else:
        project,step,task = None, None, None
        print("Error")
      for fName in fNames:  #all files in this directory
        #find project id
        projectID = None
        for item in self.db.getView('viewProjects/viewProjects'):
          if project == cT.camelCase(item.key):
            projectID = item.id
        #find parent id
        view = self.db.getView('viewProjects/viewHierarchy', key=projectID)
        parentID = None
        if step is None:
          parentID = projectID
        elif task is None:
          for item in view:
            if item.value[0]=='step' and step == cT.camelCase(item.value[1]):
              parentID = item.id
        else:
          for item in view:
            if item.value[0]=='step' and step == cT.camelCase(item.value[1]):
              for childs in item.value[2]:
                print(childs)  #TODO PRIO-1 iterate trough
        doc = {'name':fName, 'type':'measurement', 'comment':''}
        self.addData('measurement',doc,projectID,parentID)
    return


  ######################################################
  ### OUTPUT COMMANDS ###
  ######################################################
  def output(self,docType):
    view = 'view'+docType
    if docType=='Measurements':
      print('{0: <25}|{1: <21}|{2: <21}|{3: <7}|{4: <32}'.format('Name','Alias','Comment','Image','project-ID'))
    if docType=='Projects':
      print('{0: <25}|{1: <6}|{2: >5}|{3: <38}|{4: <32}'.format('Name','Status','#Tags','Objective','ID'))
    if docType=='Procedures':
      print('{0: <25}|{1: <51}|{2: <32}'.format('Name','Content','project-ID'))
    if docType=='Samples':
      print('{0: <25}|{1: <15}|{2: <27}|{3: <7}|{4: <32}'.format('Name','Chemistry','Comment','QR-code','project-ID'))
    print('-'*110)
    for item in self.db.getView(view+'/'+view):
      if docType=='Measurements':
        print('{0: <25}|{1: <21}|{2: <21}|{3: <7}|{4: <32}'.format(
          item.value[0][:25],item.value[1][:21],item.value[2][:21],str(item.value[3]),item.key))
      if docType=='Projects':
        print('{0: <25}|{1: <6}|{2: <5}|{3: <38}|{4: <32}'.format(
          item.key[:25],item.value[0][:6],item.value[2],item.value[1][:38],item.id))
      if docType=='Procedures':
        print('{0: <25}|{1: <51}|{2: <32}'.format(
          item.value[0][:25],item.value[1][:51],item.key))
      if docType=='Samples':
        print('{0: <25}|{1: <15}|{2: <27}|{3: <7}|{4: <32}'.format(
          item.value[0][:25],item.value[1][:15],item.value[2][:27],str(item.value[3]),item.key))
    print("\n\n")
    return


  def outputHierarchy(self):
    """
    print hierarchical structure in database
    - convert view into native dictionary
    - ignore key since it is always the same
    """
    if len(self.hierStack)==0:
      print('**WARNING** No project selected')
      return
    projectID = self.hierStack[0]
    view = self.db.getView('viewProjects/viewHierarchy', key=projectID)
    nativeView = {}
    for item in view:
      nativeView[item.id] = item.value
    outString = cT.projectDocsToString(nativeView, projectID,0)
    print(outString)
    return
