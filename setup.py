import os
from setuptools import setup, find_packages

version = '0.1.6'

setup(name='xmldirector.connector',
      version=version,
      description="xmldirector.connector supports mounting storages like S3, Webdav backend or local filesystem into Plone",
      long_description=open(os.path.join("docs", "source", "README.rst")).read() + "\n" +
      open(os.path.join("docs", "source", "HISTORY.rst")).read(),
      # Get more strings from
      # http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          "Programming Language :: Python",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3.6",
          "Programming Language :: Python :: 3.7",
          "Framework :: Plone",
          "Framework :: Plone :: 5.1",
          "Framework :: Plone :: 5.2",
          "Framework :: Zope2",
          "Topic :: Software Development :: Libraries :: Python Modules",
      ],
      keywords='XML Director exist-db basex owncloud alfresco existdb Plone XML Python WebDAV',
      author='Andreas Jung',
      author_email='info@zopyx.com',
      url='http://pypi.python.org/pypi/xmldirector.connector',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['xmldirector'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'zope.i18nmessageid',
          'plone.browserlayer',
          'furl',
          'fs>=2.1',
          'fs.webdavfs',
          'plone.app.testing',
          # -*- Extra requirements: -*-
      ],
      tests_require=['zope.testing'],
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
