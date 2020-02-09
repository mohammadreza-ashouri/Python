import os, json
from asTools import string2TagFieldComment, camelCase, imageToString, stringToImage
from asCouchDB import Database

class AgileScience:
  def __init__(self):
    """
    open server and define database
    - verify hierarchyRoot is in database
    - verify dataDictionary is in database
    - verify userInterface is in database
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
    self.hierStack = ['-hierarchyRoot-']
  

  def getQuestions(self):
    """
    executed after database is intialized: create all questions
    - based on data dictionary stored in DB
    - add output, default questions

    Keep separate since all questions are only needed by CLI, not by ReactJS versions
    """
    doc = self.db.getDoc("-dataDictionary-")
    allNewQuestions = self.db.getDoc("-userInterface-")
    for data in doc:            #iterate through each data-set entry: e.g. measurement
      if data.startswith("_") or data.startswith("-"):
        continue
      newQuestions = []
      for question in doc[data]: #iterate over all data stored within this data-set
        ### convert question into json-string that PyInquirer understands
        # decode incoming json
        keywords = {"list":None,"required":True,"generate":False,"default":None}
        for item in keywords:
          if item in question:
            keywords[item] = question[item]
            del question[item]
        if len(question)>1: print("**ERROR** QUESTION ILLDEFINED",question)
        name, questionString = question.popitem()
        # encode outgoing json
        newQuestion = {"type":"input","name": name,"message": questionString}
        newQuestions.append(newQuestion)
      newQuestions.append({"type":"input","name":"comment","message":"#tags, :field:value: comments"})
      if data not in self.hierList:
        newQuestions.append({"type":"confirm","name": "linked","message": "Linked to hierarchy?","default": True})
      allNewQuestions[data] = newQuestions
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
    if self.hierList[0] != "--marker--":
      self.hierList = ["--marker--"]+self.hierList
    jsonString = json.dumps(questions)
    jsonString = jsonString.replace("$thisLevel$",self.hierList[len(self.hierStack)-1])
    jsonString = jsonString.replace("$nextLevel$",self.hierList[len(self.hierStack)])
    jsonObj    = json.loads(jsonString)
    ## changes based on next question
    if "type" not in jsonObj:   #if not an expand or list type
      return jsonObj
    if jsonObj['type'] == 'expand':
      for item in jsonObj:
        if item != "choices": continue
        jsonObj[item] = [i for i in jsonObj[item] if "--marker--" not in i["name"]]
    ## create list of sub-hierarchy
    if jsonObj['type'] == 'list' and len(jsonObj['choices'])==0:
      listItems = []
      for id in self.db.getDoc(self.hierStack[-1])['childs']:
        if self.db.getDoc(id)['type']==self.hierList[len(self.hierStack)]:
          listItems.append(self.db.getDoc(id)['type']+"_"+self.db.getDoc(id)['name']+"_"+id) 
      jsonObj['choices'] = listItems
    if jsonObj['type']  == 'editor':
      jsonObj['eargs']   = self.eargs
      doc = self.db.getDoc(self.hierStack[-1])
      jsonObj['default'] = ", ".join(['#'+tag for tag in doc['tags']])+' '+doc['comment']
    return jsonObj


  def addData(self,question,data):
    """
    Save data to data base, also after edit

    Args:
       question: what question triggered the answer
       data: answer of question
    """
    if len(data)<1:   #no data returned from user
      return
    inputString = data['comment']
    if question == '-edit-':
      data = self.db.getDoc(self.hierStack[-1])
      flagLinked = False    #should not change
    else:
      data['type'] = question
      data['childs'] = []
      flagLinked = False
      if "linked" in data:
        if data['linked'] and len(self.hierStack)>1:
          flagLinked = True
        del data['linked']
      #images
      if data['type'] == 'measurement':
        if data['alias'] =='':  data['alias']=data['name']
        data['image'] = imageToString(data['name'])
    data.update(  string2TagFieldComment(inputString) )
    print("Data saved",data)
    _id, _rev = self.db.saveDoc(data)
    if question in self.hierList or flagLinked:
      parent = self.db.getDoc(self.hierStack[-1])
      parent['childs'].append(_id)
      self.db.updateDoc(parent)
    if self.cwd is not None:
      os.makedirs( camelCase(data['name']) )
    return
  

  def get(self,id):
    """
    Wrapper for getting data from database
    """
    return self.db.getDoc(id)



  def changeHierarchy(self, document):
    """
    Change through text hierarchy structure

    Args:
       document: information on how to change
    """
    if document == "-close-":
      self.hierStack.pop()
      if self.cwd is not None:
        os.chdir('..')
        self.cwd = '/'.join(self.cwd.split('/')[:-1])
      return
    listItems = document['choice'].split("_")
    if len(listItems)==3:
      levelName, name, id  = listItems
      levelIdx = self.hierList.index(levelName)
      self.hierStack.append(id)
      if self.cwd is not None:
        os.chdir( camelCase(name) )
        self.cwd += camelCase(name)+'/'
    else:
      print("** ERROR ** change Hierarchy")
    return


  ### OUTPUT COMMANDS ###
  def outputHierarchy(self):
    """
    print hierarchical structure in database
    """
    from pprint import pprint
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



  def outputMeasurements(self):
    """
    print all measurements in list
    """

    for item in self.db.getView("viewMeasurements/viewMeasurements"):
        print(item.key,"|   fileName:",item.value)
        doc = self.db.getDoc(item.key)
        if "image" in doc:
          stringToImage(doc['image'])
    return


  def outputSamples(self):
    """
    print all samples in table form
    """
    print("key|name|chemistry|size")
    for item in self.db.getView("viewData/viewSamples"):
        print(item.key,"|",item.value["name"],"|",item.value["chemistry"],"|",item.value["size"])
    return


  def outputProcedures(self):
    """
    print all procedures in table form
    """
    for item in self.db.getView("viewData/viewProcedures"):
        print(item.key,"|",item.value["name"],"|",item.value["content"],"|")
    return
