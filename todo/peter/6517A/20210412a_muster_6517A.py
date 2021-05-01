import visa
import time

rm = visa.ResourceManager()

instrument = rm.open_resource('GPIB0::27::INSTR')
instrument.timeout = 50000
print(instrument.write("*RST"))
print(instrument.write("*CLS"))
print(instrument.write("func 'curr:dc'"))

fvoltage = 10.0
# widerstand 100G

print(instrument.write("SOUR:VOLT:RANG 100")) # 100 or 1000
print(instrument.write("SOUR:VOLT %f" % fvoltage))
print(instrument.write("SOUR:VOLT:MCON ON"))
print(instrument.write("RES:MAN:VSO:OPER ON"))
print(instrument.write("CURR:DAMP OFF"))
print(instrument.write("curr:dc:rang 2E-9")) # 20E-12 200E-12 2E-9 20E-9 200E-9 2E-6 20E-6 200E-6 2E-3 20E-3
print(instrument.write("SYST:ZCH OFF"))
print(instrument.write("INIT:CONT ON"))
print(instrument.write("FORM:ELEM READ"))
print(instrument.write("CURR:NPLC 10")) # 0.01 to 10

time.sleep(3.0)
print(instrument.write("TRIG:SOUR IMM"))
print(instrument.write("TRIG:DEL 0"))

print("espected @ 100GOhm: ", fvoltage/100E9, " A")
time.sleep(1.0)
print(instrument.query("READ?"))


print(instrument.query("TRAC:POIN:ACT?"))
print(instrument.write("TRAC:CLE"))
print(instrument.query("TRAC:POIN:ACT?"))

print("nochmals")
print(instrument.write("TRAC:POIN 5"))
print(instrument.write("TRAC:CLE"))
print(instrument.write("INIT:CONT ON"))
time.sleep(0.1)

for i in range(3):
    print(instrument.write("TRAC:FEED:CONT NEXT"))
    stringvalues = instrument.query("TRAC:DATA?")
    stringlist = stringvalues.split(",")
    valuesA = [float(i) for i in stringlist]
    print(len(valuesA))

print("fertig")









##print(instrument.write("TRAC:POIN 50"))
#print(instrument.write("TRAC:FEED:CONT NEXT"))

#trig_count = 50
#assert (trig_count <= maxmemory)
#print(instrument.write("TRIG:COUN %d" % trig_count))

while False:
    print(instrument.write("TRIG:SOUR IMM"))
    time.sleep(1.0)
    answer = instrument.query("trac:data?")
    answer = answer.replace("NADC", "")
    listanswer = answer.split(",")
    values_A = [float(i) for i in listanswer[0::3]]     
    print(values_A)




exit()

str = instrument.query("READ?")  #.replace(",", "\n")
#strs = str.split(",")
#floats = [float(i) for i in strs]
print(str)


exit()


# print(instrument.write("CONF:VOLT:DC")) # auto range
print(instrument.write("CONF:VOLT:DC 100")) # 0.1, 1, 10, 100, 1000
time.sleep(1.0)
print(instrument.write("TRIG:DEL 0")) # Trigget delay
maxmemory = 512
trig_count = 50
#assert (trig_count <= maxmemory)
print(instrument.write("TRIG:COUN %d" % trig_count))  # :COUNt {<value>|MINimum|MAXimum|INFinite}  samples pro lesen
print(instrument.write("SAMP:COUN 1")) # anzahl samples pro lesen  ???
# produkt aus TRIG:COUN x TRIG:COUN  darf nicht groesser als 512 sein. Anleitung fuer mich sehr unklar.
print(instrument.write("ZERO:AUTO OFF")) # ZERO:AUTO {OFF|ONCE|ON}
print(instrument.write("INP:IMP:AUTO ON"))
NPLC = '1' #NPLC: Integration over powerlinecycles, 0.02 0.2 1 10 100
#NPLC = '0.2' #NPLC: Integration over powerlinecycles, 0.02 0.2 1 10 100
print(instrument.write("VOLT:DC:NPLC " + NPLC)) # NPLC: Integration over powerlinecycles, 0.02 0.2 1 10 100

time.sleep(1.0)

#print(instrument.write("TRIG:SOUR IMM"))
time.sleep(1.0)
#print(instrument.write("INIT"))

#time.sleep(0.5)
print(instrument.write("TRIG:SOUR IMM"))
#time.sleep(0.5)
#print(instrument.write("INIT"))


messzeit_s = 10.0
powerline_cycle_s = 0.02 * float(NPLC)
overheadfaktor = 1.0 # 1.14
messpunktzeit_s = overheadfaktor * powerline_cycle_s
i_scans = int( messzeit_s / (trig_count * powerline_cycle_s * overheadfaktor))

print ("Anzahl Scans: %d" % i_scans)
starttime = time.time()
for i in range(i_scans):
    # print ( instrument.query("DATA:POINts?") )
    #string = instrument.query("FETC?")
    #print (string)
    #print('Messung {:d}  Spannung {:.10f} V'.format(i, float(string))) # punkte
    str = instrument.query("READ?")  #.replace(",", "\n")
    strs = str.split(",")
    floats = [float(i) for i in strs]
    # f.write( instrument.query("READ?").replace(",", "\n"))
    print(str)
    print ( "Time s %.3f, espected s %.3f" % ((time.time() - starttime), ((i + 1) * trig_count * messpunktzeit_s)))
instrument.close() # visa treiber wieder schliessen

#f.close()
