; vim: set filetype=csound:

sr	=	44100
kr	=	44100
ksmps	=	1
nchnls	=	2


instr 1

	idur		init		p3
	ivol		init		p4
	ipitch		init		p5
	ipan		init		p6

	aenv		linseg		0, .01, 1, idur - .01, 0
	asig 		oscil		ivol * aenv, ipitch, 1
	aleft		=		asig * ipan
	aright		=		asig * (1 - ipan)

			out		aleft, aright

endin
