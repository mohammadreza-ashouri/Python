#!/bin/bash
echo "Installer for jamDB on Ubuntu Systems"
echo
echo "Ensure installer has sudo rights"
if [ "$EUID" -ne 0 ]
  then
  echo "  ERROR: Please run as root with 'sudo ./install.sh' "
  exit
fi
echo
THEUSER=$(logname)


echo "Ensure python is installed"
OUTPUT=$(python3 --version)
IFS=' ' read -ra OUTPUT1 <<< "$OUTPUT"
IFS='.' read -ra OUTPUT2 <<< "${OUTPUT1[1]}"
if [ ${OUTPUT1[0]} = "Python" ] && [ ${OUTPUT2[0]} = "3" ]
then
  echo "  Python installed in version 3."
else
  echo "  Info: Python 3 not installed."
  read -p "  Do you wish to install it now [Y/n] ? " yesno
  if [[ $yesno = 'N' ]] || [[ $yesno = 'n' ]]
  then
    echo "  Did not install python"
    exit
  else
    sudo apt-get install -y python3
  fi
fi
echo
echo "Ensure openCV for python is installed"
if dpkg --get-selections | grep -q "^python3-opencv[[:space:]]*install$" >/dev/null
then
  echo "  python3-opencv is installed"
else
  read -p "  Do you wish to install python3-openCV [Y/n] ? " yesno
  if [[ $yesno = 'N' ]] || [[ $yesno = 'n' ]]
  then
    echo "  Did not install python3-opencv"
    exit
  else
    sudo apt-get install -y python3-opencv
  fi
fi
echo


echo "Ensure git is installed"
if command -v git &> /dev/null
then
  echo "  git installed."
else
  echo "  Info: git not installed."
  read -p "  Do you wish to install it now [Y/n] ? " yesno
  if [[ $yesno = 'N' ]] || [[ $yesno = 'n' ]]
  then
    echo "  Did not install git"
    exit
  else
    sudo apt-get install -y git
  fi
fi
echo
echo "Ensure git-annex is installed"
if command -v git-annex &> /dev/null
then
  echo "  git-annex installed."
else
  echo "  Info: git-annex not installed."
  read -p "  Do you wish to install it now [Y/n] ? " yesno
  if [[ $yesno = 'N' ]] || [[ $yesno = 'n' ]]
  then
    echo "  Did not install git-annex"
    exit
  else
    sudo apt-get install -y git-annex
  fi
fi
OUTPUT=$(sudo -u $THEUSER git config -l | grep "user")
if [[ -n $OUTPUT ]]
then
  echo "  git user and email are set"
else
  echo "  Set your git user information"
  read -p "  What is your name? " GIT_NAME
  read -p "  What is your email? " GIT_EMAIL
  sudo -u $THEUSER git config --global --add user.name "${GIT_NAME}"
  sudo -u $THEUSER git config --global --add user.email $GIT_EMAIL
fi
echo


echo "Ensure xv works, which is required for python-pillow"
if command -v xv &> /dev/null
then
  echo "  xv is present"
else
  echo "  xv is not present. Try display"
  if ! command -v xv &> /dev/null
  then
    echo "  xv and display NOT installed."
    read -p "  Do you wish to install imagemagick now [Y/n] ? " yesno
    if [[ $yesno = 'N' ]] || [[ $yesno = 'n' ]]
    then
      echo "  Did not install imagemagick"
      exit
    else
      sudo apt-get install -y imagemagick
    fi
  fi
  read -p "  Do you wish to create link from display to xv [Y/n] ? " yesno
  if [[ $yesno = 'N' ]] || [[ $yesno = 'n' ]]
  then
    echo "  Did not create link"
    exit
  else
    sudo ln -s /usr/bin/display /usr/bin/xv
  fi
fi
echo


echo "Ensure couchdb is installed"
if dpkg --get-selections | grep -q "^couchdb[[:space:]]*install$" >/dev/null
then
  echo "  couchdb is installed"
else
  read -p "  Do you wish to install couchdb [Y/n] ? " yesno
  if [[ $yesno = 'N' ]] || [[ $yesno = 'n' ]]
  then
    echo "  Did not install couchdb"
    exit
  else
    sudo apt-get install -y gnupg ca-certificates
    echo "deb https://apache.bintray.com/couchdb-deb focal main" | sudo tee /etc/apt/sources.list.d/couchdb.list
    sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 8756C4F765C9AC3CB6B85D62379CE192D401AB61
    sudo apt update
    sudo apt install -y couchdb
  fi
fi
if command -v firefox &> /dev/null
then
  echo "  firefox is present"
  WEBBROWSER='firefox'
