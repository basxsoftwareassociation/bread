#!/bin/bash

mkdir -p flat/$(dirname $1)
xpath -e '//svg/*[not(self::defs) and not(self::style)]' $1 > flat/$1
