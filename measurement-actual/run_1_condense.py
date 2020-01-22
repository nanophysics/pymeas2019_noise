import library_path
dir_measurement = library_path.find_append_path()

def run():
  import program
  program.run_plot(dir_measurement)

  import run_2_plot_composite
  run_2_plot_composite.run()

if __name__ == '__main__':
  run()