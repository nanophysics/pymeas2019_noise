# Qt GUI Porting Task

The existing wxPython GUI should be ported to PySide6. Once complete, the wxPython GUI code will be removed.

## Existing wxPython GUI

Currently a GUI in wxPython 4.2.5:
- `run_0_gui_wxwidgets.py`  — Old GUI entry point
- `library_gui.py` — Main GUI class (`MyApp`, `PlotPanel`) with ~400 lines
- `library_gui.wxg` — XRC layout file (binary format)
- `library_gui.xrc` — XML layout definition
- `matplotlib` integration using `FigureCanvasWxAgg` and `NavigationToolbar2WxAgg`
- Reference screenshots: `src/pymeas2019_noise/wxwidgets-screenshots/`

### GUI Features to Port

Based on `library_gui.py`, the GUI includes:

**Core UI Components:**
- Matplotlib figure with animation (live plot updating every 1000ms)
- Matplotlib toolbar (zoom, pan, save)

**Control Buttons:**
- `run_0_guis.py`  — New GUI entry point
- `button_measurement_start` — Start measurement
- `button_measurement_stop` — Stop measurement
- `button_measurement_skip_settle` — Skip settle phase
- `button_display_open_directory` — Open results directory
- `button_display_clone` — Open display clone window

**Selection Controls:**
- `combo_box_presentation` — Select presentation (from presentations list)
- `combo_box_measurement_color` — Choose color for measurement
- `combo_box_display_topic` — Select topic to display
- `combo_box_display_stage` — Select stage within topic
- `button_display_reload_topic` — Refresh topic list
- `button_display_reload_stage` — Refresh stage list

**Display Elements:**
- `text_ctrl_measurement_topic` — Input field for measurement topic (prefilled with datetime)
- `label_status_text` — Status text (bold font, updated by timer every 2000ms)
- `label_coordinates` — Mouse cursor coordinates when hovering over plot

**Behavior:**
- Timer-based updates every 2000ms to refresh measurement status
- Measurement start/stop buttons enable/disable based on running state
- Combo box event handlers trigger plot updates
- Mouse motion over plot updates coordinate display

## Target: PySide6 GUI

Port to PySide6 with async support:
- `PySide6>=6.10.0`
- `PySide6-stubs>=6.7.3.0`
- `qasync>=0.27.1` (for async/await support with Qt event loop)

## Project Structure (New Qt GUI)

```
src/pymeas2019_noise/qt/
├── __init__.py
├── agent.md                          (this file)
├── qt_main.py                        (Main entry point and MyApp class - currently empty)
├── widgets_plot.py                 (PlotPanel equivalent)
├── widget_main.py                (Main window setup and layout)
```

## Matplotlib Migration Plan

The `FigureCanvasWxAgg` needs to be migrated to PySide6:

Use `matplotlib.backends.backend_qt5agg.FigureCanvasQTAgg`
   - Direct PySide6 equivalent
   - Use `NavigationToolbar2QT` instead of `NavigationToolbar2WxAgg`
   - Minimal code changes


## Implementation Guidelines

### Constraint: Do Not Touch Existing Code

- **Keep** `library_gui.py`, `library_gui.wxg`, `library_gui.xrc` **unchanged**
- All new Qt code goes into `src/pymeas2019_noise/qt/`
- No modifications - or just the really required - to existing project code during porting
- The wxPython GUI remains functional and unchanged until Qt port is complete

### Development Approach

1. Develop Qt GUI in parallel with wxPython (both will coexist initially)
2. Keep the application entry point flexible so either GUI can be selected
3. Once Qt GUI is feature-complete and tested, wxPython code can be removed in a separate task

### Code Style

- Follow existing project conventions (see `pyproject.toml` for ruff/mypy/pylint config)
- Use type hints (required by mypy)
- Maintain logging with `logging.getLogger()`
- Use `qasync` for any async operations (keep in sync with existing architecture)

## Feature Checklist

- [ ] **Plot Panel**
  - [ ] Matplotlib figure embedded in PySide6 window
  - [ ] NavigationToolbar2QT integrated
  - [ ] FuncAnimation running (updates every 1000ms)
  - [ ] Mouse motion coordinate tracking

- [ ] **Buttons**
  - [ ] Start measurement
  - [ ] Stop measurement
  - [ ] Skip settle
  - [ ] Open directory
  - [ ] Display clone
  - [ ] Reload topic
  - [ ] Reload stage

- [ ] **Combo Boxes & Selection**
  - [ ] Presentation selector (populates from presentations list)
  - [ ] Topic selector (populates dynamically)
  - [ ] Stage selector (populates based on topic)
  - [ ] Color picker

- [ ] **Input/Display**
  - [ ] Measurement topic text input (prefilled with datetime)
  - [ ] Status label (updates via timer every 2000ms)
  - [ ] Coordinate display (updates on mouse motion)

- [ ] **Event Handling & Logic**
  - [ ] Timer-based status updates (2000ms interval)
  - [ ] Button enable/disable based on measurement state
  - [ ] Combo box change handlers trigger updates
  - [ ] File lock checks (`library_filelock.FilelockGui()`)

- [ ] **Testing**
  - [ ] GUI opens without errors
  - [ ] Plot animates
  - [ ] Buttons trigger expected functions
  - [ ] Selectors populate correctly
  - [ ] Status updates in real time

## Definition of Done

Qt GUI is complete when:

1. ✓ All UI components match wxPython version feature-for-feature
2. ✓ All event handlers are wired correctly (buttons, combos, timers)
3. ✓ Matplotlib plot animates smoothly with updates every 1000ms
4. ✓ Status label updates every 2000ms
5. ✓ Mouse coordinates display when hovering over plot
6. ✓ No errors from ruff, mypy, pylint
7. ✓ GUI can be launched and used without crashing
8. ✓ Code is documented with docstrings where appropriate
9. ✓ Type hints are complete
10. ✓ Tested against actual measurement flow (not just visual inspection)

After completion, a separate task will remove the wxPython code (`library_gui.py`, `library_gui.wxg`, `library_gui.xrc`).

## References

- wxPython GUI source: [library_gui.py](../../library_gui.py)
- Qt GUI location: [qt/qt_main.py](qt_main.py)
- PySide6 documentation: https://doc.qt.io/qtforpython/
- matplotlib PySide6 backend: https://matplotlib.org/stable/backends/backend_qt5agg.html

