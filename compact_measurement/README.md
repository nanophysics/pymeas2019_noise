# Gesamtkontrolle

`run_measurements` ruft subjobs `measure` und `plot` auf.

Wird ein subjob mit <ctrl-C> abgebrochen, so soll auch `run_measurements` abgebrochen werden.

# compact_measurement\run_measurements.py

Hier wird die Ausmessung und Auswertung gestarted.

```python
CONTEXT = MeasurementContext(
    topdir=library_path.TOPDIR,
    compact_serial="20000101_01",  # Hier den zu testenden Compact_2012 eintragen
    measurement_date="20210310a",  # Hier die zu bearbeitende Messung eintragen
    speed=Speed.DETAILED,          # Für Testzwecke wird mit SMOKE oder BLIP die Testzeit massiv verkürzt
    mocked_picoscope=False,        # Für Testzwecke können einzelne Geräte gemockt (überspruchen) werden
    mocked_scanner=False,          # Für Testzwecke können einzelne Geräte gemockt (überspruchen) werden
    mocked_compact=False,          # Für Testzwecke können einzelne Geräte gemockt (überspruchen) werden
    mocked_voltmeter=False,        # Für Testzwecke können einzelne Geräte gemockt (überspruchen) werden
)
```

## Stati

Die Messung und Auswertung dauert Tage bis Wochen.
Darum wird der Ablauf in verschiedene Schritte unterteilt, die einzeln gestartet und bei Bedarf zurückgesetzt werden können.

Die Arbeitschritte sind:

* Direktorystruktur bereitstellen
* Ausmessung Compact
  * Benötigt Compact, Picoscope und Scanner
  * Dieser Arbeitschritt dauert sehr lange
  * Stati: HV_OUT_DIR_+100V\stati_blue-CH13_voltage.txt
  * Stati: HV_OUT_DIR_+100V\raw-blue-CH13\stati_noise_done.txt
  * Stati: HV_OUT_DIR_+100V\stati_noise_done.txt
* Diagramme erstellen
  * Stati: HV_OUT_DIR_+100V\raw-grey-BASENOISE\stati_plot.txt
  * Stati: HV_OUT_DIR_+100V\stati_plot.txt
* Qualifikation Compact - Beurteilung, ob die Hardware in Ordnung ist.

## FAQ: Einzelne Arbeitsschritte wiederholen

* Die entsprechenden `stati_xx.txt` Files löschen.
* `run_measurements.py` nochmals starten.
* Im von `run_measurements.py` ist ersichtlich, was übersprungen oder bearbeitet wird.

## FAQ: Qualification Compact

* `run_measurments.py` starten.
* Dadurch wird `compact_measurements\20000101_01-20210310a\result_qualification.csv` erstellt.
* Nur einmalig: Excel `pymeas_qualification_template.xlsm` neben `result_qualification.csv` kopieren.
* Daten in Excel neu laden und verifizieren.
* Falls Nachbesserungen nötig:
  * `library_qualification.py` editieren.
  * wieder oben beginnen (`run_measurments.py` starten)
