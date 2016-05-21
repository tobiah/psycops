#!/usr/bin/python

import pdb

from types import *
from copy import *
import re
import pdb
import wave


#***** CONSTANTS FOR 'JUST INTERVAL' CREATION *****

UNISON 		= 1.0 	/  1.0
MINOR_SECOND 	= 16.0 	/  15.0
HALF_STEP	= MINOR_SECOND
WHOLE_STEP 	= 9.0 	/  8.0
MINOR_THIRD 	= 6.0 	/  5.0
MAJOR_THIRD 	= 5.0 	/  4.0
PERFECT_FOURTH 	= 4.0 	/  3.0
TRITONE 	= 7.0 	/  5.0
PERFECT_FIFTH 	= 3.0 	/  2.0
MINOR_SIXTH 	= 8.0 	/  5.0
MAJOR_SIXTH 	= 5.0 	/  3.0
MINOR_SEVENTH 	= 9.0 	/  5.0
MAJOR_SEVENTH 	= 15.0 	/  8.0
OCTAVE 		= 2.0 	/  1.0

_HALF_STEP 	= 1 / HALF_STEP 
_WHOLE_STEP 	= 1 / WHOLE_STEP 
_MINOR_SECOND 	= 1 / MINOR_SECOND 
_MINOR_THIRD 	= 1 / MINOR_THIRD 
_MAJOR_THIRD 	= 1 / MAJOR_THIRD 
_PERFECT_FOURTH 	= 1 / PERFECT_FOURTH 
_TRITONE 	= 1 / TRITONE 
_PERFECT_FIFTH 	= 1 / PERFECT_FIFTH 
_MINOR_SIXTH 	= 1 / MINOR_SIXTH 
_MAJOR_SIXTH 	= 1 / MAJOR_SIXTH 
_MINOR_SEVENTH 	= 1 / MINOR_SEVENTH 
_MAJOR_SEVENTH 	= 1 / MAJOR_SEVENTH 
_OCTAVE 		= 1 / OCTAVE 

#***** EQUAL TEMPERED HALF-STEP MAKER *****
def half_step(number = 1):

	if number == 0:
		return 1

	factor = 2.0 ** (number / 12.0)

	return factor

class Playatts(dict):
	""" 
		This is meant to be a rather private class
		which is used to ensure that dicts that are
		sent as playatt args are initialized with the
		proper default values
	"""

	def __init__(self, playatts):
		self['start']		= 0
		self['warp']		= 1
		self['dwarp']		= 1
		self['amp']		= 1
		self['transpose']	= 1

		self.update(playatts)

		#dwarp defaults to warp if dwarp is not specified
		if not 'dwarp' in playatts.keys():
			self['dwarp'] = self['warp']

		self.type = 'playatts'



class Instrument():
	
	def __init__(self, orc, instrument, pnames = None):

		self.orc = orc
		self.instrument = instrument
		if pnames:
			self.pnames = ['i', instrument] + pnames
		else:
			self.pnames = self.make_pnames_from_orchestra()
		
		#self.make_pa_file()

	def make_pnames_from_orchestra(self):
		
		this_is_my_instrument = 0
		orc_file = open("%s.orc" % self.orc, 'r')
		for line in orc_file.readlines():

			#***** FLAG ENTRY INTO THIS INSTRUMENT DEF *****
			if line.find('instr') >= 0:
				line = re.sub(';.*', '', line)
				parts = line.split()
				if int(parts[1]) == self.instrument:
					this_is_my_instrument = 1
					continue

			#***** FIND AND PARSE passign LINE *****
			if this_is_my_instrument and line.find('passign') >= 0:
				fields = line.split('passign')[0]
				fields = fields.replace(',', ' ')
				fields = fields.split('i_')
				fields = ''.join(fields).split()
				return fields

	def make_pa_file():
		pa_name = "%s_%s.pa" % __file__.replace('.py', ''), str(self.instrument)
		pa = open(pa_name, 'w')
		line = "\t%s passign 3" % ', '.join(self.pnames)
		pa.write(line)
		pa.close()


	def __call__(self, info):

		info['type'] = 'i'
		info['inst'] = self.instrument

		pnames = ['type', 'inst', 'start'] + self.pnames
		e = Event(info, pnames)
		return e


