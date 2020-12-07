pip:
	rm -rf dist/
	python3 setup.py build sdist
	twine upload dist/*

locale:
	cd bread && ../manage.py makemessages -l de

checks:
	black --check bread
	flake8 bread
