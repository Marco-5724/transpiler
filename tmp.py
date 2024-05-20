#!/usr/bin/env python3 -u
import glob
import os
import subprocess

subprocess.run(['touch', 'test_file.txt'])
subprocess.run(['ls', '-l', 'test_file.txt'])

for course in ['COMP1511', 'COMP1521', 'COMP2511', 'COMP2521']:
    print(f"{course}")
    subprocess.run(['mkdir', {course}])
    subprocess.run(['chmod', '700', {course}])

print(f"What is the airspeed velocity of an unladen swallow:")
velocity = input()

print(f"Hello $name, my favourite colour is $colour too.")

print(f"{' '.join(sorted(glob.glob('*')))}")
os.chdir('/tmp')
print(f"{' '.join(sorted(glob.glob('*')))}")
os.chdir('..')
print(f"{' '.join(sorted(glob.glob('*')))}")
