import socket
from struct import unpack
import pprint

DEBUG_OUTPUT = True

class MaxMindReader:

	def __init__(self, data_dir):

		self.data_reader = [
			{
				'file' : data_dir + 'GeoIPCountryWhois.csv',
				'reader' : self.readIPv4CountryWhois
			},
			{
				'file' : data_dir + 'GeoIPv6.csv',
				'reader' : self.readIPv6CountryWhois
			},
			{
				'file' : data_dir + 'GeoLiteCity-Location.csv',
				'reader' : self.readCityLocations
			},
			{
				'file' : data_dir + 'GeoIPASNum2v6.csv',
				'reader' : self.readIPv6ToASN
			},
			{
				'file' : data_dir + 'GeoIPASNum2.csv',
				'reader' : self.readIPv4NumToASN
			},
			{
				'file' : data_dir + 'GeoLiteCityv6.csv',
				'reader' : self.readIPv6Locations
			},
			{
				'file' : data_dir + 'GeoLiteCity-Blocks.csv',
				'reader' : self.readCityBlocks
			}
		]

		''' comment -> format of the entries '''
		self.countries = dict() # [id] : country_name
		self.ipv4_to_country = list() # [ipv4_start, ipv4_end, ipv4_num_start, ipv4_num_end, country_code]
		self.ipv6_to_country = list() # [ipv6_start, ipv6_end, ipv6_num_start, ipv6_num_end, country_code]
		self.location_definitions = dict()  # [locId] : [country, region, city, postalCode, latitude, longitude, metroCode, areaCode]
		self.ipv4_location_blocks = list() # [ipv4_num_start, ipv4_num_end, locId]
		self.ipv6_locations = list() # [ipv6_s, ipv6_e, ipv6_num_s, ipv6_num_e, country_code, latitude, longitude]
		self.ipv4_asn_blocks = list() # [ipv4_num_start, ipv4_num_end, as_number]
		self.ipv6_asn_blocks = list() # [ipv6_num_start, ipv6_num_end, ipv6_prefix, as_number]

		self.asns = dict() # [as_number] : owner

		for source in self.data_reader:
			source['reader'](source['file'])

	def readIPv6ToASN(self, file_name):
		''' asn, ipv6_start, ipv6_end, ipv6_prefix '''

		try:
			f = file(file_name)
		except:
			raise IOError('(readIPv6ToASN) failed to open %s.\n' % (file_name))

		for line in f:

			elems = line.translate(None, '"\n').split(',')

			if len(elems) < 4:
				raise Exception('(readIPv6ToASN) invalid line length readIPv6ToASN: %s' % (elems))

			as_ident = elems[0].split(' ')[0]
			as_number = as_ident.translate(None, 'AS')

			if not as_number.isdigit():
				raise Exception('(readIPv6ToASN) invalid AS number in readIPv6ToASN: %s' % (elems))

			if as_number not in self.asns:

				as_owner = ''.join(elems[0:-3]).split(' ')[1:]

				if len(as_owner)  == 0:
					self.asns[int(as_number)] = as_ident + ' (unknown)'
				else:
					self.asns[int(as_number)] = ' '.join(as_owner)

			self.ipv6_asn_blocks.append([MaxMindReader.ipv6str2num(elems[-3].strip()), MaxMindReader.ipv6str2num(elems[-2].strip()), int(elems[-1]), int(as_number)])

		if DEBUG_OUTPUT:
			print '(readIPv6ToASN) IPv6 ASN blocks: %d' % (len(self.ipv6_asn_blocks))
			print '(readIPv6ToASN) ASN entries: %d' % (len(self.asns))

	def readIPv4NumToASN(self, file_name):
		''' ipv4_num_start, ipv4_num_end, asn '''

		try:
			f = file(file_name)
		except:
			raise IOError('(readIPv4NumToASN) failed to open %s.\n' % (file_name))

		missing_countries = []
		fixed_entries = 0
		
		for line in f:

			elems = line.translate(None, '"\n').split(',')

			if len(elems) < 3:
				raise Exception('(readIPv4NumToASN) invalid line length readIPv4NumToASN: %s' % (elems))

			if not elems[2].startswith('AS'):
				raise Exception('(readIPv4NumToASN) invalid line format readIPv4NumToASN: %s' % (elems))

			as_data = ' '.join(elems[2:]).split(' ')
			as_number = as_data[0].translate(None, 'AS')
			if not as_number.isdigit():
				raise Exception('(readIPv4NumToASN) invalid AS number in readIPv4NumToASN: %s' % (elems))

			if int(as_number) not in self.asns:
				self.asns[int(as_number)] = ' '.join(as_data[1:])
			self.ipv4_asn_blocks.append([int(elems[0]), int(elems[1]), int(as_number)])

		if DEBUG_OUTPUT:
			print '(readIPv6Locations) IPv4 ASN blocks: %d' % (len(self.ipv4_asn_blocks))
			print '(readIPv6Locations) ASN entries: %d' % (len(self.asns))

	def readIPv6Locations(self, file_name):

		''' ipv6_s, ipv6_e, ipv6_num_s, ipv6_num_e, country_code, ?, ?, latitude, longitude, ?, ?, ? '''

		try:
			f = file(file_name)
		except:
			raise IOError('(readIPv6Locations) failed to open %s.\n' % (file_name))

		missing_countries = []
		fixed_entries = 0
		
		for line in f:

			elems = line.translate(None, '"\n').split(',')

			if len(elems) is not 12:
				raise Exception('(readIPv6Locations) invalid line length readIPv6Locations: %s' % (elems))

			if elems[4] not in self.countries:
				self.countries[elems[4]] = elems[4] + ' (unknown)'
				fixed_entries += 1
				if elems[4] not in missing_countries:
					missing_countries.append(elems[4])

			self.ipv6_locations.append([elems[0], elems[1], int(elems[2]), int(elems[3]), elems[4], float(elems[7]), float(elems[8])])
		
		if DEBUG_OUTPUT:
			if fixed_entries > 0:
				print '(readIPv6Locations) fixed country entries: %d (%s)' % (fixed_entries, ','.join(missing_countries))
			print '(readIPv6Locations) IPv6 locations: %d' % (len(self.ipv6_locations))

	def readCityBlocks(self, file_name):

		''' ipv4_num_start, ipv4_num_end, locId '''

		try:
			f = file(file_name)
		except:
			raise IOError('(readCityBlocks) failed to open %s.\n' % (file_name))

		i = 0
		
		for line in f:
						
			elems = line.translate(None, '"\n').split(',')

			if not elems[0].isdigit():
				continue

			if len(elems) is not 3:
				raise Exception('(readCityBlocks) invalid line length readCityBlocks: %s' % (elems))

			self.ipv4_location_blocks.append([int(elems[0]), int(elems[1]), int(elems[2])])

		if DEBUG_OUTPUT:
			print '(readCityBlocks) IPv4 to city number blocks: %d' % (len(self.ipv4_location_blocks))

	def readCityLocations(self, file_name):

		''' locId, country, region, city, postalCode, latitude, longitude, metroCode, areaCode '''

		try:
			f = file(file_name)
		except:
			raise IOError('(readCityLocations) failed to open %s.\n' % (file_name))

		missing_countries = []
		fixed_entries = 0
		
		for line in f:

			elems = line.translate(None, '"\n').split(',')

			if not elems[0].isdigit():
				continue

			if len(elems) < 9 or len(elems) > 10:
				raise Exception('(readCityLocations) invalid line length readCityLocations: %s' % (elems))

			elems[0] = int(elems[0])

			if elems[1] not in self.countries:
				self.countries[elems[1]] = elems[1] + ' (unknown)'
				fixed_entries += 1
				if elems[1] not in missing_countries:
					missing_countries.append(elems[1])

			if len(elems) == 9:
				elems[5] = float(elems[5])
				elems[6] = float(elems[6])
				self.location_definitions[int(elems[0])] = elems[1:]
			else:
				self.location_definitions[int(elems[0])] = [elems[1], elems[2], ','.join(elems[3:5]), elems[5], float(elems[6]), float(elems[7]), elems[8], elems[9]]

		if DEBUG_OUTPUT:
			if fixed_entries > 0:
				print '(readCityLocations) fixed country entries: %d (%s)' % (fixed_entries, ','.join(missing_countries))
			print '(readCityLocations) city locations: %d' % (len(self.location_definitions))

	def readIPv4CountryWhois(self, file_name):

		''' ipv4_start, ipv4_end, ipv4_num_start, ipv4_num_end, country_code, country_name '''

		try:
			f = file(file_name)
		except:
			raise IOError('(readIPv4CountryWhois) failed to open %s.\n' % (file_name))

		for line in f:

			elems = line.translate(None, '"\n').split(',')

			if len(elems) > 7 or len(elems) < 6:
				raise Exception('(readIPv4CountryWhois) invalid line length readIPv4CountryWhois: %s' % (elems))

			if elems[4] is not None:
				self.countries[elems[4]] = ','.join(elems[5:])

			self.ipv4_to_country.append([elems[0], elems[1], int(elems[2]), int(elems[3]), elems[4]])

		if DEBUG_OUTPUT:
			print '(readIPv4CountryWhois) country codes: %d' % (len(self.countries))
			print '(readIPv4CountryWhois) IPv4 to country entries: %d' % (len(self.ipv4_to_country))

	def readIPv6CountryWhois(self, file_name):

		''' ipv6_start, ipv6_end, ipv6_num_start, ipv6_num_end, country_code, country_name '''
		try:
			f = file(file_name)
		except:
			raise IOError('(readIPv6CountryWhois) failed to open %s.\n' % (file_name))

		for line in f:

			elems = line.translate(None, '"\n').split(',')

			if len(elems) > 7 or len(elems) < 6:
				raise Exception('(readIPv6CountryWhois) invalid line length readIPv6CountryWhois: %s' % (elems))
			
			if elems[4] is not None:
				self.countries[elems[4]] = ','.join(elems[5:])
				
			self.ipv6_to_country.append([elems[0], elems[1], int(elems[2]), int(elems[3]), elems[4]])

		if DEBUG_OUTPUT:
			print '(readIPv6CountryWhois) country codes: %d' % (len(self.countries))
			print '(readIPv6CountryWhois) IPv6 to country entries: %d' % (len(self.ipv6_to_country))

	@staticmethod
	def ipv4str2num(address):
		return unpack('!I', socket.inet_aton(address))[0]

	@staticmethod
	def ipv6str2num(address):
		''' taken from http://stackoverflow.com/a/5620442 '''
		_str = socket.inet_pton(socket.AF_INET6, address)
		a, b = unpack('!2Q', _str)
		return (a << 64) | b

	@staticmethod
	def getipversion(address):

		try:
			socket.inet_pton(socket.AF_INET, address)
			return 4
		except:
			try:
				socket.inet_pton(socket.AF_INET6, address)
				return 6
			except:
				return None

	def get_ip_data(self, ip_address):

		ip_version = MaxMindReader.getipversion(ip_address)

		output = dict()
		if ip_version == 4:

			output['ip'] = {}
			output['ip']['address'] = ip_address
			output['ip']['version'] = 4
			ip_num = MaxMindReader.ipv4str2num(ip_address)
			output['ip']['uint'] = ip_num

			output['location'] = {}
			for entry in self.ipv4_to_country:
				if entry[2] <= ip_num and entry[3] >= ip_num:
					country_code = entry[4]
					country_name = self.countries[country_code]
					output['location']['country'] = {
						'code' : country_code, 
						'name' : country_name
					}
					break
					
			for entry in self.ipv4_location_blocks:
				if entry[0] <= ip_num and entry[1] >= ip_num:
					loc_id = entry[2]
					loc_def = self.location_definitions[loc_id]

					output['location']['longitude'] = loc_def[5]
					output['location']['latitude'] = loc_def[4]
					output['location']['city'] = loc_def[2]
					break

			for entry in self.ipv4_asn_blocks:
				if entry[0] <= ip_num and entry[1] >= ip_num:
					as_num = entry[2]
					output['as'] = {
						'num' : as_num, 
						'owner' : self.asns[as_num]
					}
					break
		elif ip_version == 6:

			output['ip'] = {}
			output['ip']['address'] = ip_address
			output['ip']['version'] = 6
			ip_num = MaxMindReader.ipv6str2num(ip_address)
			output['ip']['uint'] = ip_num

			output['location'] = {}
			for entry in self.ipv6_locations:
				if entry[2] <= ip_num and entry[3] >= ip_num:
					country_code = entry[4]
					country_name = self.countries[country_code]
					output['location']['country'] = {
						'code' : country_code, 
						'name' : country_name
					}
					output['location']['longitude'] = entry[6]
					output['location']['latitude'] = entry[5]
					break

			for entry in self.ipv6_asn_blocks:
				if entry[0] <= ip_num and entry[1] >= ip_num:
					as_num = entry[3]
					output['as'] = {
						'num' : as_num, 
						'owner' : self.asns[as_num]
					}
					output['ip']['prefix'] = entry[2]
					break
		else:
			output = {'error' : 'invalid IP address'}

		return output