else
  if command -v chromium &> /dev/null
  then
    echo "  chromium is present"
    WEBBROWSER='chromium'
  else
    echo "  neither firefox nor chromium are present."
    read -p "  What is your webbrowser? " WEBBROWSER
    if command -v ${WEBBROWSER} &> /dev/null
    then
      echo "  ${WEBBROWSER} is present"
    else
      echo "  No webbrowser found"
      exit
    fi
  fi
fi
echo
echo "Start of webbrowser, please setup administrator and password for couchDB"
echo "These will be saved on the harddisk in a file in plain text. Since this"
echo "port cannot be reached from outside, there is no real danger."
sudo -u $THEUSER $WEBBROWSER 127.0.0.1:5984/_utils/
read -p "  Which user name did you enter? " CDB_USER
read -p "  Which password did you enter? " CDB_PASSW
echo


echo "Two empty (for safety) directories are required. One for the source code"
echo "and the other as central place to store data, work in."
read -p "  Where to store the source code? [jamDB_Source, i.e. /home/${THEUSER}/jamDB_Source] " jamDB_src
read -p "  Where to store the data? [jamDB, i.e. /home/${THEUSER}/jamDB] " jamDB
read -p "  What is your user id, e.g. orcid-id. Only small letters [random_user] ? " jamDB_user
if [ -z $jamDB_src ]
then
  jamDB_src="jamDB_Source"
fi
if [ -z $jamDB ]
then
  jamDB="jamDB"
fi
if [ -z $jamDB_user ]
then
  jamDB_user="random_user"
fi
sudo -u $THEUSER mkdir /home/$THEUSER/$jamDB_src
sudo -u $THEUSER mkdir /home/$THEUSER/$jamDB_src/jamDB_tutorial
sudo -u $THEUSER mkdir /home/$THEUSER/$jamDB
echo


echo "Start cloning the git repositories: tools, python-backend, javascript-frontend"
cd /home/$THEUSER/$jamDB_src
sudo -u $THEUSER git clone https://jugit.fz-juelich.de/s.brinckmann/experimetal-micromechanics.git
sudo -u $THEUSER git clone https://jugit.fz-juelich.de/s.brinckmann/jamdb-python.git
sudo -u $THEUSER git clone https://jugit.fz-juelich.de/s.brinckmann/jamdb-reactelectron.git
echo


echo "Adopt path and python-path in your environment"
read -p "  Do you wish to append the .bashrc file [Y/n] ? " yesno
if [[ $yesno = 'N' ]] || [[ $yesno = 'n' ]]
then
  echo "  Did not append the .bashrc file."
  exit
else
  sudo -u $THEUSER echo "#jamDB changes" >> /home/$THEUSER/.bashrc
  sudo -u $THEUSER echo "export PATH=\$PATH:/home/${THEUSER}/${jamDB_src}/jamdb-python" >> /home/$THEUSER/.bashrc
  sudo -u $THEUSER echo "export PYTHONPATH=\$PYTHONPATH:/home/${THEUSER}/${jamDB_src}/jamdb-python" >> /home/$THEUSER/.bashrc
  sudo -u $THEUSER echo "export PYTHONPATH=\$PYTHONPATH:/home/${THEUSER}/${jamDB_src}/experimetal-micromechanics" >> /home/$THEUSER/.bashrc
fi
echo


echo "Install python requirements"
cd /home/$THEUSER/$jamDB_src/jamdb-python
read -p "  Do you wish to install these requirements [Y/n] ? " yesno
if [[ $yesno = 'N' ]] || [[ $yesno = 'n' ]]
then
  echo "  Did not install requirements"
  exit
else
  cd /home/$THEUSER/$jamDB_src/jamdb-python
  sudo -H pip3 install -r requirements.txt
fi
echo


echo "Create jamDB configuration file .jamDB.json in home directory"
read -p "  Do you wish to create a file .jamDB.json in your home folder [Y/n] ? " yesno
if [[ $yesno = 'N' ]] || [[ $yesno = 'n' ]]
then
  echo "  Did not create .jamDB.json file."
  exit
