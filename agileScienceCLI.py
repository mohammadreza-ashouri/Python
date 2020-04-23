#!/usr/bin/python3
##################################
####  COMMAND LINE INTERFACE  ####
##################################
import copy, json, os
from PyInquirer import prompt, Separator
from pprint import pprint
from agileScience import AgileScience

### INITIALIZATION
be = AgileScience()
print("Start in directory",os.path.abspath(os.path.curdir))
# keep main-menu and the other menus separate from dataDictionary since only CLI needs menu
menuOutline = json.load(open(be.softwarePath+"/userInterfaceCLI.json", 'r'))
nextMenu = 'main'
### MAIN LOOP
while be.alive:
  #output the current hierarchical level
  if len(be.hierStack) == 0:
    print("\n==> You are at the root |"+be.cwd+"| <==")
  else:
    levelName = be.hierList[len(be.hierStack)-1]
    objName   = be.getDoc(be.hierStack[-1])['name']
    print("\n==> You are in "+levelName+": "+objName+" |"+be.cwd+"| <==")
  #####################
  ### prepare menu  ###
  #####################
  if nextMenu in menuOutline and nextMenu != 'edit':
    #main and output menu are outlined in file, use those
    nextMenu = copy.deepcopy(menuOutline[nextMenu])
    question = [{'type': 'list', 'name': 'choice', 'message': nextMenu[0], 'choices':[]}]
    for idx, item in enumerate(nextMenu):
      if idx == 0:
        continue
      #extract properties of dictionary item
      append, expand = None, None
      if 'append' in item:
        append = item.pop('append')
      if 'expand' in item:
        expand = item.pop('expand')
      key, value = item.popitem()
      #use properties to
      if append is not None:
        if append == 'thisLevel':
          append = be.hierList[len(be.hierStack)-1] if len(be.hierStack) > 0 else None
        else:
          append = be.hierList[len(be.hierStack)] if len(be.hierStack) < len(be.hierList) else None
        if append is None:
          continue
        key   += ' '+append
        value += append
      if expand is None:
        expand = ['']
      else:
        if nextMenu == 'main':
          expand = [' '+j for i, j in be.db.dataLabels]
        else:  # output
          expand = [' '+j for i, j in be.db.dataLabels+be.db.hierarchyLabels]
      #create list of choices
      for item in expand:
        question[0]['choices'].append({'name': key+item, 'value': value+item[1:]})
  elif nextMenu == 'edit':
    #edit menu
    question = {"default": "", "eargs": be.eargs, "message": menuOutline['edit'][0],
                "name": "comment", "type": "editor"}
    question['default'] = be.getEditString()
  elif nextMenu.startswith('change'):
    #change menu
    question = [{'type': 'list', 'name': 'choice', 'message': nextMenu[0], 'choices':[]}]
    if len(be.hierStack) == 0: # no project in list: use VIEW
      doc    = be.db.getView('viewProjects/viewProjects')
      values = [i['id'] for i in doc]
      names  = [i['value'][0] for i in doc]
    else:                      # step/task: get its children
      names, values = be.getChildren(be.hierStack[-1])
    if len(names)==0:
      print('Nothing to choose from!')
      nextMenu = 'main'
      continue
    for name, value in zip(names, values):
      question[0]['choices'].append({'name': name, 'value': 'function_changeHierarchy_'+value})
  else:
    #ask for measurements, samples, procedures, projects, ...
    #create form (=sequence of questions for string input) is dynamically created from dataDictonary
    docType = nextMenu.split('_')[1]
    question = []
    if docType not in be.dataDictionary:  #only measurements, samples, procedures
      for type_, label_ in be.db.dataLabels:
        if label_ == docType:
          docType = type_
    docLabel = next(iter(be.dataDictionary[docType]))
    for line in be.dataDictionary[docType][docLabel]:  # iterate over all data stored within this docType
      ### convert line into json-string that PyInquirer understands
      # decode incoming json
      keywords = {"list": None, "generate": None, "length":None}
      for item in keywords:
        if item in line:
          keywords[item] = line[item]
          del line[item]
      if len(line) > 1:
            print("**ERROR** QUESTION ILLDEFINED", line)
      name, questionString = line.popitem()
      # encode outgoing json
      if keywords['generate'] is not None:
        continue  # it is generated, no need to ask
      newQuestion = {"type": "input", "name": name, "message": questionString}
      if keywords['list'] is not None:
        newQuestion['type'] = 'list'
      if isinstance(keywords['list'], list):
        newQuestion['choices'] = keywords['list']
      question.append(newQuestion)
  #####################
  ### ask question  ###
  #####################
  # print("\n\n")
  # pprint(question)
  answer = prompt(question)
  # pprint(answer)
  #####################
  ### handle answer ###
  #####################
  if 'choice' in answer:
    # forms that ask further questions
    answer = answer['choice'].split('_')
    if answer[0] == 'menu':
      nextMenu = answer[1]
    elif answer[0] == 'form':
      nextMenu = '_'.join(answer)
    else:   #e.g. function
      if len(answer) == 2:
        res = getattr(be, answer[1])()
      elif len(answer) > 2:
        res = getattr(be, answer[1])('_'.join(answer[2:]))
      else:
        res = ''
      if res is not None:
        print(res)  #output string returned from e.g. output-projects
      nextMenu = 'main'
  else:
    # all data collected, save it
    if nextMenu=='edit': #edit-> update data
      be.setEditString(answer['comment'])
    else:
      be.addData(docType, answer)
    nextMenu = 'main'
  continue
