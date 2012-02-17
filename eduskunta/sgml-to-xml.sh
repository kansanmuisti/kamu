#!/bin/sh

CATALOG_FILE="eduskunta.cat"
INPUT="$1"
OUTPUT="$2"

MY_PATH="$(dirname "$0")"
CATALOG_FILE="$MY_PATH"/$CATALOG_FILE

set -e

osx -xno-nl-in-tag -xpreserve-case -c "$CATALOG_FILE" "$INPUT" > "$OUTPUT"
tidy -q -utf8 -xml -m -i $OUTPUT
