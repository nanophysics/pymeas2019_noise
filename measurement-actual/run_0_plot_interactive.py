import pathlib

import matplotlib.pyplot as plt

import library_topic
import library_plot
import library_gui

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).absolute().parent

def run():
    plotData = library_topic.PlotDataMultipleDirectories(DIRECTORY_OF_THIS_FILE)

    fig, ax = plt.subplots(figsize=(8, 4))
    plot_context = library_plot.PlotConext(plotData=plotData, fig=fig, ax=ax)
    plot_context.update_presentation(library_topic.PRESENTATIONS.get(library_topic.DEFAULT_PRESENTATION), update=False)

    app = library_gui.MyApp(plot_context)
    app.MainLoop()


if __name__ == "__main__":
    run()
