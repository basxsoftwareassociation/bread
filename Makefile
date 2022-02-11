pip:
	rm -rf dist/
	python3 setup.py build sdist
	twine upload dist/*

locale:
	./manage.py makemessages -l de -l th -l nb_NO -l fr -l pt -l en

checks:
	black --check bread
	flake8 bread

css:
	pysassc -I bread/static/design/carbon_design/scss/globals/scss/vendor/ bread/static/design/carbon_design/scss/styles.scss > bread/static/css/bread-main.css
	pysassc -t compressed -I bread/static/design/carbon_design/scss/globals/scss/vendor/ bread/static/design/carbon_design/scss/styles.scss > bread/static/css/bread-main.min.css

js: bread/static/js/bread.min.js

bread/static/js/bread.min.js: bread/static/js/htmx.js bread/static/js/bliss.js bread/static/js/main.js bread/static/design/carbon_design/js/carbon-components.js
	uglifyjs $^ > $@

download_js_libraries:
	curl -L https://unpkg.com/htmx.org/dist/htmx.js -o bread/static/js/htmx.js
	curl -L https://blissfuljs.com/bliss.js -o bread/static/js/bliss.js

watch_css:
	find bread/static/design/carbon_design/scss -name '*.scss' | entr -n pysassc -I bread/static/design/carbon_design/scss/globals/scss/vendor/ bread/static/design/carbon_design/scss/styles.scss > bread/static/css/bread-main.css

raise_and_release_minor_version:
	git push
	NEWVERSION=$$(                              \
	   echo -n '__version__ = ' &&              \
	   cat bread/__init__.py |            \
	   cut -d = -f 2 |                          \
	   python3 -c 'i = input().strip().strip("\""); print("\"" + ".".join(i.split(".")[:-1] + [str(int(i.split(".")[-1]) + 1) + "\""]))' \
    ) &&                                        \
	echo $$NEWVERSION > bread/__init__.py
	git commit -m 'bump version' bread/__init__.py && git push && git push --tags
