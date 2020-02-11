import library_plot
import config_measurement

def run():
  plotData = library_plot.PlotDataMultipleDirectories(__file__)
  library_plot.do_plots(plotData=plotData, title=config_measurement.TITLE, do_show=False, write_files=('png', ))

if __name__ == '__main__':
  run()