import library_topic
import library_plot
import library_gui
import config_measurement

def run():
  plotData = library_topic.PlotDataMultipleDirectories(__file__)
  # library_plot.do_plot(plotData=plotData, title=config_measurement.TITLE, do_show=True, write_files=(), do_animate=True, presentation_tag='LSD')
  fig = library_plot.do_plot2(plotData=plotData, title=config_measurement.TITLE, do_show=True, write_files=(), do_animate=True, presentation_tag='LSD')
  plot_context = library_gui.PlotContext(figure=fig, do_animate=True)
  app = library_gui.MyApp(plot_context)

  library_plot.globals.initialize_plot_lines()
  library_plot.globals.update_presentation()

  app.MainLoop()

if __name__ == '__main__':
  run()