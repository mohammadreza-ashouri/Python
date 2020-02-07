import json, re


def jsonValidator(data):
  """
  for debugging, test if valid json object

  Args: 
     data: string to test
  """
  try:
    json.loads(json.dumps(data) )
    return True
  except ValueError as error:
    print("**ERROR** invalid json: %s" % error)
    return False


def string2TagFieldComment(comment):
  """
  extract tags, fields and comments from string

  Args:
     comment: input string
  """
  reply = {}
  tags = re.findall("#[\S]+",comment)
  for tag in tags:
    comment = comment.replace(tag,"")
  reply["tags"] = [tag[1:] for tag in tags]
  fields = re.findall(":[\S]+:[\S]+:",comment)
  for field in fields:
    comment = comment.replace(field,"")
    _, key, value, _ = field.split(":")
    try:
      value = float(value)
    except:
      pass
    reply[key] = value
  reply["comment"] = comment.strip().replace("  "," ")
  return reply
