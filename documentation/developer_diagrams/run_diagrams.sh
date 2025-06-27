#!/bin/sh

cd ../..

pyreverse --output=dot --project=FIR program_classify.py program_fir.py program_eseries.py
pyreverse --output=dot --project=pymeas2019_noise --ignore=database.py *.py measurement_actual/*.py

mv classes_* documentation/developer_diagrams
mv packages_* documentation/developer_diagrams
