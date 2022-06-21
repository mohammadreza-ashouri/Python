

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
  import os, json, shutil
  from zipfile import ZipFile, ZIP_DEFLATED

  #global variables
  elnName = None
  elnVersion = None

  def processPart(part):
    """
    recursive function call to process this node
    """
    success = True
    if not isinstance(part, dict):
      print("**ERROR in part",part)
      return False
    print('\nProcess:',part['@id'])
    # find next node to process
    newNode = [i for i in graph if '@id' in i and i['@id']==part['@id']]
    if len(newNode)>1:
      print('**ERROR multiple nodes with same id')
      return False
    # if node with more subnodes
    if len(newNode)==1:
      newNode = newNode[0]
      if elnName=='Kadi4Mat':
        docType = 'x'+str(len(newNode['@id'].split('/'))-2)
        newNode['pathOnKadi4Mat'] = newNode.pop('@id')
        newNode['-name'] = newNode.pop('name')
        if 'description' in newNode:
          newNode['comment']=newNode.pop('description')
      elif elnName=='PASTA ELN':
        docType = newNode['-type'][0]
        newNode['_id'] = newNode.pop('@id')
      else:
        print('**ERROR undefined ELN-Name', elnName)
      subparts = newNode.pop('hasPart') if 'hasPart' in newNode else []
      print('subparts:\n'+'\n'.join(['  '+i['@id'] for i in subparts]))
      if '@type' in newNode:
        del newNode['@type']
      if elnName=='PASTA ELN' and newNode['-type'][0]!='x0':
        backend.db.saveDoc(newNode)
        if newNode['-type'][0][0]=='x':
          os.makedirs(backend.basePath+newNode['-branch'][0]['path'])
        backend.currentID = newNode['_id']
      else:
        backend.addData(docType,newNode)
      if len(subparts)>0:  #don't do if no subparts: measurements, ...
        backend.changeHierarchy(backend.currentID)
        for subpart in subparts:
          processPart(subpart)
        backend.changeHierarchy(None)
    # ---
    # if final leaf node described in hasPart
    if len(part)>1:
      #save to file
      source = elnFile.open(dirName+os.sep+part['@id'])
      #do database entry
      if elnName=='Kadi4Mat':
        docType = 'measurement'
        part['otherELNName'] = part.pop('@id')
        part['-name'] = os.path.basename(part['otherELNName'])
        if 'description' in part:
          part['comment']=part.pop('description')
        del part['@type']
        targetFileName = os.path.basename(part['otherELNName'])
      elif elnName=='PASTA ELN':
        targetFileName = part['@id']
      else:
        print('**ERROR undefined ELN-Name', elnName)
      target = open(targetFileName, "wb")
      with source, target:  #extract one file to its target directly
        shutil.copyfileobj(source, target)
      if elnName!='PASTA ELN':
        backend.addData(docType,part)
    return

  ######################
  #main function
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
    for i in graph:
      if 'sdPublisher' in i:
        elnName = i['sdPublisher']['name']
        elnVersion = i['version']
        #iteratively go through list
        for part in i['hasPart']:
          processPart(part) #TODO_P2 first child should get elnName and version
  return True


