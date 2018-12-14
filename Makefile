build:
	sh bootstrap-py3.sh

release:
	mkrelease -p -d pypi

docs:
	cd docs; make html

upload-docs:
	python setup.py upload_docs --upload-dir docs/build/html

test:
	bin/test xmldirector
	bin/test-crex xmldirector

test-coverage:
	unbuffer bin/test --coverage=${PWD}/coverage xmldirector | tee coverage.txt

demo:
	bin/instance run src/xmldirector.demo/democontent/setup-plone.py local

demo-docker:
	bin/instance run src/xmldirector.demo/democontent/setup-plone.py docker
