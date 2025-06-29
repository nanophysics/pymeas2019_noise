set -eu

../venv/bin/python -m pymeas2019_noise.run_1_process_raw

# uv run --with=git+https://github.com/nanophysics/pymeas2019_noise.git -- python -m pymeas2019_noise.run_1_process_raw