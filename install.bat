@echo off
REM print content line. No " '
echo Installer for PASTA database on Windows Systems
echo IMPORTANT: always select to adjust the PATH VARIABLE during installation.
echo IMPORTANT: if you have problems, visit https://jugit.fz-juelich.de/s.brinckmann/pasta_python/-/wikis/home#installation-scripts
REM print empty line
echo.
REM ask for user input
echo Two empty (for safety) directories are required. One for the source code
echo and the other as central place to store data, work in.
set softwareDir=
set pasta=
set pasta_user=
set /p softwareDir="Which subdirectory of 'My Documents' should the software be installed to [e.g. pasta_source]? "
set /p pasta="Which subdirectory of 'My Documents' should the data be stored [e.g. pasta]? "
set /p pasta_user=" What is your user id, e.g. orcid-id. Only small letters [random_user] "
REM check for empty line
if not defined softwareDir (set softwareDir=pasta_source)
if not defined pasta (set pasta=pasta)
if not defined pasta_user (set pasta_user=random_user)
set softwareDir=%HOMEDRIVE%%HOMEPATH%\Documents\%softwareDir%
set downloadDir=%softwareDir%\tempDownload
mkdir %softwareDir%
mkdir %downloadDir%
mkdir %HOMEDRIVE%%HOMEPATH%\Documents\%pasta%
echo.


