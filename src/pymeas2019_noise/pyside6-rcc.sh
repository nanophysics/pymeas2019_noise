
uvx --from pyside6-essentials==6.11.1 pyside6-rcc resources/gui_resources.qrc -o resources_compiled/gui_resources_rc.py
uvx --from pyside6-essentials==6.11.1 pyside6-uic --from-imports resources/gui_main.ui -o resources_compiled/gui_main.py
