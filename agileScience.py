#!/usr/bin/python3
##################################
####  COMMAND LINE INTERFACE  ####
##################################
import copy
from PyInquirer import prompt
from asBackend import AgileScience

### INITIALIZATION
be = AgileScience()
questionSets = be.getQuestions()
addNewHierarchy = ['Add new '+i for i in be.hierList]
addNewDocuments = ['Add to '+ i for j,i in be.typeLabels]


### CONTINUOUSLY ASK QUESTIONS until exit
nextQuestion = '-root-'
while True:
    #output the current hierarchical level
    if len(be.hierStack) == 0:
        print("\n==> You are at the root",be.cwd)
    else:
        levelName = be.hierList[len(be.hierStack)-1]
        objName   = be.getDoc(be.hierStack[-1])['name']
        print("\n==> You are in "+levelName+":",objName,be.cwd )
    #prepare questions
    questions = copy.deepcopy(questionSets[nextQuestion])
    questions = be.questionCleaner(questions)
    #ask question
    if questions is None:
        nextQuestion = '-root-'
        continue
    else:
        answer = prompt(questions)
    #handle answers that come not out of '-root-' question
    if 'choice' not in answer:                  #if measurement, project data entered
        be.addData(nextQuestion,answer)
        nextQuestion = '-root-'
    elif nextQuestion == '-use-':               #change into given project, step, task
        be.changeHierarchy(answer['choice'])
        nextQuestion = '-root-'
    #answers that come out of '-root-' question
    elif answer['choice'] in addNewHierarchy:     #if wants to enter project, step, task data
        nextQuestion = answer['choice'].split()[-1]
    elif answer['choice'] in addNewDocuments:
        idx = addNewDocuments.index( answer['choice'] )
        nextQuestion = be.typeLabels[idx][0]
    elif answer['choice'] == "Output database": #if wants to get output
        nextQuestion = '-output-'
    elif nextQuestion=='-output-':
        be.output(answer['choice'])
        nextQuestion = '-root-'
    elif 'Change to' in answer['choice']:       #change project, step, task
        nextQuestion = '-use-'
    elif "Close " in answer['choice']:          #close project, step, task
        be.changeHierarchy('-close-')
        nextQuestion = '-root-'
    elif "Edit " in answer['choice']:           #edit  project, step, task
        nextQuestion = '-edit-'
    elif answer['choice'] == "Exit program":    #exit
        break
    else:
        print("**WARNING** Non identified case",answer)
