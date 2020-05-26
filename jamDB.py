#!/usr/bin/python3
""" Main function when command-line commands used
"""
import argparse,textwrap
from backend import JamDB

argparser = argparse.ArgumentParser(usage='''jamDB.py <command> <item>

Possible commands are:
    print: 'Projects', 'Samples', 'Measurements', 'Procedures'
    clean, scan, produce, compare, hierarchy: documentID. To be identified by printing first
        cleaning: docID=all cleans all
    newDB: add/update database configuration. E.g.
        '{"test":{"user":"Peter","password":"Parker",...}}' ''')
argparser.add_argument("command", help="print, clean, scan, produce, compare, hierarchy, newDB")
argparser.add_argument("item",    help="'Projects', 'Samples', 'Measurements', 'Procedures', 'documentID'")
argparser.add_argument("-db","--database", help="name of database configuration")
args = argparser.parse_args()
if args.command=="newDB":
  #use new database configuration and store in local-config file
  # no need to touch default databases since database can be chosen by -db
  newDB = json.loads(args.item)
  label = list(newDB.keys()).pop()
  with open(os.path.expanduser('~')+'/.jamDB.json','r') as f:
    configuration = json.load(f)
  configuration[label] = newDB[label]
  with open(os.path.expanduser('~')+'/.jamDB.json','w') as f:
    f.write(json.dumps(configuration, indent=2))
else:
  #other commands
  try:
    be = JamDB(args.database)
    if args.command=="print":
      print(be.output(args.item,True))
    elif args.command=='clean' and args.item=='all':
      be.cleanTree(all=True)
    else:
      be.changeHierarchy(args.item)
      if args.command=='clean':
        be.cleanTree(all=False)
      elif args.command=='scan':
        be.scanTree()
      elif args.command=='produce':
        be.scanTree('produceData')
      elif args.command=='compare':
        be.scanTree('compareToDB')
      elif args.command=='hierarchy':
        print(be.outputHierarchy(True,True))
      else:
        print("Wrong command:",args.command)
    be.exit()
  except:
    argparser.print_help()
    exit(1)
