$Id: README.txt,v 1.3 2005/12/17 13:13:16 chris Exp $

Installation:
-------------
Needs the cheutils package!

Put the urlregex and cheutils directories in your PYTHONPATH, e.g.:

$ mkdir -p ~/lib/python/urlregex ~/lib/python/cheutils
$ cp urlregex/*.py ~/lib/python/urlregex/
$ cp cheutils/*.py ~/lib/python/cheutils/
$ export PYTHONPATH="~/lib/python:$PYTHONPATH"

Copy the executables in the Exec directory in your PATH, e.g.:

$ cp urlregex/Exec/* cheutils/Exec/* ~/bin/
$ export PATH="~/bin:$PATH"
