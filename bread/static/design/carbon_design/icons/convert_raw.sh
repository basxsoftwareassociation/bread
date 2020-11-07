#!/bin/bash

mkdir -p flat/$(dirname $1)
xpath -e '//svg/*[not(self::defs)' $1 > flat/$1
