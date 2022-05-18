#!/bin/bash
echo "Installer for PASTA database on Ubuntu 20.04"
echo "IMPORTANT: if you have problems, visit https://jugit.fz-juelich.de/pasta/main/-/wikis/home#installation-scripts"
echo "Default choices are accepted by return: [Y/n]->yes; [default]->default"
echo
read -p "Do you wish to start installing now [Y/n] ? " yesno
if [[ $yesno = 'N' ]] || [[ $yesno = 'n' ]]
then
  echo "  Did not install anything"
  exit
fi
echo

echo "Ensure installer has sudo rights"
if [ "$EUID" -ne 0 ]
  then
  echo "  ERROR: Please run as root with 'sudo ./install.sh' "
  exit
fi
echo
THEUSER=$(logname)

echo "Ensure that conda is not running"
if conda &>/dev/null
then
  echo "  'conda' is installed; I deactivate it."
  conda deactivate
else
  echo "  Info: 'conda' is not installed."
fi

echo "Ensure python is installed"
OUTPUT=$(python3 --version)
IFS=' ' read -ra OUTPUT1 <<< "$OUTPUT"
IFS='.' read -ra OUTPUT2 <<< "${OUTPUT1[1]}"
if [ ${OUTPUT1[0]} = "Python" ] && [ ${OUTPUT2[0]} = "3" ]
then
  echo "  Python installed in version 3."
else
  echo "  Info: Python 3 will be installed."
  sudo apt install -y python3 >/dev/null
fi
echo
echo "Ensure openCV (as an example downstream package) for python is installed"
if dpkg --get-selections | grep -q "^python3-opencv[[:space:]]*install$" >/dev/null
then
  echo "  python3-opencv is installed"
else
  echo "  Info: Python-OpenCV will be installed. This takes a few minutes."
  sudo add-apt-repository universe       >> installLog.txt
  sudo apt install -y python3-opencv >> installLog.txt
fi
echo
echo "Ensure pip for python is installed"
if dpkg --get-selections | grep -q "^python3-pip[[:space:]]*install$" >/dev/null
then
  echo "  python3-pip is installed"
else
  echo "  Info: Python3-pip will be installed."
  sudo apt install -y python3-pip     >/dev/null
fi
echo

echo "Ensure pandoc is installed"
if command -v pandoc &> /dev/null
then
  echo "  pandoc installed."
else
  echo "  Info: pandoc will be installed. This takes a few minutes."
  sudo apt install -y pandoc          >> installLog.txt
fi
echo


echo "Install git, git-annex, datalad"
wget -O- http://neuro.debian.net/lists/focal.de-fzj.full | sudo tee /etc/apt/sources.list.d/neurodebian.sources.list
sudo apt-key adv --recv-keys --keyserver hkps://keyserver.ubuntu.com 0xA5D32F012649A5A9
sudo apt update >/dev/null
sudo apt install -y datalad >/dev/null


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
  if ! command -v display &> /dev/null
  then
    echo "  xv and display are NOT installed. Imagemagick will be installed."
    sudo apt install -y imagemagick                         >> installLog.txt
  fi
  if [ -f "/usr/bin/xv" ]; then
    echo "xv exists now."
  else
    echo "  Create link from display to xv."
    sudo ln -s /usr/bin/display /usr/bin/xv
  fi
fi
echo


echo "Ensure couchdb is installed"
if dpkg --get-selections | grep -q "^couchdb[[:space:]]*install$" >/dev/null
then
  echo "  couchdb is installed"
else
  echo "Install instructions:"
  echo "  choose Standalone installation. Rest: choose OK"
  read -p "  Continue [Y/n] ? " yesno
  if [[ $yesno = 'N' ]] || [[ $yesno = 'n' ]]
  then
    echo "  Did not install anything"
    exit
  fi
  echo
  sudo apt update
  sudo apt install -y curl apt-transport-https gnupg
  curl https://couchdb.apache.org/repo/keys.asc | gpg --dearmor | sudo tee /usr/share/keyrings/couchdb-archive-keyring.gpg >/dev/null 2>&1
  source /etc/os-release
  echo "deb [signed-by=/usr/share/keyrings/couchdb-archive-keyring.gpg] https://apache.jfrog.io/artifactory/couchdb-deb/ ${VERSION_CODENAME} main" \
      | sudo tee /etc/apt/sources.list.d/couchdb.list >/dev/null
  sudo apt update
  sudo apt install -y couchdb
fi
CDB_USER="admin"
echo "  The password and username are scrambled at first usage, hence not stored as plain-text. Both are in a vault."
read -p "  Which password did you enter? " CDB_PASSW
echo


echo "Two empty (for safety) directories are required. One for the source code"
echo "and the other as central place to store data, work in."
read -p "  Where to store the source code? [pasta_source, i.e. /home/${THEUSER}/pasta_source] " pasta_src
read -p "  Where to store the data? [pasta, i.e. /home/${THEUSER}/pasta] " pasta
if [ -z $pasta_src ]
then
  pasta_src="pasta_source"
fi
if [ -z $pasta ]
then
  pasta="pasta"
fi
sudo -u $THEUSER mkdir /home/$THEUSER/$pasta_src
sudo -u $THEUSER mkdir /home/$THEUSER/$pasta_src/pasta_tutorial
sudo -u $THEUSER mkdir /home/$THEUSER/$pasta
echo


echo "Start cloning the git repositories: tools, python-backend, javascript-frontend"
cd /home/$THEUSER/$pasta_src
sudo -u $THEUSER git clone https://jugit.fz-juelich.de/s.brinckmann/experimental-micromechanics.git
sudo -u $THEUSER git clone https://jugit.fz-juelich.de/pasta/main.git
sudo -u $THEUSER git clone https://jugit.fz-juelich.de/pasta/gui.git
echo


