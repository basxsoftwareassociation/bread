# This target can be used to regenerate the main css file
# This can be used for a development environment in order to prevent re-compiling the whole carbon-design scss on every request
#

compile_scss:
	rm -rf static/CACHE/css
	python manage.py collectstatic --noinput
	python manage.py compress --settings {{ project_name }}.settings.production
	touch {{ project_name }}/settings/local.py
	sed -i -e '/OVERRIDE_STYLESHEET/d' {{ project_name }}/settings/local.py
	for i in $$(\ls static/CACHE/css); do cat static/CACHE/css/$$i >> static/CACHE/css/precompiled.css ; done
	echo OVERRIDE_STYLESHEET = '"'/static/CACHE/css/precompiled.css'"' >> {{ project_name }}/settings/local.py
