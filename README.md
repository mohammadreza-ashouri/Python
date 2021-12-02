### About Main project
Main backend: install first! (Python backend of PASTA database)

Pasta-dishes are a mixture pasta and sauce, the latter adds flavors
and richness to the otherwise boring pasta. This database combines raw-data with rich metadata
to allow advanced data science. In the database, one
can fully adapt and improvise the metadata definitions to generate something novel. PASTA
uses a local-first approach: store all data and metadata locally (always accessible to user)
and synchronize with a server upon user request.

For Ubuntu and Windows, there are installation scripts in this list; We suggest to download those and use them.
- Windows:
  - download [install.bat](https://jugit.fz-juelich.de/pasta/main/-/blob/master/install.bat)
  - use cmd.exe and go to download folder
  - start script "install.bat"
- Linux:
  - download [install.sh](https://jugit.fz-juelich.de/pasta/main/-/blob/master/install.sh)
  - use terminal to change into folder, e.g. "cd ~/Downloads"
  - "chmod 755 install.sh"
  - "sudo ./install.sh"

Help for problems:
- General requirements and assumptions: 3GB (on disk C: on windows) and a 64-bit computer
- Often a restart helps because it updates environmental variables. Restart your shell (Windows: cmd.exe, Linux: bash).
  If the script stops twice at the same point, then it is time to read the next line.
- For Windows, the software is saved under "My Documents" in a subfolder. The data is at an arbitrary location. Future versions might allow more flexibility.
- If the graphical user interface (GUI) hangs:
  - "Ctrl-R" restarts it
- Contact Steffen and send the output of cmd.exe / bash as a file

More documentation is in the wiki-section (left-sidebar). [Easy link](https://jugit.fz-juelich.de/pasta/main/-/wikis/home)

Screenshots are in the GUI section: [Easy link](https://jugit.fz-juelich.de/pasta/gui)