REM Install Python, Set PAPTH, Set PYTHONPATH, Install some python-packages
echo Ensure that the ordinary python is installed
echo Anaconda is not supported since it uses the
echo.  conda-framework which makes it difficult to
echo.  (1) install custom packages, (2) run your own
echo.  python programs from windows. It basically
echo.  creates a bubble, which is difficult to
echo.  penetrate. If you have it installed, stop here,
echo.  uninstall Anaconda and restart this script.
pause
FOR /F "tokens=* USEBACKQ" %%F in (`python --version`) do (set var=%%F)
echo %var% | findstr /C:"Python 3" 1>nul
REM echo with preceeding space
REM chain commands, use & at beginning of new line
if errorlevel==1 (echo.  Download python now) else (echo.  Python is installed in version 3.& goto end_python)
pause
if not exist %downloadDir%/python-3.8.7-amd64.exe (bitsadmin.exe /TRANSFER python3 https://www.python.org/ftp/python/3.8.7/python-3.8.7-amd64.exe  %downloadDir%/python-3.8.7-amd64.exe)
echo IMPORTANT: SELECT "Add Python 3.8 to PATH" inside the installer
pause
start /WAIT %downloadDir%/python-3.8.7-amd64.exe
:end_python
echo.


echo Set environment variables: PATH
echo %PATH% | findstr "pasta_python">nul
REM echo with preceeding space
REM chain commands, use & at beginning of new line
if errorlevel==1 (echo.  setting path now^
  & echo CANNOT DO THIS AUTOMATICALLY. Please do manually:^
  & echo.  Adopt the Environment Variables. Click start-button and type^
  & echo.  "Enviro" and select "Edit environmenal variables for your account"^
  & echo.  from the search results. In the window for USER-VARIABLES, click^
  & echo.  on "Path" and "Edit...". Click new three times and enter each time^
  & echo.  with copy-paste if content is already inside, skip it^
  & echo.  - C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python38^
  & echo.  - C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python38\Scripts^
  & echo.  - %softwareDir%\pasta_python^
  & echo.^
  & pause
  ) else (echo.  no need to set path variable as it seems to be correct)
echo.
REM this does not work in a reproducable fashion
REM  setx PATH "%PATH%;C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python38;C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python38\Scripts;%softwareDir%\pasta_python"^

echo Verify that python works
FOR /F "tokens=* USEBACKQ" %%F in (`python --version`) do (set var=%%F)
echo Output: %var%
echo.

echo Install basic python packages
pip.exe install --disable-pip-version-check win-unicode-console
pip.exe install --disable-pip-version-check matplotlib pandas wget spyder opencv-python
echo.

echo Test if python is fully working: plot a sine-curve
set var=void void
set /p var="  Skip sine-curve [y/N] "
echo %var% | findstr "y">nul
if errorlevel==1 (python.exe -c "import numpy as np;x = np.linspace(0,2*np.pi);y = np.sin(x);import matplotlib.pyplot as plt;plt.plot(x,y);plt.show()")
echo.
echo If error occured with numpy: there is some issue with Windows
echo.  and some basic fuction. Click start button and type: cmd and
echo.  commandline tool. Enter "pip install numpy==1.19.3" in it.
echo.
echo Spyder is a helpful Tool for writing python code. Search for
echo.  "spyder" on your hard-disk and pin it to start.
echo.
echo If you only care about python, stop here.
echo.
pause


REM START WITH PANDOC
echo Install pandoc
set var=void void
FOR /F "tokens=* USEBACKQ" %%F in (`where pandoc`) do (set var=%%F)
echo %var% | findstr "void">nul
if errorlevel==1 (echo. Pandoc is installed & goto end_pandoc)
echo.  Download Pandoc now
if not exist %downloadDir%\pandoc-2.11.3.2-windows-x86_64.msi (python.exe -m wget -o %downloadDir% https://github.com/jgm/pandoc/releases/download/2.11.3.2/pandoc-2.11.3.2-windows-x86_64.msi)
start /WAIT %downloadDir%\pandoc-2.11.3.2-windows-x86_64.msi
:end_pandoc
echo.


REM START WITH GIT, Git-annex, git-credentials
echo Install git
set var=void void
FOR /F "tokens=* USEBACKQ" %%F in (`where git`) do (set var=%%F)
echo %var% | findstr "void">nul
if errorlevel==1 (echo. Git is installed) else (^
  echo.  Download git now^
  & python.exe -m wget -o %downloadDir% https://github.com/git-for-windows/git/releases/download/v2.30.0.windows.1/Git-2.30.0-64-bit.exe^
  & echo IMPORTANT: In "Adjusting your path environment" select: "Run Git from the Windows Command Prompt"
  & pause
  & start /WAIT %downloadDir%\Git-2.30.0-64-bit.exe^
  )
echo.
echo Install git-annex
set var=void void
FOR /F "tokens=* USEBACKQ" %%F in (`where git-annex`) do (set var=%%F)
echo %var% | findstr "void">nul
if errorlevel==1 (echo. Git-annex is installed) else (^
  echo.  Download git-annex now^
  & python.exe -m wget -o %downloadDir% https://downloads.kitenet.net/git-annex/windows/7/current/git-annex-installer.exe^
  & start /WAIT %downloadDir%\git-annex-installer.exe^
  )
echo.
echo Check git credentials
set var=void void
FOR /F "tokens=* USEBACKQ" %%F in (`git config --global --get user.name`) do (set var=%%F)
echo %var% | findstr "void">nul
if errorlevel==1 (echo.  git-username is set & goto end_user_name)
echo.  set git-username credentials
set /p var="  What is your name? "
git config --global --add user.name "%var%"
:end_user_name
set var=void void
FOR /F "tokens=* USEBACKQ" %%F in (`git config --global --get user.email`) do (set var=%%F)
echo %var% | findstr "void">nul
if errorlevel==1 (echo.  git-email is set & goto end_git_email)
echo.  set git-email credentials
set /p var="  What is your email address? "
git config --global --add user.email "%var%"
:end_git_email
echo.


REM Start with couchDB
echo Install couchDB
echo.  If Windows warns you, go to **more information** and
echo.  **run anyway**. Remeber the user and password that you
echo.  enter in the setup utility. If the webbrowser does not
echo.  start automatically, go to http://localhost:5984/_utils
echo.
if exist "%ProgramFiles%\Apache CouchDB\bin" (goto end_couchdb)
if not exist %downloadDir%/apache-couchdb-3.1.1.msi (python.exe -m wget -o %downloadDir% https://couchdb.neighbourhood.ie/downloads/3.1.1/win/apache-couchdb-3.1.1.msi)
start /WAIT %downloadDir%\apache-couchdb-3.1.1.msi
:end_couchdb

echo Please note: user name and password are scrambled at first usage, aka they are not stored as plain text but in vault.
set /p CDB_USER="Which user-name did you use? [admin] "
set /p CDB_PASSW="Which password did you enter? "
if not defined CDB_USER (set CDB_USER=admin)


REM Clone source from repository; set PYTHONPATH
echo Clone files from repositories
cd %softwareDir%
git clone https://jugit.fz-juelich.de/s.brinckmann/experimental-micromechanics
git clone https://jugit.fz-juelich.de/s.brinckmann/pasta_python.git
git clone https://jugit.fz-juelich.de/s.brinckmann/pasta_electron.git

echo Set environment variables: PYTHONPATH
setx PYTHONPATH "%softwareDir%\experimental-micromechanics\src;%softwareDir%\pasta_python"
echo.

echo Install python libraries for backend
cd %softwareDir%\pasta_python
pip.exe install --disable-pip-version-check -r requirements.txt
pip.exe install --disable-pip-version-check pywin32 pywin32-ctypes
echo.

echo Create basic .pasta.json configuration
cd %HOMEDRIVE%%HOMEPATH%
echo { > .pasta.json
echo   "-userID": "%pasta_user%",>> .pasta.json
echo   "-defaultLocal": "pasta_tutorial",>> .pasta.json
echo   "-defaultRemote": "remote",>> .pasta.json
echo   "-eargs": {"editor": "emacs", "ext": ".org", "style": "all"},>> .pasta.json
echo   "-magicTags": ["P1","P2","P3","TODO","WAIT","DONE"],>> .pasta.json
echo.  >> .pasta.json
echo   "pasta_tutorial": {>> .pasta.json
echo     "user": "%CDB_USER%",>> .pasta.json
echo     "password": "%CDB_PASSW%",>> .pasta.json
echo     "database": "pasta_tutorial",>> .pasta.json
echo     "path": "Documents\\%pasta%">> .pasta.json
echo   },>> .pasta.json
echo.  >> .pasta.json
echo   "remote": {>> .pasta.json
echo     "user": "____",>> .pasta.json
echo     "password": "____",>> .pasta.json
echo     "url": "https://____",>> .pasta.json
echo     "database": "____">> .pasta.json
echo   },>> .pasta.json
echo.  >> .pasta.json
echo   "-tableFormat-": {>> .pasta.json
echo     "project":{"-label-":"Projects","-default-": [22,6,50,22]},>> .pasta.json
echo     "measurement":{"-default-": [24,7,23,23,-5,-6,-6,-6]},>> .pasta.json
echo     "sample":{"-default-": [23,23,23,23,-5]},>> .pasta.json
echo     "procedure":{"-default-": [20,20,20,40]}>> .pasta.json
echo   }>> .pasta.json
echo }>> .pasta.json
echo.


REM Run a two short tests of the python backend
echo Run a very short (5sec) test of the python backend
cd %softwareDir%\pasta_python
python pastaDB.py test
echo.
echo If this test is not successful, it is likely that you entered the wrong username
echo.  and password. Open the file %HOMEDRIVE%%HOMEPATH%\.pasta.json in an editor and
echo.  correct the entries after "user" and "password". "-userID" does not matter.
echo.  Entries under "remote" do not matter.
echo.
echo Run a short (20-80sec) test of the python backend
python Tests\testTutorial.py
echo.


REM START WITH NODE, NPM, do "npm install" and "npm start"
echo Install NPM
set var=void void
FOR /F "tokens=* USEBACKQ" %%F in (`where npm`) do (set var=%%F)
echo %var% | findstr "void">nul
if errorlevel==1 (echo. NPM is installed & goto end_npm)
echo.  Download NPM now
if not exist %downloadDir%\node-v14.15.4-x64.msi (python.exe -m wget -o %downloadDir% https://nodejs.org/dist/v14.15.4/node-v14.15.4-x64.msi)
start /WAIT %downloadDir%\node-v14.15.4-x64.msi
:end_npm
echo.

echo install graphical user interface (GUI) requirements
echo Don't care about vulnerablies right now in this test.
cd %softwareDir%\pasta_electron
cmd /c "npm install"

echo.
echo ==========================================================
echo Start the graphical user interface. If you want to do that in
echo the future:
echo.  cd %softwareDir%\pasta_electron
echo.  npm start
echo Enjoy this test version. Ctrl-C stops the command-prompt,
echo.  sometimes multiple are required.
echo ==========================================================
echo.
npm start

pause
