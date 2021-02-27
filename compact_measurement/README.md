Direktorystruktur

20201111_03-DAdirect-10V/DA01
20201111_03-DAdirect-10V/DA02

20201111_03-DAdirect+10V/DA01
20201111_03-DAdirect+10V/DA02

20201111_03-DAdirect+0V/DA01
20201111_03-DAdirect+0V/DA02

20201111_03-OUT-10V/DA01
20201111_03-OUT-10V/DA02

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