class Event(list):
	"""
		Basic building block for any score event.
		Repesents one line in a Csound score.
	"""
	

	def __init__(self, pfields = [], pmap = {}):
		"""
			Handle string, array and dict init arg types.
			e.g.: e = Event("i1 0 3 10000 440") or
			      e = Event(['i', 0, 3, 10000, 440])
		"""
		self.pmap = pmap

		#***** DICT TO PFIELDS *****
		if(type(pfields) is DictType):
			holder = []
			for key in self.pmap:
				try:
					holder.append(pfields[key])
				except KeyError:
					holder.append(0.0)
			pfields = holder

		#***** STRING TO PFIELDS *****
		if(type(pfields) is StringType):
			pfields = pfields.split()
			## String pfield arg must handle "i1 0 3 10000 440" 
			## where p[0] and p[1] are combined ***
			parts = [pfields[0][0], int(pfields[0][1:])]
			pfields = parts + pfields[1:]

		self.append(str(pfields[0]))

		for p in pfields[1:]:
			try:
				v = float(p)
			except ValueError:
				v = '"%s"' % str(p)

			self.append(v)

		self.type = 'event'



	def __getitem__(self, what):
		if type(what) is IntType:
			return list.__getitem__(self, what)
		else:
			if what in self.pmap:
				return self[self.pmap[what]]
			else:
				raise PmapError("Item '%s' not found in event pmap")

	def copy(self, **playatts):
		"""
			Returns a new identical event, modified by 
			optional keyword args (warp, start, dwarp, amp, transpose)
		"""
		if type(playatts) is type({}):
			playatts = Playatts(playatts)

		temp = Event(self[:])

		if playatts:
			temp[2] *= playatts['warp']	
			temp[2] += playatts['start']	
			temp[3] *= playatts['dwarp']	#or, "duration warp"
			if len(temp) >= 5:
				temp[4] *= playatts['amp']		
			if len(temp) >= 6:
				temp[5] *= playatts['transpose']	
			
		return temp

		
	def out(self, **playatts):
		"""
			Printing
		"""
		# IF THERE ARE PLAYATTS, WE WILL REINVENT OURSELVES
		# PASSED PLAYATTS ARE ONLY TEMPORARY AND DO NOT
		# ALTER THE ORIGINAL EVENT.  FOR THAT USE
		# "event.warp = 1.4" and so on.
		if(len(playatts)):
			temp = self.copy(**playatts)
		else:
			temp = self

		out = ''
		if len(temp) > 0:
			#out = temp[0]
			#if type(temp[1]) == type(''):
			#	out += ' '
			out = ' '.join([str(i) for i in temp])
		return out 


	def __str__(self):
		return self.out()


	def __mul__(self, num):
		temp = Phrase()
		for i in range(0, num):
			temp.append(self.copy())
		return temp
	

class Phrase(list):
	""" 
		Group of Events, and/or other Phrases. Phrases 
		can contain any mixture of Events and Phrases to 
		an arbitrary level of hierarchy.
	"""

	def read(self, filename):
		for line in open(filename, r):
			self.append(Event(line))
		


	def __init__(self, starter = [], **play_atts):
		self.start		= 0
		self.warp		= 1
		self.dwarp		= 1
		self.amp		= 1
		self.transpose		= 1
		self.length		= 0

		for key, val in play_atts:
			setattr(self, key, val)
			
		self.type = 'phrase'
		self.block_playatts	= 0

		for e in starter:
			self.append(e)

	def cat(self, thing):
		self.append(thing.copy(start = self.length))
		self.length += thing.length

	def __str__(self):
		"""
			print all events in score format
		"""
		outstring = "Phrase\n"
		for e in self:
			outstring += str(e) + "\n"
		return outstring

	def copy(self, **playatts):
		temp = Phrase()
		for e in self:
			temp.append(e.copy(**playatts))
		return temp

	def __add__(self, other):
		temp = self.copy()
		for e in other:
			temp.append(e.copy())
		return temp

	def __mul__(self, num):
		temp = list()
		for i in range(0, num):
			temp += self
		return temp

	def zith(self, pfield, start, end):
		event_count = len(self)
		span = end - start
		for event_index in range(event_count):
			e = self[event_index]
			if e.type == 'phrase':
				e.zith(pfield, start, end)
			portion = event_index / (float(event_count) - 1.0)
			value = start + portion * span
			self[event_index][pfield] = value

	def ezith(self, pfield, start, end):
		start	= float(start); end = float(end)
		steps	= float(len(self) - 1.0)
		span	= end / start
		for e in range(len(self)):
			portion = e / steps 
			value = start * span ** portion
			self[e][pfield] = value

	def out(self, **playatts):

		if type(playatts) is type({}):
			playatts = Playatts(playatts)

		playatts['warp'] 	*= self.warp
		playatts['dwarp'] 	*= self.dwarp
		playatts['start'] 	+= self.start
		playatts['amp'] 	*= self.amp
		playatts['transpose'] 	*= self.transpose

		output = ''
		for e in self:
			output += e.out(**playatts) + "\n"

		return output

class DrumScore(Phrase):
	
	def __init__(self, starter = [], **play_atts):
		Phrase.__init__(self, starter, play_atts)
	
	def append(self, what):
		
		Phrase.append(self, what, start = self.length)

class DrumPattern(Phrase):

	volume_map = {
		'.':	0,
		'+':	.05,
		'-':	-.05,
		'u':	.1,	
		'd':	-.1,	
		'U':	.2,
		'D':	-.2
	}


	def __init__(self, kit, **kwargs):
		#pdb.set_trace();
		Phrase.__init__(self)
		self.kit = kit
		self.pattern = kwargs
		self.length = 0

		for name, sequence in self.pattern.iteritems():
			self.last_volume = '0'
			drum = kit[name]
			position = 0
			for num in sequence:
				position += 1
				num = self.translate(num)
				if num:
					e = drum.copy(start = position)
					e[4] *= num
					self.last_volume = num
					self.append(e)
		if position > self.length:
			self.length = position

	def out(self, atom = 1.0, **kwargs):
		return Phrase.out(self, warp = atom, dwarp = 1)


	def translate(self, num):
		
		if num == ' ':
			return None
		elif num == '0':
			self.last_volume = 1

		elif num in self.volume_map:
			self.last_volume += self.volume_map[num]
			if self.last_volume < 0:
				self.last_volume = 0
			if self.last_volume > 1:
				self.last_volume = 1
		else:
			self.last_volume = float(num) / 10.0

		return self.last_volume

class DrumKit(dict):
	
	def __init__(self, drums = None, **kwargs):
		if drums:
			for name, drum in drums:
				self[name] = drum
		self.update(kwargs)

class Drum(Event):

	def __init__(self, base_event):
		
		Event.__init__(self, base_event)


class PmapError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)



















