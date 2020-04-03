#!/usr/bin/python3
import js2py

import json, re
import base64, io
import js2py, os
import numpy as np
from PIL import Image


def jsonValidator(data):
    """
    for debugging, test if valid json object
    - not really used

    Args:
       data: string to test
    """
    try:
        json.loads(json.dumps(data))
        return True
    except ValueError as error:
        print("**ERROR** invalid json: %s" % error)
        return False


def imageToString(url):
    """
    convert png file to b64-string
    - not really used

    future: test if jpeg and png strings are the same
    do I need to save jpeg, png as marker in list ['png',64byte]
    https://stackoverflow.com/questions/16065694/is-it-possible-to-create-encoded-base64-url-from-image-object

    Args:
       url: path to image
    """
    encoded = base64.b64encode(open(url, 'rb').read())
    aString = encoded.decode()
    return aString


def stringToImage(aString, show=True):
    """
    convert a b64-string to png file
    - not really used

    Args:
       aString: 64byte string of image
       show: show image
    """
    imgdata = base64.b64decode(aString)
    image = Image.open(io.BytesIO(imgdata))
    if show:
        image.show()
    return image


def createQRcodeSheet(fileName="../qrCodes.pdf"):
    """
    Documentation QR-codes
    - img = qrcode.make("testString",error_correction=qrcode.constants.ERROR_CORRECT_M)
    - or ERROR-CORRECT_H for better errorcorrection
    Sizes:
    - QR code size 1.5-2cm
    - with frame 2.25-3cm
    - Page size 18x27cm; 6x9 = 54
    """
    import qrcode
    from commonTools import commonTools as cT  # don't import globally since it disturbs translation
    img = qrcode.make(cT.uuidv4(),
                      error_correction=qrcode.constants.ERROR_CORRECT_M)
    size = img.size[0]
    hSize = 6*size
    vSize = 9*size
    new_im = Image.new('RGB', (hSize, vSize))
    for i in np.arange(0, hSize, size):
        for j in np.arange(0, vSize, size):
            img = qrcode.make(cT.uuidv4(),
                              error_correction=qrcode.constants.ERROR_CORRECT_M)
            new_im.paste(img, (i, j))
    new_im.save(fileName)
    return


def translateJS2PY():
    """
    Translate js-code to python-code using js2py lib
    - remove the last export-lines from commonTools.js
    """
    jsString = open('../ReactDOM/src/commonTools.js', "r").read()
    jsString = re.sub(r"export.+;", "", jsString)
    jsFile = io.StringIO(jsString)
    js2py.translate_file(jsFile, 'commonTools.py')



###########################################
##### MAIN FUNCTION
###########################################
if __name__ == "__main__":
    # translate js-code to python
    translateJS2PY()
    # prepare new sheet with QR-codes, does not hurt to create new
    createQRcodeSheet()
