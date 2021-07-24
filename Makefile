pip:
	rm -rf dist/
	python3 setup.py build sdist
	twine upload dist/*

locale:
	./manage.py makemessages -l de -l th -l nb_NO -l fr -l pt

checks:
	black --check bread
	flake8 bread

css:
	sassc -I bread/static/design/carbon_design/scss/globals/scss/vendor/ bread/static/design/carbon_design/scss/styles.scss > bread/static/css/bread-main.css
	sassc -s compressed -I bread/static/design/carbon_design/scss/globals/scss/vendor/ bread/static/design/carbon_design/scss/styles.scss > bread/static/css/bread-main.min.css

js:
	uglifyjs bread/static/js/* bread/static/design/carbon_design/js/carbon-components.js > bread/static/js/bread.min.js

watch_css:
	find bread/static/design/carbon_design/scss -name '*.scss' | entr sassc -I bread/static/design/carbon_design/scss/globals/scss/vendor/ bread/static/design/carbon_design/scss/styles.scss > bread/static/css/bread-main.css

