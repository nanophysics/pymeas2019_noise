import sys
import matplotlib.backend_tools

import library_topic

matplotlib.use('TkAgg')

# Hide messages like:
#   Treat the new Tool classes introduced in v1.5 as experimental for now, the API will likely change in version 2.1 and perhaps the rcParam as well
import warnings
warnings.filterwarnings(action='ignore')

def initialize(plt):
  plt.rcParams['toolbar'] = 'toolmanager'

def add_buttons(fig):
  fig.canvas.manager.toolmanager.add_tool('List', ListTools)
  fig.canvas.manager.toolmanager.add_tool('Autozoom', UserAutozoom)
  fig.canvas.manager.toolbar.add_tool('Autozoom', 'navigation', 1)

  fig.canvas.manager.toolmanager.add_tool('Presentation', UserSelectPresentation)
  fig.canvas.manager.toolbar.add_tool('Presentation', 'navigation', 1)

  fig.canvas.manager.toolmanager.add_tool('Start', UserMeasurementStart)
  fig.canvas.manager.toolbar.add_tool('Start', 'navigation', 1)


def start_animation(plotData, fig, func_animate):

  def endless_iter():
    while True:
      yield 42

  animation = matplotlib.animation.FuncAnimation(fig,
    func=func_animate, 
    frames=endless_iter(),
    # Delay between frames in milliseconds
    interval=1000,
    # A function used to draw a clear frame. If not given, the results of drawing from the first item in the frames sequence will be used.
    init_func=None,
    repeat=False
  )

  return animation

class UserMeasurementStart(matplotlib.backend_tools.ToolBase):
  description = 'Measurement Start'

  def get_random_color(self):
    COLORS = (
      'blue',
      'orange',
      'black',
      'green',
      'red',
      'cyan',
      'magenta',
    )
    import random
    return random.choice(COLORS)

  def startDialog(self):
    import tkinter
    import tkinter.ttk

    self.directory_name = None
    dialog = tkinter.Tk()

    dialog.title("Start Measurement")
    dialog.minsize(400, 120)
    dialog.columnconfigure(0, weight=1)
    dialog.rowconfigure(0, weight=1)
    dialog.rowconfigure(1, weight=1)
    dialog.rowconfigure(2, weight=1)
    dialog.rowconfigure(3, weight=2)
    
    def clickStart():
      self.directory_name = f'{library_topic.DIRECTORY_NAME_RAW_PREFIX}{entryColor.get()}-{entryTopic.get()}'
      dialog.quit()

    label=tkinter.ttk.Label(dialog, text="Topic name of this measurement")
    label.grid(column=0, row=0, sticky=tkinter.EW)

    entryColor = tkinter.ttk.Entry(dialog, width=50)
    entryColor.grid(column=0, row=1, sticky=tkinter.EW)
    entryColor.insert(0, self.get_random_color())

    entryTopic = tkinter.ttk.Entry(dialog, width=50)
    entryTopic.grid(column=0, row=2, sticky=tkinter.EW)
    entryTopic.insert(0, library_topic.ResultAttributes.getdatetime())

    button = tkinter.ttk.Button(dialog, text="Start", command=clickStart)
    button.grid(column=0, row=3)

    dialog.mainloop()
    # Will return from 'mainloop()' when 'dialog.quit()' was called.
    dialog.destroy()

    return self.directory_name

  def trigger(self, *args, **kwargs):
    directory_name = self.startDialog()
    if directory_name is None:
      # The dialog has been closed
      return

    # The start button has been pressed
    import subprocess
    import run_0_measure
    subprocess.Popen(['cmd.exe', '/K', 'start', sys.executable, run_0_measure.__file__, directory_name])

class UserSelectPresentation(matplotlib.backend_tools.ToolBase):
  description = 'Select Presentation'

  def selectPresentationDialog(self):
    import tkinter
    import tkinter.ttk
    dialog = tkinter.Tk() 
    dialog.geometry('800x100')
    dialog.columnconfigure(0, weight=1)
    dialog.rowconfigure(0, weight=1)
    dialog.rowconfigure(1, weight=1)

    labelTop = tkinter.Label(dialog, text='Select a presentation')
    labelTop.grid(column=0, row=0, sticky=tkinter.EW)

    labels = [f'{p.tag}: {p.y_label}' for p in library_topic.PRESENTATIONS.list]
    # combobox = tkinter.Listbox(dialog, values=labels)
    combobox = tkinter.ttk.Combobox(dialog, values=labels)
    combobox.grid(column=0, row=1, sticky=tkinter.EW)
    combobox.current(0)

    self.selected_presentation = None

    def callbackFunc(event):
      self.selected_presentation = library_topic.PRESENTATIONS.list[combobox.current()]
      print(f'Selected:  {self.selected_presentation.tag}')
      dialog.quit()

    combobox.bind("<<ComboboxSelected>>", callbackFunc)

    dialog.mainloop()
    # Will return from 'mainloop()' when 'dialog.quit()' was called.
    dialog.destroy()
    return self.selected_presentation

  def trigger(self, *args, **kwargs):
    matplotlib.backend_tools.ToolBase.trigger(self, *args, **kwargs)
    presentation = self.selectPresentationDialog()
    if presentation == None:
      return
    import library_plot
    library_plot.globals.update_presentation(presentation=presentation)

class ListTools(matplotlib.backend_tools.ToolBase):
  '''List all the tools controlled by the `ToolManager`'''
  # keyboard shortcut
  default_keymap = 'm'
  description = 'List Tools'

  def trigger(self, *args, **kwargs):
    print('_' * 80)
    print(f"{'Name (id)':12} {'Tool description':45} {'Keymap'}")
    print('-' * 80)
    tools = self.toolmanager.tools
    for name in sorted(tools):
      if not tools[name].description:
          continue
      keys = ', '.join(sorted(self.toolmanager.get_tool_keymap(name)))
      print("{0:12} {1:45} {2}".format(
          name, tools[name].description, keys))
    print('_' * 80)
    print("Active Toggle tools")
    print("{0:12} {1:45}".format("Group", "Active"))
    print('-' * 80)
    for group, active in self.toolmanager.active_toggle.items():
      print("{0:12} {1:45}".format(str(group), str(active)))

class UserAutozoom(matplotlib.backend_tools.ToolBase):
  default_keymap = 'z'
  description = 'Auto Zoom'
  def trigger(self, *args, **kwargs):
    for ax in self.figure.get_axes():
      ax.relim()
      ax.autoscale()
    self.figure.canvas.draw()
    print('Did Autozoom')
