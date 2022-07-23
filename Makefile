pip:
	rm -rf dist/
	python3 setup.py build sdist
	twine upload dist/*

locale:
	./manage.py makemessages -l de -l th -l nb_NO -l fr -l pt -l en

checks:
	black --check basxbread
	flake8 basxbread

css:
	pysassc -I basxbread/static/design/carbon_design/scss/globals/scss/vendor/ basxbread/static/design/carbon_design/scss/styles.scss > basxbread/static/css/basxbread-main.css
	pysassc -t compressed -I basxbread/static/design/carbon_design/scss/globals/scss/vendor/ basxbread/static/design/carbon_design/scss/styles.scss > basxbread/static/css/basxbread-main.min.css

js: basxbread/static/js/basxbread.min.js

basxbread/static/js/basxbread.min.js: basxbread/static/js/htmx.js basxbread/static/js/bliss.js basxbread/static/js/main.js basxbread/static/design/carbon_design/js/carbon-components.js
	uglifyjs $^ > $@

download_js_libraries:
	curl -L https://unpkg.com/htmx.org/dist/htmx.js -o basxbread/static/js/htmx.js
	curl -L https://blissfuljs.com/bliss.js -o basxbread/static/js/bliss.js

watch_css:
	find basxbread/static/design/carbon_design/scss -name '*.scss' | entr -n pysassc -I basxbread/static/design/carbon_design/scss/globals/scss/vendor/ basxbread/static/design/carbon_design/scss/styles.scss > basxbread/static/css/basxbread-main.css

raise_and_release_minor_version:
	git push
	NEWVERSION=$$(                              \
	   echo -n '__version__ = ' &&              \
	   cat basxbread/__init__.py |            \
	   cut -d = -f 2 |                          \
	   python3 -c 'i = input().strip().strip("\""); print("\"" + ".".join(i.split(".")[:-1] + [str(int(i.split(".")[-1]) + 1) + "\""]))' \
    ) &&                                        \
	echo $$NEWVERSION > basxbread/__init__.py
	git commit -m 'bump version' basxbread/__init__.py && git push && git push --tags
