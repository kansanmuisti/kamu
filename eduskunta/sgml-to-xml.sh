#!/bin/sh

CATALOG_FILE="eduskunta.cat"
INPUT="$1"
OUTPUT="$2"

set -e

osx -xno-nl-in-tag -xpreserve-case -c eduskunta.cat "$INPUT" > "$OUTPUT"
tidy -q -utf8 -xml -m -i $OUTPUT
