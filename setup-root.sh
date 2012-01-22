#!/bin/sh

set -e

DEB_DEPENDENCIES="virtualenvwrapper python-imaging python-lxml \
	python-mysqldb gettext python-numpy subversion git opensp"

echo "Installing main dependencies..."
apt-get install $DEB_DEPENDENCIES

echo "Installing extra packages..."
EXTRA_DEPENDENCIES="libnode-less"

for pkg in $EXTRA_DEPENDENCIES; do
	# Check if package is present
	if apt-cache show $pkg > /dev/null; then
        	apt-get install $pkg
        fi
done
