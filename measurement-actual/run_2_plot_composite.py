import library_plot

def run():
  TITLE = 'Preamplifier Noise 2020: Measure Noise Density'

  plotData = library_plot.PlotData(__file__)
  library_plot.do_plot(plotData, title=TITLE, do_show=True)

if __name__ == '__main__':
  run()