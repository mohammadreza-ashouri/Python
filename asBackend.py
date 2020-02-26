import os, json
from asTools import string2TagFieldComment, imageToString, stringToImage
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
    for item in allNewQuestions:
      if ('choices' in allNewQuestions[item][0]) and \
         (allNewQuestions[item][0]['choices'] == '$docLabels$'):
        allNewQuestions[item][0]['choices'] = [j for i,j in self.typeLabels]
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
  def addData(self,question,data):
    """
    Save data to data base, also after edit

    Args:
       question: what question triggered the answer
       data: answer of question
    """
    projectID = ""
    if len(self.hierStack)>0:
      projectID = self.hierStack[0]
    if 'flagLinked' in data:
      flagLinked = data['flagLinked'] and len(self.hierStack)>0
      del  data['flagLinked']
    if question == '-edit-':
      temp = self.db.getDoc(self.hierStack[-1])      
      temp.update(data)
      data = temp
      question = data['type']
      flagLinked = False    #should not change
    elif self.cwd is not None:
      os.makedirs( cT.camelCase(data['name']), exist_ok=True )
    data = cT.fillDocBeforeCreate(data, question,projectID).to_dict()
    #TODO add image
    if data['type']=='measurement':
      data['image'] = ''
    # print("Data saved",data)
    _id, _rev = self.db.saveDoc(data)
    if (question in self.hierList or flagLinked) and data['type']!='project':
      parent = self.db.getDoc(self.hierStack[-1])
      parent['childs'].append(_id)
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
    """
    # TODO Convert to js
    # convert into native dictionary tree
    hierTree = {}
    for item in self.db.getView("viewHierarchy/viewHierarchy"):
      hierTree[item.key] = [(i,None) for i in item.value]
    # create hierarchical tree
    for keyI in hierTree:
      for keyJ in hierTree:
        for idx, childOfI in enumerate(hierTree[keyI]):
          keyOfChildI, value = childOfI
          if keyOfChildI == keyJ:
            hierTree[keyI][idx] = (keyJ, hierTree[keyJ])
    hierTree = ("-hierarchyRoot-", hierTree["-hierarchyRoot-"])
    # create long string and print
    output = self.outputHierarchyString(hierTree)
    print(output)
    return


  def outputHierarchyString(self, branch, level=0):
    """
    Recursively called function to create string representation of hierarchy tree
    """
    output = "\t"*level + self.db.getDoc(branch[0])['name']  + "\t" + branch[0]+"\n"
    for subBranch in branch[1]:
      output += self.outputHierarchyString(subBranch,level+1)
    return output

