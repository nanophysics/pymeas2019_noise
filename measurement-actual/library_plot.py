import pathlib
import matplotlib.pyplot as plt
import matplotlib.ticker
import matplotlib.animation

import library_topic

# TODO: Remove
PickleResultSummary = library_topic.PickleResultSummary

class Globals:
  def __init__(self):
    self.presentation = None
    self.plotData = None
    self.fig = None
    self.ax = None

  def set(self, plotData, fig, ax):
    # assert self.plotData is None
    # assert self.fig is None
    self.plotData = plotData
    self.fig = fig
    self.ax = ax

  def update_presentation(self, presentation=None, update=True):
    if presentation is not None:
      self.presentation = presentation
    if update:
      assert self.plotData is not None
      plt.ylabel(f'{self.presentation.tag}: {self.presentation.y_label}')
      for topic in self.plotData.listTopics:
        topic.recalculate_data(presentation=self.presentation)
      for ax in self.fig.get_axes():
        ax.relim()
        ax.autoscale()
        plt.xlabel('Frequency [Hz]')
        plt.grid(True, which="major", axis="both", linestyle="-", color='gray', linewidth=0.5)
        plt.grid(True, which="minor", axis="both", linestyle="-", color='silver', linewidth=0.1)
        ax.xaxis.set_major_locator(matplotlib.ticker.LogLocator(base=10.0, numticks=20))
        ax.yaxis.set_major_locator(matplotlib.ticker.LogLocator(base=10.0, numticks=20))
        # Uncomment to modify figure
        # self.fig.set_size_inches(13.0, 7.0)
        # ax.set_xlim(1e-2, 1e2)
        # ax.set_ylim(1e-10, 1e-1)
      self.fig.canvas.draw()

globals = Globals()

def do_plots(**args):
  '''
  Print all presentation (LSD, LS, PS, etc.)
  '''
  for tag in library_topic.PRESENTATIONS.tags:
    do_plot(presentation_tag=tag, **args)

def do_plot(plotData, title=None, do_show=False, do_animate=False, write_files=('png', 'svg'), write_files_directory=None, presentation_tag='LSD'):
  globals.update_presentation(library_topic.PRESENTATIONS.get(presentation_tag), update=False)

  if do_show or do_animate:
    import library_tk
    library_tk.initialize(plt)

  fig, ax = plt.subplots()
  globals.set(plotData, fig, ax)

  if title:
    plt.title(title)

  if do_show or do_animate:
    import library_tk
    library_tk.add_buttons( fig)

  def initialize_plot_lines():
    for topic in plotData.listTopics:
      x, y = globals.presentation.get_xy(topic)
      plot_line, = ax.loglog(
        x, y,
        linestyle='none',
        linewidth=0.1,
        marker='.',
        markersize=3, 
        color=topic.color,
        label=topic.topic
      )
      topic.set_plot_line(plot_line)

    leg = ax.legend(fancybox=True, framealpha=0.5)
    leg.get_frame().set_linewidth(0.0)

  initialize_plot_lines()

  globals.update_presentation()

  if write_files_directory is None:
    # The current directory
    write_files_directory = pathlib.Path(__file__).parent

  for ext in write_files:
    filename = write_files_directory.joinpath(f'result_{globals.presentation.tag}.{ext}')
    print(filename)
    fig.savefig(filename, dpi=300)

  if do_show or do_animate:
    if do_animate:
      import library_tk

      def animate(i):
        if plotData.directories_changed():
          plotData.remove_lines_and_reload_data(fig, ax)
          initialize_plot_lines()
          #initialize_grid()
          return

        for topic in plotData.listTopics:
          topic.reload_if_changed(globals.presentation)

      _animation = library_tk.start_animation(plotData=plotData, fig=fig, func_animate=animate)
      # '_animation': This avoids the garbage collector to be called !?
    plt.show()

  fig.clf()
  plt.close(fig)
  plt.clf()
  plt.close()
