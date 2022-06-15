

def importELN(backend, database, elnFileName):
  '''
  import .eln file from other ELN or from PASTA

  Args:
    backend (backend): backend
    database (string): name of database
    elnFileName (string): name of file

  Returns:
    success as bool
  '''
  import os, json
  from zipfile import ZipFile, ZIP_DEFLATED
  with ZipFile(elnFileName, 'r', compression=ZIP_DEFLATED) as elnFile:
    files = elnFile.namelist()
    dirName=files[0].split(os.sep)[0]
    if dirName+'/ro-crate-metadata.json' not in files:
      print('**ERROR: ro-crate does not exist in folder. EXIT')
      return False
    graph = json.loads(elnFile.read(dirName+'/ro-crate-metadata.json'))["@graph"]
    # print(json.dumps(graph,indent=2))
    #find information from master node
    elnName, elnVersion = '', ''
    parts = []
    for i in graph:
      if 'sdPublisher' in i:
        elnName = i['sdPublisher']['name']
        elnVersion = i['version']
        parts = i['hasPart']
    #iteratively go through list
    while len(parts)>0:
      part = parts.pop()
      # print('Process:',part)
      if isinstance(part, dict):
        partName = part['@id']
      elif isinstance(part, string):
        partName = part
      else:
        print("**ERROR in part",part)
        return False
      newNode = [i for i in graph if '@id' in i and i['@id']==partName]
      if len(newNode)>1:
        print('**ERROR multiple nodes with same id')
        return False
      if len(newNode)==1:
        newNode = newNode[0]
        parts += newNode['hasPart']
        docType = 'x'+str(len(newNode['@id'].split('/'))-2)
        newNode['pathOnKadi4Mat'] = newNode.pop('@id')
        newNode['-name'] = newNode.pop('name')
        newNode['comment']=newNode.pop('description')
        del newNode['hasPart']
        del newNode['@type']
        backend.addData(docType,newNode)
      if len(part)>1:
        docType = 'measurement'
        newNode['-name'] = newNode.pop('@id')
        newNode['comment']=newNode.pop('description')
        del newNode['@type']
        elnFile.extract(dirName+os.sep+newNode['-name'], path=backend.cwd)
        print('Add file to DB 2',json.dumps(part,indent=2))
        a = 4/0

  # print('\n',json.dumps(i,indent=2))
  # print('\n'.join(files),'\n')
  # print('\n\nHere',database, elnName, elnVersion)

  return True