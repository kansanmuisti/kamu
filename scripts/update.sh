#!/bin/bash

TIMESTAMP_FORMAT="+%Y-%m-%d %H:%M:%S"
ROOT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

LOG_FILE="/tmp/kamu-import-$(date "+%Y-%m-%d-%H-%M").log"

if [ -f $ROOT_PATH/local_update_config ]; then
    $ROOT_PATH/local_update_config
fi

echo --------------------------------- >> $LOG_FILE
echo "$(date "$TIMESTAMP_FORMAT") Starting import" >> $LOG_FILE
echo --------------------------------- >> $LOG_FILE

cd $ROOT_PATH


if [ "$1" == "weekly" ]; then
    # Once a week, re-import all MPs
    python manage.py eduskunta --traceback --member --full --replace >> $LOG_FILE 2>&1
    if [ $? -ne 0 ]; then
        cat $LOG_FILE
        exit 1
    fi
elif [ "$1" == "nightly" ]; then
    # Once a night, re-import MPs
    python manage.py eduskunta --traceback --member --replace >> $LOG_FILE 2>&1
    if [ $? -ne 0 ]; then
        cat $LOG_FILE
        exit 1
    fi
else
    # Import new MPs
    python manage.py eduskunta --traceback --member >> $LOG_FILE 2>&1
    if [ $? -ne 0 ]; then
        cat $LOG_FILE
        exit 1
    fi

    # Import new documents
    python manage.py eduskunta --traceback --doc >> $LOG_FILE 2>&1
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

    # Import new votes
    python manage.py eduskunta --traceback --vote >> $LOG_FILE 2>&1
    if [ $? -ne 0 ]; then
        cat $LOG_FILE
        exit 1
    fi

    # Recalculate keyword activities
    python manage.py eduskunta --traceback --keyword-activity >> $LOG_FILE 2>&1
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
