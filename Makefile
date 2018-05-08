.PHONY: test report clean build
WAL=resources/Astronomy.wal

default: build

test:
	coverage run --append --source=workbench -m unittest test.all

report:
	coverage report -m

clean:
	rm -rf build
	rm -rf dist
	rm -rf pytils.egg-info
	coverage erase

build:
#	python setup.py sdist
	python develop.py install

run:
#	python setup.py sdist
	python dev-server.py -v
