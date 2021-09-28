.PHONY: clean
.DEFAULT_GOAL := test

clean:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

test:
	pytest

coverage:
	coverage run --source takehome -m pytest
	coverage report -m
	coverage html
	open htmlcov/index.html

release: dist
	twine upload dist/*

dist: clean
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist

install: clean
	python setup.py install
