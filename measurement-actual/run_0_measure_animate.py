import time
import library_plot
import run_2_plot_composite

def run():
  plotData = library_plot.PlotData(__file__)

  library_plot.do_plot(plotData, title=run_2_plot_composite.TITLE, do_animate=True)

if __name__ == '__main__':
  run()
