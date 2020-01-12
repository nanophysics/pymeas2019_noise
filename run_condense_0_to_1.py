import program
import program_fir

if __name__ == '__main__':
  if False:
    import cProfile
    cProfile.run('program.run_condense_0to1()', sort='tottime')
    import sys
    sys.exit(0)
  program.run_condense_0to1()
  pass
  # program_fir.DensityPlot.directory_plot(program.DIRECTORY_0_RAW, program.DIRECTORY_1_CONDENSED)
  pass
