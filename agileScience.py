#!/usr/bin/python3
##################################
####  COMMAND LINE INTERFACE  ####
##################################
import copy
from PyInquirer import prompt
from asBackend import AgileScience

### INITIALIZATION
backend = AgileScience()
questionSets = backend.getQuestions()

### CONTINUOUSLY ASK QUESTIONS until exit
nextQuestion = '-root-'
while True:
    #output the current hierarchical level
    if backend.hierarchyLevel == 0:
        print("\n=====> You are at the root")
    else:
        levelName = backend.hierarchyList[backend.hierarchyLevel-1]
        objName   = backend.get(backend.hierarchyStack[-1])['name']
        print("\n=====> You are in "+levelName+":",objName )
    #prepare questions
    questions = copy.deepcopy(questionSets[nextQuestion])
    questions = backend.questionCleaner(questions)
    #ask question
    doc = prompt(questions)
    #handle answers
    if not 'choice' in doc:                         backend.addData(nextQuestion,doc)
    nextQuestion = "-root-"   #default case
    if not 'choice' in doc:                         continue
    if doc['choice'] == "-exit-":                   break
    if doc['choice'] in questionSets:               nextQuestion = doc['choice']
    if doc['choice'] == "Output tree-hierarchy":    backend.outputHierarchy("-hierarchyRoot-")
    if doc['choice'] == "Output sample list":       backend.outputSamples()
    if doc['choice'] == "Output measurement list":  backend.outputMeasurements()
    if doc['choice'] == "Output procedures list":   backend.setView()
    if doc['choice'] == "new":                      nextQuestion = backend.hierarchyList[backend.hierarchyLevel]
    if doc['choice'].split("_")[0] in backend.hierarchyList: backend.changeHierarchy(doc)
    if doc['choice'] == "-close-":                  backend.changeHierarchy("-close-")
