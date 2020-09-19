import fs from 'fs';
import convert from 'muban-convert-hbs';

const template = fs.readFileSync(process.argv[2], 'utf-8');
fs.writeFileSync(
    process.argv[2].split('.').slice(0, -1).join('.') + ".html",
    convert.default(template) + "\n\n{% comment %}\nOriginal handlebar template:\n\n" + template + "\n{% endcomment %}", 'utf-8'
);
