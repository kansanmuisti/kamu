#!/bin/sh

set -e

URL_BASE="http://www.kansanmuisti.fi/storage"
DB_NAME="kamu.sql.bz2"
DB_URL="${URL_BASE}/$DB_NAME"
IMG_NAME="kamu-images.tar.bz2"
IMG_URL="${URL_BASE}/$IMG_NAME"

if [ ! -f $DB_NAME ]; then
	echo "Downloading database dump..."
	wget "${DB_URL}"
fi

echo "Installing initial database contents..."
bunzip2 -c $DB_NAME | python manage.py dbshell

if [ ! -f $IMG_NAME ]; then
	echo "Downloading images..."
	wget "${IMG_URL}"
fi
echo "Untarring images..."
tar xjf ${IMG_NAME}

echo "Remove $DB_NAME and $IMG_NAME yourself."
echo "All done! \o/"
