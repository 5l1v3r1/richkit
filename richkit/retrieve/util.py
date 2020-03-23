import requests
import json
import logging
import statistics
from datetime import datetime
from richkit.analyse import tld, sld, sl_label, depth, length

logger = logging.getLogger(__name__)


class DomainCertificates:

    # Website used to retrieve the certificates belonging a domain
    crtSH_url = "https://crt.sh/{}"

    def __init__(self, domain):
        self.domain = domain
        self.certificates = None
        self.certificates_features = None
        self.get_certificates(self.domain)

    def get_certificates(self, domain):

        try:
            r = requests.get(self.crtSH_url.format("?q=" + domain + "&output=json"))
            content = r.content.decode('utf-8')
            if len(r.text) == 2:        # It's 2 when the domain is not found
                raise Exception("Domain not found")
            self.certificates = json.loads(content)
        except Exception as e:
            logger.error('Error while retrieving certificates: %s', e)
            raise e

    def get_certificate_info(self, cert_id):
        try:
            r = requests.get(self.crtSH_url.format("?id=" + cert_id))
            if "<BR><BR>Certificate not found </BODY>" in r.text:
                raise Exception("Certificate not found")
            if "<BR><BR>Invalid value:" in r.text:
                raise Exception("Certificate not found")
            return r.text
        except Exception as e:
            logger.error('Error while retrieving certificate %s: %s', cert_id, e)
            return None

    def get_cert_features(self):
        certs_features = []
        for cert in self.certificates:
            if '@' not in cert.get('name_value'):
                not_before = cert.get('not_before')
                not_after = cert.get('not_after')
                not_before_obj = datetime.strptime(not_before, "%Y-%m-%dT%H:%M:%S")
                not_after_obj = datetime.strptime(not_after, "%Y-%m-%dT%H:%M:%S")
                validity = (not_after_obj.date() - not_before_obj.date()).days
                features = dict({
                    'ID': cert.get('id'),
                    'Issuer': cert.get('issuer_name'),
                    'Algorithm': None,
                    'ValidationL': None,
                    'NotBefore': not_before,
                    'NotAfter': not_after,
                    'Validity': validity,       # days
                    'SANFeatures': None
                })
                certs_features.append(features)
        self.certificates_features = certs_features
        return certs_features

    def get_san_features(self):
        for cert in self.certificates_features:
            text = self.get_certificate_info(str(cert["ID"]))
            text_list = text.split('<BR>')

            SAN_list = []           # Used to store the  SANs
            policy_list = []        # Used to store the policies in order to get the Validation Level

            algo_index = '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Signature&nbsp;Algorithm:'
            san_index = '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;DNS:'
            policy_index = '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Policy:&nbsp;'
            for row in text_list:
                # Get Signature Algorithm
                if algo_index in row:
                    cert["Algorithm"] = row[len(algo_index) + 6:]

                # Get SANs
                if san_index in row:
                    SAN_list.append(row[len(san_index):])

                if policy_index in row:
                    policy_list.append(row[len(policy_index):])

            cert["ValidationL"] = policy_list
            cert["SANFeatures"] = dict({
                'util': SAN_list,
                'DomainCount': len(SAN_list),
                'UniqueApexCount': unique_apex(SAN_list),
                'UniqueSLDCount': unique_sld(SAN_list),
                'ShortestSAN': int(min([length(row) for row in SAN_list])),
                'LongestSAN': int(max([length(row) for row in SAN_list])),
                'SANsMean': statistics.mean([len(row) for row in SAN_list]),
                'MinSublabels': min([int(depth(row)) - 2 for row in SAN_list]),
                'MaxSublabels': max([int(depth(row)) - 2 for row in SAN_list]),
                'MeanSublabels': statistics.mean([int(depth(row)) for row in SAN_list]),
                'UniqueTLDsCount': unique_tld(SAN_list),
                'UniqueTLDsDomainCount': unique_tld(SAN_list) / len(SAN_list),
                'ApexLCS': None,        # Don't need to implement
                'LenApexLCS': None,
                'LenApexLCSnorm': None
            })

        return self.certificates_features


def unique_apex(sans):
    """
    Number of unique apex/root domains covered by the certificate
    :param sans: List of Subject Alternative Name
    """
    apex = [sld(san) for san in sans]
    return len(set(apex))


def unique_tld(sans):
    """
    Number of unique apex/root domains covered by the certificate
    :param sans: List of Subject Alternative Name
    """
    get_tlds = [tld(san) for san in sans]
    return len(set(get_tlds))


def unique_sld(sans):
    """
    Number of unique apex/root domains covered by the certificate
    :param sans: List of Subject Alternative Name
    """
    get_sld = [sl_label(san) for san in sans]
    return len(set(get_sld))