def exportELN(backend, docID):
  import os, json, subprocess
  import base64, io, shutil
  from PIL import Image
  from datetime import datetime
  from zipfile import ZipFile, ZIP_DEFLATED
  docProject = backend.db.getDoc(docID)
  dirNameProject = docProject['-branch'][0]['path']
  zipFileName = dirNameProject+'.eln'
  print('Create eln file '+zipFileName)
  with ZipFile(zipFileName, 'w', compression=ZIP_DEFLATED) as zipFile:
    # numAttachments = 0
    graph = []

    #1 ------- write JSON files -------------------
    listDocs = backend.db.getView('viewHierarchy/viewHierarchy', startKey=docID)
    #create tree of hierarchical data
    treedata = {}

    def listChildren(id, level):
      """
      """
      items = [i for i in listDocs if len(i['key'].split(' '))==level]
      if id is not None:
        items = [i for i in items if i['key'].startswith(id)]
      #sort by child
      keys = [i['key'] for i in items]
      childNums = [i['value'][0] for i in items]
      items = [x for _, x in sorted(zip(childNums, keys))]
      #create sub-children
      for item in items:
        children = listChildren(item,level+1)
        treedata[item.split(' ')[-1]] = children
        if level == 1:
          treedata['__masterID__'] = item
      return [i.split(' ')[-1] for i in items]

    children = listChildren(id=None, level=1)
    masterID = treedata.pop('__masterID__')
    # print(treedata)
    for doc in treedata:
      doc = backend.db.getDoc(doc)
      if 'image' in doc:
        fileName = '__thumbnails__'+os.sep+doc['_id']
        if doc['image'].startswith('data:image/png'):
          fileName += '.png'
          imgdata = doc['image'][22:]
          imgdata = base64.b64decode(imgdata)
          imgdata = io.BytesIO(imgdata)
          target = zipFile.open(dirNameProject+os.sep+fileName,'w')
          with imgdata, target:  #extract one file to its target directly
            shutil.copyfileobj(imgdata, target)
        elif doc['image'].startswith('<?xml'):
          fileName += '.svg'
          zipFile.writestr(dirNameProject+os.sep+fileName, doc['image'])
        else:
          print('image type not implemented')
        del doc['image']
      doc['@id'] = doc.pop('_id')
      if len(treedata[doc['@id']])>0:
        doc['hasPart'] = [{'@id':i} for i in treedata[doc['@id']]]
      graph.append(doc)
      # # Attachments
      # if '_attachments' in doc:
      #   numAttachments += len(doc['_attachments'])
      #   for i in range(len(doc['_attachments'])):
      #     attachmentName = dirNameProject+os.sep+'__database__'+os.sep+doc['_id']+'/v'+str(i)+'.json'
      #     zipFile.writestr(attachmentName, json.dumps(doc.get_attachment('v'+str(i)+'.json')))

    #2 ------------------ write data-files --------------------------
    masterChildren = [{'@id':masterID}]
    for path, _, files in os.walk(dirNameProject):
      if '/.git' in path or '/.datalad' in path:
        continue
      path = os.path.relpath(path, backend.basePath)
      for iFile in files:
        if iFile.startswith('.git') or iFile=='.id_pastaELN.json':
          continue
        masterChildren.append({'@id':path+os.sep+iFile, '@type':'File'})
        zipFile.write(path+os.sep+iFile, dirNameProject+os.sep+path+os.sep+iFile)

    #3 ------------------- write index.json ---------------------------
    index = {}
    index['@context']= 'https://w3id.org/ro/crate/1.1/context'
    index
    # master node ro-crate-metadata.json
    cwd = backend.cwd
    os.chdir(backend.softwarePath)
    cmd = ['git','tag']
    output = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    os.chdir(backend.basePath+os.sep+cwd)
    masterNode  = {'@id':'ro-crate-metadata.json',\
      '@type':'CreativeWork',\
      'about': {'@id': './'},\
      'conformsTo': {'@id': 'https://w3id.org/ro/crate/1.1'},\
      'schemaVersion': 'v1.0',\
      'dateCreated': datetime.now().isoformat(),\
      'sdPublisher': {'@type':'Organization', 'name': 'PASTA ELN',\
        'logo': 'https://raw.githubusercontent.com/PASTA-ELN/desktop/main/pasta.png',\
        'slogan': 'The favorite ELN for experimental scientists',\
        'url': 'https://github.com/PASTA-ELN/',\
        'description':'Version '+output.stdout.decode('utf-8').split()[-1]},\
      'version': '1.0',\
      'hasPart': masterChildren\
      }
    #finalize file
    graph.append(masterNode)
    index['@graph'] = graph
    zipFile.writestr(dirNameProject+os.sep+'ro-crate-metadata.json', json.dumps(index, indent=2))
  return True

"""
Whishlist Kadi4Mat:
- no redundant info;
"""