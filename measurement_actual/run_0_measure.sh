set -eu

../venv/bin/python -m pymeas2019_noise.run_0_measure

# uv run --with=git+https://github.com/nanophysics/pymeas2019_noise.git -- python -m pymeas2019_noise.run_0_measure