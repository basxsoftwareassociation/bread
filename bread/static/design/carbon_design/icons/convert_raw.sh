#!/bin/bash

mkdir -p flat/$(dirname $1)
xpath -e '//svg/*[not(self::defs) and not(self::style) and not(self::rect and @class="st0")]' $1 > flat/$1
