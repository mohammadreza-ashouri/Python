#!/usr/bin/python3
##################################
####  COMMAND LINE INTERFACE  ####
##################################
import copy, json
from PyInquirer import prompt, Separator
from pprint import pprint
from agileScience import AgileScience

### INITIALIZATION
be = AgileScience()
# keep main-menu and the other menus separate from dataDictionary since only CLI needs menu
menuOutline = json.load(open(be.softwareDirectory+"/userInterfaceCLI.json", 'r'))
nextMenu = 'main'
### MAIN LOOP
while be.alive:
    #output the current hierarchical level
    if len(be.hierStack) == 0:
        print("\n==> You are at the root", be.cwd)
    else:
        levelName = be.hierList[len(be.hierStack)-1]
        objName   = be.getDoc(be.hierStack[-1])['name']
        print("\n==> You are in "+levelName+":", objName, be.cwd)
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
        doc = be.db.getDoc(be.hierStack[-1])
        docType = doc['type']
        question['default'] = ", ".join([tag for tag in doc['tags']])+' '+doc['comment']
    elif nextMenu.startswith('change'):
        #change menu
        question = [{'type': 'list', 'name': 'choice', 'message': nextMenu[0], 'choices':[]}]
        if len(be.hierStack) == 0:
            # no project in list: get a VIEW
            doc    = be.db.getView('viewProjects/viewProjects')
            values = [i['id'] for i in doc]
            names  = [i['key'] for i in doc]
        else:
            # at least a project: get its childs
            doc    = be.db.getDoc(be.hierStack[-1])
            values = [id for id in doc['childs'] if id.startswith('t')]
            names  = [be.db.getDoc(id)['name'] for id in doc['childs'] if id.startswith('t')]
        for name, value in zip(names, values):
            question[0]['choices'].append({'name': name, 'value': 'function_changeHierarchy_'+value})
    else:
        #ask for measurements, samples, procedures
        #create form (=sequence of questions for string input) is dynamically created from dataDictonary
        docType = nextMenu.split('_')[1]
        question = []
        if docType not in be.dataDictionary:
            for type_, label_ in be.db.dataLabels:
                if label_ == docType:
                    docType = type_
        for line in be.dataDictionary[docType]:  # iterate over all data stored within this docType
            if isinstance(line, str):  # skip first line of each doctype: its label
                continue
            ### convert line into json-string that PyInquirer understands
            # decode incoming json
            keywords = {"list": None, "generate": None}
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
        answer = answer['choice'].split('_')
        if answer[0] == 'menu':
            nextMenu = answer[1]
        elif answer[0] == 'form':
            nextMenu = '_'.join(answer)
        else:
            if len(answer) == 2:
                res = getattr(be, answer[1])()
            elif len(answer) > 2:
                res = getattr(be, answer[1])('_'.join(answer[2:]))
            else:
                res = ''
            print(res)
            nextMenu = 'main'
    else:
        be.addData(docType, answer)
        nextMenu = 'main'
    continue
