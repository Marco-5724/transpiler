#!/bin/dash

hour=$(date +"%H")
case "$hour" in
    0[6-9]|1[0-1]) echo "Good Morning" ;;
    1[2-7]) echo "Good Afternoon" ;;
    *) echo "Good Evening" ;;
esac
