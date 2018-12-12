#!/bin/sh
virtualenv-2.7 --clear .
./bin/pip install -r requirements.txt
./bin/buildout $*

