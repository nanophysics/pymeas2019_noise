import library_plot

TITLE = 'Preamplifier Noise 2020: Measure Noise Density'

def run():
  plotData = library_plot.PlotData(__file__)
  

  # library_plot.do_plot(plotData=plotData, title=TITLE, do_show=False, write_files=('png',), presentation_tag='PSD')
  # library_plot.do_plot(plotData=plotData, title=TITLE, do_show=False, write_files=('png',), presentation_tag='PSD')
  # library_plot.do_plot(plotData=plotData, title=TITLE, do_show=False, write_files=(), presentation_tag='PS')
  # library_plot.do_plot(plotData=plotData, title=TITLE, do_show=False, write_files=(), presentation_tag='LS')
  # library_plot.do_plot(plotData=plotData, title=TITLE, do_show=False, write_files=(), presentation_tag='INTEGRAL')
  # library_plot.do_plot(plotData=plotData, title=TITLE, do_show=False, write_files=(), presentation_tag='DECADE')
  library_plot.do_plot(plotData=plotData, title=TITLE, do_show=True, write_files=(), presentation_tag='LSD')
  # library_plot.do_plots(plotData=plotData, title=TITLE, do_show=False, write_files=('png', ))

if __name__ == '__main__':
  run()