else
  sudo -u $THEUSER echo "{" > /home/$THEUSER/.jamDB.json
  sudo -u $THEUSER echo "  \"-userID\": \"${jamDB_user}\"," >> /home/$THEUSER/.jamDB.json
  sudo -u $THEUSER echo "  \"-defaultLocal\": \"local\"," >> /home/$THEUSER/.jamDB.json
  sudo -u $THEUSER echo "  \"-defaultRemote\": \"remote\"," >> /home/$THEUSER/.jamDB.json
  sudo -u $THEUSER echo "  \"-eargs\": {\"editor\": \"emacs\", \"ext\": \".org\", \"style\": \"all\"}," >> /home/$THEUSER/.jamDB.json
  sudo -u $THEUSER echo "  \"-magicTags\": [\"P1\",\"P2\",\"P3\",\"TODO\",\"WAIT\",\"DONE\"]," >> /home/$THEUSER/.jamDB.json
  sudo -u $THEUSER echo "  " >> /home/$THEUSER/.jamDB.json
  sudo -u $THEUSER echo "  \"local\": {" >> /home/$THEUSER/.jamDB.json
  sudo -u $THEUSER echo "    \"user\": \"${CDB_USER}\"," >> /home/$THEUSER/.jamDB.json
  sudo -u $THEUSER echo "    \"password\": \"${CDB_PASSW}\"," >> /home/$THEUSER/.jamDB.json
  sudo -u $THEUSER echo "    \"database\": \"${jamDB_user}\"," >> /home/$THEUSER/.jamDB.json
  sudo -u $THEUSER echo "    \"path\": \"${jamDB}\"" >> /home/$THEUSER/.jamDB.json
  sudo -u $THEUSER echo "  }," >> /home/$THEUSER/.jamDB.json
  sudo -u $THEUSER echo "  " >> /home/$THEUSER/.jamDB.json
  sudo -u $THEUSER echo "  \"jamDB_tutorial\": {" >> /home/$THEUSER/.jamDB.json
  sudo -u $THEUSER echo "    \"user\": \"${CDB_USER}\"," >> /home/$THEUSER/.jamDB.json
  sudo -u $THEUSER echo "    \"password\": \"${CDB_PASSW}\"," >> /home/$THEUSER/.jamDB.json
  sudo -u $THEUSER echo "    \"database\": \"jamdb_tutorial\"," >> /home/$THEUSER/.jamDB.json
  sudo -u $THEUSER echo "    \"path\": \"${jamDB_src}/jamDB_tutorial\"" >> /home/$THEUSER/.jamDB.json
  sudo -u $THEUSER echo "  }," >> /home/$THEUSER/.jamDB.json
  sudo -u $THEUSER echo "  " >> /home/$THEUSER/.jamDB.json
  sudo -u $THEUSER echo "  \"remote\": {" >> /home/$THEUSER/.jamDB.json
  sudo -u $THEUSER echo "    \"user\": \"____\"," >> /home/$THEUSER/.jamDB.json
  sudo -u $THEUSER echo "    \"password\": \"____\"," >> /home/$THEUSER/.jamDB.json
  sudo -u $THEUSER echo "    \"url\": \"https://____\"," >> /home/$THEUSER/.jamDB.json
  sudo -u $THEUSER echo "    \"database\": \"____\"" >> /home/$THEUSER/.jamDB.json
  sudo -u $THEUSER echo "  }" >> /home/$THEUSER/.jamDB.json
  sudo -u $THEUSER echo "}" >> /home/$THEUSER/.jamDB.json
fi
echo


read -p "Run a test for 30sec - 2min [Y/n] ? " yesno
if [[ $yesno = 'N' ]] || [[ $yesno = 'n' ]]
then
  echo "  Did not run test"
  exit
else
  cd /home/$THEUSER/$jamDB_src/jamdb-python
  sudo PYTHONPATH=/home/$THEUSER/$jamDB_src/jamdb-python:/home/$THEUSER/$jamDB_src/experimetal-micromechanics/src -u $THEUSER python3 Tests/testTutorial.py
fi
echo


echo "Graphical user interface GUI"
read -p "  Do you wish to install graphical user interface requirements [Y/n] ? " yesno
if [[ $yesno = 'N' ]] || [[ $yesno = 'n' ]]
then
  echo "  Did not install requirements"
  exit
else
  cd /home/$THEUSER/$jamDB_src/jamdb-reactelectron
  sudo -u $THEUSER npm install
fi
echo -e "\033[0;31m=========================================================="
echo -e "Last step: Start the graphical user interface. If you want to do that in "
echo -e "the future:"
echo -e "  cd /home/$THEUSER/$jamDB_src/jamdb-reactelectron"
echo -e "  npm start"
echo -e "During the first run of the GUI, click 'Test Backend' in CONFIGURATION. It"
echo -e "is good to start with Projects, then Samples and Procedures and finally"
echo -e "Measurements."
echo -e "==========================================================\033[0m"
echo
sudo PATH=$PATH:/home/$THEUSER/$jamDB_src/jamdb-python -u $THEUSER npm start
