#!/bin/sh

# pyreverse --output=dot --project=pymeas2019_noise --ignore=database.py *.py measurement-actual/*.py
pyreverse --output=dot --project=pymeas2019_noise --ignore=database.py *.py measurement-actual/*.py

mv classes_* documentation_design
mv packages_* documentation_design
