#!/bin/bash

set -x

export PATH=\
/opt/buildout.python/bin:\
$PATH:

echo $CONNECTOR_URL
echo $PLONE_VERSION
echo $DOCKER
echo $DOCKER_OPTIONS

config=buildout-plone-$PLONE_VERSION.cfg

docker run -d $DOCKER_OPTIONS $DOCKER

#virtualenv --clear .
#python3 -m venv .
pip install setuptools==36.6.0
pip install zc.buildout
buildout bootstrap
buildout -c $config

if [[ $TYPE  == 'OWNCLOUD' ]]
then
    wget http://localhost:8080
fi

bin/test -s xmldirector.connector

