xmldirector.connector
=====================


``xmldirector.connector`` integrates  Plone 5 with 

- local filesystem
- WebDAV-backed backend
- AWS S3
- remote servers over SFTP/SSH

``xmldirector.connector`` provides a ``Connector`` content-type that
mounts a particular storage into Plone. 

No support for indexing and search mounted content.



Requirements
------------

- Plone 5.2 with Python 3.6 or higher (tested)

- Supported backends:

    - eXist-db 

    - Base-X 

    - OwnCloud
    
    - Alfresco

    - Marklogic Server

    - AWS S3

    - Cloud federation services

      - Otixo.com
      - Storagemadeeasy.com


Configuration
-------------

Goto the Plone control panel and click on the ``XML-Director Connector`` configlet and
configure the your service

ExistDB
+++++++
  
- `webdav://localhost:6080/existdb/webdav/db`
- username and password required to access your XML database over WebDAV

BaseX
+++++

- `webdav://localhost:8984/webdav`                                     
- username and password required to access your XML database over WebDAV

Owncloud
++++++++

- `webdav://hostname:port/remote.php/webdav`
- username and password required to access your Owncloud instance over WebDAV

Alfresco
++++++++

- `webdav://hostname:port/webdav`
- username and password required to access your Alfresco instance over WebDAV

Local filesystem
++++++++++++++++

- `file:///path/to/some/directory`
- no support for credentials, the referenced filesystem must be readable (and writable)

AWS S3
++++++
    
- `s3://bucketname`
- enter your AWS access key as username and the AWS secret key as password
  (You need to install the Python package `fs-s3fs` through buildout).

SSH/SFTP
++++++++

- `ssh://hostname.com` or `sftp://hostname.com`
  (You need to install the Python package `fs.sshfs` through buildout).



API notes
+++++++++

The implementation of `xmldirector.connector` is heavily backed by the PyFilesystem 2 API.
Every `Connector` instance in Plone gives you access to the mounted storage through the 
`handle = connector.get_handle()` call which is instance of `fs.base.FS`. Check
https://docs.pyfilesystem.org for details.

Compatiblity with rclone
------------------------

An alternative to using native drivers under the hood, using `rclone`
(https://rclone.org/) is meanwhile perhaps the better solution. `rclone` is an
application (a commandline utility) to interact with up to 40 different storage
systems out of the box. `rclone` also allows you to mount different storages
directly into your filesystem (tested on Linux but supposed to work on Mac and
Windows too).  So for example, you can mount your Dropbox and Google Drive
storages into your local filesystem under `/mnt/dropbox` and `/mnt/drive` and
point your connector instances to `file:///mnt/dropbox` and
`file:///mnt/drive`.  So any interaction would happen through the filesystem
driver of Pyfilesystem. The underlying communication with the Dropbox or Google
Drive API would be handled by `rclone` under the hood.

Security
++++++++

The mounted storage gives you access to all contents inside the mounted
subtree.  The mounted filesystem is sandboxed
(https://docs.pyfilesystem.org/en/latest/concepts.html#sandboxing). So you can
not escape and access content outside the mounted storage.

Available drivers
+++++++++++++++++

Connectivity with other backend is accomplished through dedicated driverse that implementation
the API layer between PyFilesystem 2 and the related backend. 
See https://www.pyfilesystem.org/page/index-of-filesystems/ for all available drivers.

License
-------
This package is published under the GNU Public License V2 (GPL 2)

Source code
-----------
See https://bitbucket.org/onkopedia/xmldirector.connector

Bugtracker
----------
See https://bitbucket.org/onkopedia/xmldirector.connector


Author
------
| Andreas Jung/ZOPYX
| Hundskapfklinge 33
| D-72074 Tuebingen, Germany
| info@zopyx.com
| www.zopyx.com
