import library_plot

TITLE = 'Preamplifier Noise 2020: Measure Noise Density'

def run():
  plotData = library_plot.PlotData(__file__)
  library_plot.do_plot(plotData, title=TITLE, do_show=True, do_write_files=True)

if __name__ == '__main__':
  run()