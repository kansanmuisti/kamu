#!/bin/bash

TIMESTAMP_FORMAT="+%Y-%m-%d %H:%M:%S"
ROOT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

LOG_FILE="/tmp/kamu-import-$(date "+%Y-%m-%d").log"

if [ -f $ROOT_PATH/local_update_config ]; then
	. $ROOT_PATH/local_update_config
fi

echo --------------------------------- >> $LOG_FILE
echo "$(date "$TIMESTAMP_FORMAT") Starting import" >> $LOG_FILE
echo --------------------------------- >> $LOG_FILE

cd $ROOT_PATH

# Import new documents
python manage.py eduskunta --traceback --docs >> $LOG_FILE 2>&1
if [ $? -ne 0 ]; then
    cat $LOG_FILE
    exit 1
fi

# Import new minutes
python manage.py eduskunta --traceback --minutes >> $LOG_FILE 2>&1
if [ $? -ne 0 ]; then
    cat $LOG_FILE
    exit 1
fi

# Once a night, import MPs
if [ "$1" == "nightly" ]; then
    python manage.py eduskunta --traceback --members >> $LOG_FILE 2>&1
    if [ $? -ne 0 ]; then
        cat $LOG_FILE
        exit 1
    fi
fi

# Once a week, re-import all MPs
if [ "$1" == "weekly" ]; then
    python manage.py eduskunta --traceback --members --replace >> $LOG_FILE 2>&1
    if [ $? -ne 0 ]; then
        cat $LOG_FILE
        exit 1
    fi
fi

if [ ! -z "$VARNISH_BAN_URL" ]; then
    varnishadm ban req.url \~ "$VARNISH_BAN_URL" >> $LOG_FILE 2>&1
    if [ $? -ne 0 ]; then
        cat $LOG_FILE
        exit 1
    fi
fi


echo "Import completed successfully." >> $LOG_FILE
