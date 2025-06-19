import visa

rm = visa.ResourceManager()
interval_in_ms = 500
print(rm.list_resources())
i_average = 8
instrument = rm.open_resource('GPIB0::12::INSTR')
instrument.timeout = 5000
print(instrument.write("*RST"))
print(instrument.write("*CLS"))
print(instrument.write("CONF:VOLT:DC"))
print(instrument.write("INP:IMP:AUTO ON"))
print(instrument.write("VOLT:DC:NPLC 10")) # NPLC: Integration over powerlinecycles, 0.02 0.2 1 10 100
print(instrument.write("TRIG:SOUR IMM"))

voltage = 0.0
for i in range(i_average):
    string = instrument.query("READ?")
    voltage += float(string)
    print(f'Messung {i:d}  Spannung {float(string):.10f} V') # punkte
voltage = voltage / i_average
print(f'Der Mittelwert ist: {voltage:.10f} V\n')

rm.close() # wuerde den visa treiber wieder schliessen
