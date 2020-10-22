#!/usr/bin/python3
import subprocess
import asyncio
from questionary import prompt, Separator
from datalad import api as datalad

question = [{'type': 'list', 'name': 'choice', 'message': 'Menu', 'choices': ['Red pill','Blue pill']}]
print("You have to take four pills")
for i in range(4):
  asyncio.set_event_loop(asyncio.new_event_loop()) 
  answer = prompt(question)
  name =  answer['choice'].replace(' ','_')+str(i)
  print("Create path: "+name)
  ### does not work
  ds = datalad.create(name, cfg_proc='text2git')
  ### works perfectly
  # cmd = ['datalad','create','-c','text2git',name]
  # output = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  # print("Log: dataset created. Success")


