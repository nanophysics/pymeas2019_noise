# evaluate flicker noise
f_low = 0.1
f_high = 10.0

import math

P_sum = 0.0
n = 0
with open('result_presentation.txt','r') as inf:
    PS = eval(inf.read())['presentations']['PS']
for f, p in zip(PS['x'], PS['y']):
    if f > f_low:
        P_sum += p
        n += 1
        if f > f_high - 1e-3:
            break
assert(n == 24) # we assume there are no missing values
flicker_noise_Vrms = math.sqrt(P_sum)
print( f'Flickernoise: 0.1 Hz to 10 Hz is {flicker_noise_Vrms:0.3E} Vrms' )
