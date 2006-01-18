$Hg: README.txt,v$

Installation:
-------------
Needs the cheutils package!

Put the tpager and cheutils directories in your PYTHONPATH, e.g.:

$ mkdir -p ~/lib/python/tpager ~/lib/python/cheutils
$ cp tpager/*.py ~/lib/python/urlregex/
$ cp cheutils/*.py ~/lib/python/cheutils/
$ export PYTHONPATH="~/lib/python:$PYTHONPATH"

Copy the sigpager executable in the Exec directory in your PATH,
e.g.:

$ cp tpager/Exec/sigpager ~/bin/
$ export PATH="~/bin:$PATH"
