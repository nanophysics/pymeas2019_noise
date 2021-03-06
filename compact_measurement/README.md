# Gesamtkontrolle

`run_measurements` ruft subjobs `measure` und `plot` auf.

Wird ein subjob mit <ctrl-C> abgebrochen, so soll auch `run_measurements` abgebrochen werden.

## Dependencies

### Structure
All filenames below will be build like `stati_<NAME>_done.txt`.

Timescale: downwords

measurements
  -
    measurement_DA01
    plot_DA01
  -
    measurement_DA02
    plot_DA02
  measurement_DA_DIRECT_10V
  plot_DA_DIRECT_10V

### Dependencies - depends-on
plot_DA01 depends-on measurement_DA01
plot_DA_DIRECT_10V depends-on measurement_DA_DIRECT_10V

==> if LEFT.timestamp < RIGHT.timestamp: process LEFT

### Dependencies - feeds
measurement_DA01 feeds measurement_DA_DIRECT_10V
plot_DA_DIRECT_10V feeds measurements

==> process LEFT: remove stati of RIGHT

## Directories

<compact_serial>-<messdatum>-<messung>-<voltage>/<channel>

compact_serial: 20201111_03
messdatum: 20201130a
messung: [DAdirect, DAout, HVdirect, HVout, supply, short]
voltage: DAdirect, DAout: [-10, 0, 10]
voltage: HVdirect, HVout: [-100, 0, 100]
voltage: supply: [-14, 14]
voltage: short: [0]

channel: [DA01, DA02, ... DA10]
channel: supply, short: [measurement]

## Status

Die Messung und Auswertung dauert Tage bis Wochen.
Darum wird der Ablauf in verschiedene Schritte unterteilt, die einzeln gestartet und bei Bedarf zurückgesetzt werden können.

Die Arbeitschritte sind:

* Direktorystruktur bereitstellen
* Ausmessung Compact
  * Benötigt Compact, Picoscope und Scanner
  * Dieser Arbeitschritt dauert sehr lange
  * SMOKE, DETAILED
* Qualifikation Compact - Beurteilung, ob die Hardware in Ordnung ist.
* Diagramme Compact

Anforderungen:

* Ein Arbeitschritt, der aufgrund eines Softwareabsturzes nicht beendet wurde, muss als solchen erkannt und neu durchgeführt werden.
* Ein korrekt abgeschlossener Arbeitschritt muss übersprungen werden.
* Mit einfachen Filemanipulationen kann der Status zurückgesetzt werden.

Implementation:

* SMOKE, DETAILED
  * DETAILED: Alle Arbeitschritte werden ausgeführt.
  * SMOKE: Die Messzeit wird verkürzt
    * indem nur jeder Messtyp einmal gemessen wird.
    * indem ungenauer gemessen wird


* Stati
  * Ein korrekt abgeschlossener Arbeitschritt hinterlässt ein File:
    * stati_20201111_03-20201130a_A_directorystructure_done.txt
    * 20201111_03-20201130a_DIRECT_-10V_DA/blue-DA03/stati_measurement_done.txt
    * stati_20201111_03-20201130a_B_qualification_done.txt
    * stati_20201111_03-20201130a_C_diagrams_done.txt

