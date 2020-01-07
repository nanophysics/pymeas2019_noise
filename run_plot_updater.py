import time
import program
import program_fir

if __name__ == '__main__':
  while True:
    try:
      program_fir.DensityPlot.directory_plot(program.DIRECTORY_0_RAW, program.DIRECTORY_1_CONDENSED)
    except Exception as e:
      print(e)
    time.sleep(2.0)

