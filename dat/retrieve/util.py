import requests
from bs4 import BeautifulSoup, NavigableString
import whois
import sys
import logging
logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    level=logging.DEBUG) ## default logging level is WARNING, making it DEBUG !
logger = logging.getLogger(__name__)


class URLVoid(object):

	def __init__(self, domain):
		self.domain = domain
		self.value = self.urlvoid_parser()

	def urlvoid_parser(self):
		"""
		Parses URLVOID table with beatifulsoup
		:return: dictionary which contains urlvoid response
		"""
		url = "https://www.urlvoid.com/scan/" + self.domain
		res = requests.get(url)
		text = res.text
		try:
			soup = BeautifulSoup(text, "lxml").find("table", class_="table table-custom table-striped")
			all_tr = soup.find_all("tr")
			value = {tr.find_all("td")[0].text:
						 tr.find_all("td")[1].text.replace("\xa0", "")
					 for tr in all_tr}
		except ModuleNotFoundError as me:
			logger.error("Opps ! Error : %s", me)
		return value

	def get_last_analysis_date(self):
		"""

		:return: Last analysis time of given domain on URLVOID
		"""
		try:
			result = self.value["Last Analysis"][:-9]
		except KeyError as ke:
			logger.error('Error while retrieving value',ke)
		return result

	def domain_registration_date(self):
		"""

		:return: Registration time of domain
		"""
		try:
			result = self.value["Domain Registration"]
		except KeyError as ke:

			logger.error(f' DRD: Error while retrieving value; %s ',ke)
		return result

	def blacklist_status(self):
		"""

		:return: Blacklist status among 36 services which are enable in URLVOID itself.
		"""
		try:
			result = self.value["Blacklist Status"]
		except KeyError as ke:

			logger.error(' Blacklist status: Error while retrieving value; %s ', ke)
		return result

	def get_asn(self):
		"""

		:return: ASN Number
		"""
		try:
			result = self.value["ASN"]
		except KeyError as ke:
			logger.error('ASN: Error while retrieving value; %s ',ke)
		return result

	def get_server_location(self):
		"""

		:return: Server location of domain which exists on URLVOID
		"""
		try:
			result = self.value["Server Location"]
		except KeyError as ke:

			logger.error(' Server Location : Error while retrieving value; %s ',ke)
		return result

	def get_ip_address(self):
		"""

		:return: IP address of given domain via URLVOID service
		"""
		try:
			result = self.value["IP Address"]
		except KeyError as ke:
			logger.error(' IP Address: Error while retrieving value; %s ',ke)
		return result

	def get_detection_rate(self):
		"""

		:return: Returns detection rate in percentage.
		"""
		try:
			parts = self.blacklist_status().split("/")
			result = int(parts[0]) / int(parts[1]) * 100
		except IndexError as ie:
			logger.error('Detection rate : Error while retrieving value; %s ',ie)
		return result

	def get_whois_info(self):
		"""

		:return: returns whois information of given domain name.
		"""
		domain = whois.query(self.domain)
		result = {
			"d_name"           : domain.name,
			"d_expiration_date": domain.expiration_date,
			"d_last_updated"   : domain.last_updated,
			"d_registrar"      : domain.registrar
		}
		return result
