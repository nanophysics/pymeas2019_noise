import library_topic
import library_plot
import config_measurement

def run():
  plotData = library_topic.PlotDataMultipleDirectories(__file__)
  library_plot.do_plot(plotData=plotData, title=config_measurement.TITLE, do_show=True, write_files=(), presentation_tag='LSD')

if __name__ == '__main__':
  run()