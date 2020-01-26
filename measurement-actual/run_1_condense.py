import library_path
dir_measurement = library_path.find_append_path()

def reload_if_changed(dir_raw):
  import program
  return program.reload_if_changed(dir_raw=dir_raw)

def run():
  import program
  program.run_condense(dir_measurement)

  import run_2_plot_composite 
  run_2_plot_composite.run()

if __name__ == '__main__':
  run()