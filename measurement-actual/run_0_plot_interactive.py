import matplotlib.pyplot as plt

import library_topic
import library_plot
import library_gui


def run():
    plotData = library_topic.PlotDataMultipleDirectories(__file__)
    presentation_tag = "LSD"

    fig, ax = plt.subplots(figsize=(8, 4))
    plot_context = library_plot.PlotConext(plotData=plotData, fig=fig, ax=ax)
    plot_context.update_presentation(library_topic.PRESENTATIONS.get(presentation_tag), update=False)

    app = library_gui.MyApp(plot_context)

    app.MainLoop()


if __name__ == "__main__":
    run()
