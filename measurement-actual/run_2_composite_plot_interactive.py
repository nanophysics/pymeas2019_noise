import library_plot

TITLE = 'Preamplifier Noise 2020: Measure Noise Density'

def run():
  plotData = library_plot.PlotDataMultipleDirectories(__file__)
  library_plot.do_plot(plotData=plotData, title=TITLE, do_show=True, write_files=(), presentation_tag='LSD')

if __name__ == '__main__':
  run()