rem ..\venv\Scripts\python.exe run_0_measure.py
uv run --with=git+https://github.com/nanophysics/pymeas2019_noise.git -- python run_0_measure.py
echo ERRORLEVEL %ERRORLEVEL%
pause
