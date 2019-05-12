measurements = (
  dict(f=1, t=7),
  dict(f=2, t=3.5),
)



defaults = dict(
skalierungsfaktor= 1.00E+03,
input_Vp=	0.1, #	input range, 10, 5, 2, 1, 0.5, 0.2, 0.1
input_set_Vp= 	10, #	set voltage input, out is adjusted automatically
)

channels = [
	dict(
                name = 'CH1 CMRR',
     input_Vp=	0.2,
            ),
	dict(
                name = 'CH12 CMRR',
     input_Vp=	0.2,
            ),
]
