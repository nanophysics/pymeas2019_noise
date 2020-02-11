import library_plot
import library_topic
import config_measurement

def run():
  plotData = library_topic.PlotDataMultipleDirectories(__file__)

  library_plot.do_plot(plotData, title=config_measurement.TITLE, do_animate=True, write_files=())

if __name__ == '__main__':
  run()
