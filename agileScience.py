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

### CONTINUOUSLY ASK QUESTIONS until exit
nextQuestion = '-root-'
while True:
    #output the current hierarchical level
    if len(be.hierStack) == 1:
        print("\n==> You are at the root",be.cwd)
    else:
        levelName = be.hierList[len(be.hierStack)-1]
        objName   = be.get(be.hierStack[-1])['name']
        print("\n==> You are in "+levelName+":",objName,be.cwd )
    #prepare questions
    questions = copy.deepcopy(questionSets[nextQuestion])
    questions = be.questionCleaner(questions)
    #ask question
    doc = prompt(questions)
    #handle answers
    if 'choice' not in doc:                         be.addData(nextQuestion,doc)
    nextQuestion = "-root-"   #default case
    if 'choice' not in doc:                         continue
    if doc['choice'] == "-exit-":                   break
    if doc['choice'] in questionSets:               nextQuestion = doc['choice']
    if doc['choice'] == "Output tree-hierarchy":    be.outputHierarchy()
    if doc['choice'] == "Output sample list":       be.outputSamples()
    if doc['choice'] == "Output measurement list":  be.outputMeasurements()
    if doc['choice'] == "Output procedures list":   be.outputProcedures()
    if doc['choice'] == "new":                      nextQuestion = be.hierList[len(be.hierStack)]
    if doc['choice'].split("_")[0] in be.hierList:  be.changeHierarchy(doc)
    if doc['choice'] == "-close-":                  be.changeHierarchy("-close-")
