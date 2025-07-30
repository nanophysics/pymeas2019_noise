            # Memory leak:
            # See: https://github.com/pytorch/pytorch/issues/94893
            # Linux: scipy: 1.16.0

            # There is a memory leak on this line! How is this possible?
            # The memory leak occurs because assigning self._win = self._win
            # s_fac creates a new array and the old immutable array may still be referenced elsewhere, breaking the intended immutability and potentially causing memory issues; to fix this, update the array in-place using self._win *= s_fac.

=========================================
python -m pymeas2019_noise.run_measure_synthetic > leak_1_121_634_816.txt 2>&1

grep 'ModuleSpec ' leak.txt | wc -l
392

grep '<SourceFileLoader ' leak.txt | wc -l
385

grep '<function ' leak.txt | wc -l
15824

grep '<Signature ' leak.txt | wc -l
350

grep '<cell ' leak.txt | wc -l
3998

grep '<dict ' leak.txt | wc -l
5407


python -m pymeas2019_noise.run_measure_synthetic > leak_1_121_634_816.txt 2>&1


===============================================================

python -m memray run -m pymeas2019_noise.run_measure_synthetic

12_582_912?
--> memray-pymeas2019_noise.run_measure_synthetic.159767.bin

1_121_976_320
--> memray-pymeas2019_noise.run_measure_synthetic.165489.bin

memray flamegraph memray-pymeas2019_noise.run_measure_synthetic.165489.bin 


