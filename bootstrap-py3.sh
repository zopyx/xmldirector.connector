#!/bin/sh
python3 -m venv .
./bin/pip install -r requirements.txt
./bin/buildout $*

