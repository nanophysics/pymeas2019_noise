# Design

## Stream-Interface

- init(stage: int, dt_s: float)
- push(array)
- flush()

### These classes are Stream-Sinks and implement the Stream-Interface

- class Density (in and out)
- class FIR
- class OutTrash

### These classes are Stream-Sources - they drive a Stream-Interface

- class InThread
- class InSynthetic
- class InFile

### Example pipelines

- InSynthetic -> FIR -> Density -> FIR -> Density -> OutTrash
- Picosope -> InThread -> FIR -> Density -> FIR -> Density -> OutTrash

## Animated Plots

### Two processes

- The measuring process writes files in `measurement_actual\raw-blue-measurement1`.
- The gui process detects changes of the modification dates of the files. This triggers the display to redraw.

### Redraw triggering

These events may occur

- A directory `measurement_actual\raw-blue-measurement1` appears or dissapears.
  - Implemented in `PlotDataMultipleDirectories.directories_changed()`

- A file `measurement_actual\raw-blue-measurement1\densitystep_*.pickle` dissappears.
    This is not detected

- The modification date of a file `measurement_actual\raw-blue-measurement1\densitystep_*.pickle` changes.
- A file `measurement_actual\raw-blue-measurement1\densitystep_*.pickle` appears.
  - Implemented in `program.py reload_if_changed()`
  - Implemented in `DensityPlot.file_changed()`

  This then will write `result_summary.pickle`


Topics not used in the implementation:
  - Only one directory may be measured at the time. So for all remaining directories, it is not required to look for file-timestamps - however, there is not way to find out which direcotry is processing now.
  - Option to enhance: In `tmp_filelock_lock.txt` we could write the directory name of the actual measurement: So we only have to poll for timestamps in that directory.


## SQLite versus filesystem

Every topic has it's own sqlite database with all `densitystep_3_slow_06_SKIP.pickle` files.
The structure would be

- raw-blue-measurement1
  - densitystep.sqlite
  - result_summary.pickle
- raw-blue-measurement2
  - densitystep.sqlite
  - result_summary.pickle

Pro:
- Fast search for changes in sqlite.
- Blocking write/read in sqlite.
- No parsing of the filename requried: `densitystep_3_slow_01_SKIP.pickle`: <stepname> <stage> <SKIP>

Con:
- Refactoring required
- Renaming of directories on the file is not possible anymore as the open sqllite-databases will lock the directory.

Option:
- All `result_summary.pickle` will be stored in a memory-base sqlite db
