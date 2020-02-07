#!/usr/bin/python3
##################################
####  COMMAND LINE INTERFACE  ####
##################################
import copy
from PyInquirer import prompt
from asCouchDB import Database

### INITIALIZATION
db = Database()
questionSets = db.getQuestions()

### CONTINUOUSLY ASK QUESTIONS until exit
nextQuestion = '-root-'
while True:
    #output the current hierarchical level
    if db.hierarchyLevel == 0:
        print("\n=====> You are at the root")
    else:
        levelName = db.hierarchyList[db.hierarchyLevel-1]
        objName   = db.db.get(db.hierarchyStack[-1])['name']
        print("\n=====> You are in "+levelName+":",objName )
    #prepare questions
    questions = copy.deepcopy(questionSets[nextQuestion])
    questions = db.questionCleaner(questions)
    #ask question
    doc = prompt(questions)
    #handle answers
    if not 'choice' in doc:                         db.addData(nextQuestion,doc)
    nextQuestion = "-root-"   #default case
    if not 'choice' in doc:                         continue
    if doc['choice'] == "-exit-":                   break
    if doc['choice'] in questionSets:               nextQuestion = doc['choice']
    if doc['choice'] == "Output tree-hierarchy":    db.outputHierarchy("-hierarchyRoot-")
    if doc['choice'] == "Output sample list":       db.outputSamples()
    if doc['choice'] == "Output measurement list":  db.outputMeasurements()
    if doc['choice'] == "Output procedures list":   db.outputProcedures()
    if doc['choice'] == "new":                      nextQuestion = db.hierarchyList[db.hierarchyLevel]
    if doc['choice'].split("_")[0] in db.hierarchyList: db.changeHierarchy(doc)
    if doc['choice'] == "-close-":                  db.changeHierarchy("-close-")
