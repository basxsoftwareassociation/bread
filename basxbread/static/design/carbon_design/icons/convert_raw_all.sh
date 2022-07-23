#!/bin/bash

find raw_32 -name '*.svg' -exec ./convert_raw.sh {} \;

# some extra changes to fix appeareance
cp flat/raw_32/information--square--filled.svg tmp
cat tmp | head -n -1 > flat/raw_32/information--square--filled.svg

# some extra changes to fix appeareance
cp flat/raw_32/warning--alt--filled.svg tmp
cat tmp | head -n -1 > flat/raw_32/information--square--filled.svg

rm tmp
