#!/bin/sh

npm install carbon-components muban-convert-hbs

# patch muban-convert-hbs
cat <<EOF | patch -p1 node_modules/muban-convert-hbs/lib/Context.js
162a163,164
>     if(!currentScope)
>       return '???';
EOF
# our improved version of django transpiler
cp DjangoTranspiler.js node_modules/muban-convert-hbs/lib/

find node_modules/carbon-components/src/ -name '*.hbs' -exec node convert2html.js {} \; 2>&1 | grep -v ExperimentalWarning
# correct some of the transpilation and apply the carbon-icon tag correctly
find node_modules/carbon-components/src/ -name '*.html' -exec sed -i \
    -e 's/{{ root\.prefix }}/{{ prefix }}/g' \
    -e 's/{{ [a-zA-Z0-9_\.]*root,prefix }}/{{ prefix }}/g' \
    -e 's/{{ [a-zA-Z0-9_\.]*\.carbon-icon }}/{% carbon_icon "?" %}/g' \
    -e 's/{{ carbon-icon }}/{% carbon_icon "?" %}/g' \
    -e 's/{% include "/{% include "carbon_design\/components\//g' \
    -e 's/{{ prefix }}/bx/g' \
    -e '1 i {% load carbon_design_tags %}' \
    {} \;
find node_modules/carbon-components/src/ -name '*.html' -exec cp {} components/ \;

pydir=../../layout/carbon_design/components/
# generate some django stubs
for template_name in $(find components/ -name '*.html')
do
    filename=$(basename $template_name)
    django_template_name="carbon_design/"$template_name
    python_identifier=$( echo $filename | sed -e 's/\.html//g' -e 's/--/_/g' -e 's/-//g' )
    python_class=$( echo $filename | sed -e 's/\.html//g' -e 's/--/_/g' -e 's/-/_/g' | sed -E 's/_([a-z])/\U\1/g' | sed -E 's/^([a-z])/\U\1/g')
    python_module=$pydir$python_identifier".py"
    echo $filename $django_template_name $python_class $python_module
    cat <<EOF > $python_module
from crispy_forms.utils import TEMPLATE_PACK

from layout.carbon_design import Component


class $python_class(Component):
    template = "$django_template_name"

    def __init__(self, *fields, **kwargs):
        super().__init__(*fields, **kwargs)

    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK, **kwargs):
        return super().render(form, form_style, context, template_pack, **kwargs)
EOF

done

rm -rf node_modules 