echo "Adopt path and python-path in your environment"
sudo -u $THEUSER echo "#PASTA changes" >> /home/$THEUSER/.bashrc
sudo -u $THEUSER echo "export PATH=\$PATH:/home/${THEUSER}/${pasta_src}/main" >> /home/$THEUSER/.bashrc
sudo -u $THEUSER echo "export PYTHONPATH=\$PYTHONPATH:/home/${THEUSER}/${pasta_src}/main" >> /home/$THEUSER/.bashrc
sudo -u $THEUSER echo "export PYTHONPATH=\$PYTHONPATH:/home/${THEUSER}/${pasta_src}/experimental-micromechanics/src" >> /home/$THEUSER/.bashrc
echo


echo "Install python requirements. This takes a few minutes."
cd /home/$THEUSER/$pasta_src/main
sudo -H pip3 install -r requirements.txt           >> installLog.txt
echo


echo "Create PASTA configuration file .pastaELN.json in home directory"
sudo -u $THEUSER echo "{" > /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "  \"softwareDir\": \"/home/${THEUSER}/${pasta_src}/main\"," >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "  \"userID\": \"${THEUSER}\"," >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "  \"default\": \"pasta_tutorial\"," >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "  \"magicTags\": [\"P1\",\"P2\",\"P3\",\"TODO\",\"WAIT\",\"DONE\"]," >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "  " >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "  \"links\": {" >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "    \"research\": {" >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "      \"local\": {" >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "        \"user\": \"${CDB_USER}\"," >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "        \"password\": \"${CDB_PASSW}\"," >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "        \"database\": \"pasta_tutorial\"," >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "        \"path\": \"/home/${THEUSER}/${pasta}\"" >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "      }," >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "      \"remote\": {}" >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "    }," >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "    " >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "    \"pasta_tutorial\": {" >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "      \"local\": {" >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "        \"user\": \"${CDB_USER}\"," >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "        \"password\": \"${CDB_PASSW}\"," >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "        \"database\": \"pasta_tutorial\"," >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "        \"path\": \"/home/${THEUSER}/${pasta_src}/pasta_tutorial\"" >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "      }," >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "      \"remote\": {}" >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "    }" >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "  }," >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "  " >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "  \"tableFormat\": {" >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "    \"x0\":{\"-label-\":\"Projects\",\"-default-\": [22,6,50,22]}," >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "    \"measurement\":{\"-default-\": [24,7,23,23,-5,-6,-6,-6]}," >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "    \"sample\":{\"-default-\": [23,23,23,23,-5]}," >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "    \"procedure\":{\"-default-\": [20,20,20,40]}" >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "  }" >> /home/$THEUSER/.pastaELN.json
sudo -u $THEUSER echo "}" >> /home/$THEUSER/.pastaELN.json
sudo chown $THEUSER:$THEUSER /home/$THEUSER/.pastaELN.json
echo


echo "Run a very short test for 5sec?"
cd /home/$THEUSER/$pasta_src/main
sudo PYTHONPATH=/home/$THEUSER/$pasta_src/main:/home/$THEUSER/$pasta_src/experimental-micromechanics/src -u $THEUSER python3 pastaELN.py test
echo
echo 'If this test is not successful, it is likely that you entered the wrong username'
echo "  and password. Open the file /home/$THEUSER/.pastaELN.json with an editor and correct"
echo '  the entries after "user" and "password". "-userID" does not matter. Entries under'
echo '  "remote" do not matter, either.'
sudo PYTHONPATH=/home/$THEUSER/$pasta_src/main:/home/$THEUSER/$pasta_src/experimental-micromechanics/src -u $THEUSER python3 pastaELN.py extractorScan
echo
echo "Run a short test for 20-40sec?"
sudo PYTHONPATH=/home/$THEUSER/$pasta_src/main:/home/$THEUSER/$pasta_src/experimental-micromechanics/src -u $THEUSER python3 Tests/testTutorial.py
echo


echo "Graphical user interface GUI"
echo "  Ensure npm is installed"
if command -v npm &> /dev/null
then
  echo "  npm installed."
else
  echo "  Info: npm will be installed."
  sudo apt install -y npm                         >> installLog.txt
fi
echo
cd /home/$THEUSER/$pasta_src/gui
sudo -u $THEUSER npm install                          >> installLog.txt


echo -e "\033[0;31m=========================================================="
echo -e "Last step: Start the graphical user interface. If you want to do that in "
echo -e "the future:"
echo -e "  cd /home/$THEUSER/$pasta_src/gui"
echo -e "  npm start"
echo -e "During first run of the GUI, click 'Test Backend' in CONFIGURATION/Top-left corner."
echo -e "It is good to start with Projects, then Samples and Procedures and finally"
echo -e "Measurements."
echo -e "==========================================================\033[0m"
echo
sudo PATH=$PATH:/home/$THEUSER/$pasta_src/main -u $THEUSER npm start

echo -e "\033[0;31m=========================================================="
echo -e "Last step: Start the graphical user interface. If you want to do that in "
echo -e "the future:"
echo -e "  cd /home/$THEUSER/$pasta_src/gui"
echo -e "  npm start"
echo -e "During first run of the GUI, click 'Test Backend' in CONFIGURATION/Top-left corner."
echo -e "It is good to start with Projects, then Samples and Procedures and finally"
echo -e "Measurements."
echo -e "==========================================================\033[0m"
echo
