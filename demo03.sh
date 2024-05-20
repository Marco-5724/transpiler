#!/bin/dash

touch test_file.txt
ls -l test_file.txt

for course in COMP1511 COMP1521 COMP2511 COMP2521 
do                                               
    echo $course                                  
    mkdir $course                                 
    chmod 700 $course                            
done           

echo What is the airspeed velocity of an unladen swallow:
read velocity

echo Hello $name, my favourite colour is $colour too.

echo *
cd /tmp
echo *
cd ..
echo *