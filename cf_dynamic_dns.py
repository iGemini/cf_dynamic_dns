import sys
import requests
import logging
from systemd.journal import JournalHandler

# -----------------------------
# CONFIG SECTION
# -----------------------------
CF_USER = ''
CF_API_KEY = ''
DNS_ZONE_NAME = ''
DNS_ZONE_ID = ''
RECORD_NAME = ''
# -----------------------------

API_ENDPOINT = 'https://api.cloudflare.com/client/v4/'
API_HEADERS = { 'X-Auth-Email': CF_USER, 'X-Auth-Key': CF_API_KEY}

# -----------------------------
# SET UP LOGGING
# -----------------------------
logHandler = JournalHandler(SYSLOG_IDENTIFIER = 'cf-dynamic-dns')
formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
logHandler.setFormatter(formatter)
logger = logging.getLogger('cf-dynamic-dns')
logger.propagate = False
logger.setLevel(logging.DEBUG)
logger.addHandler(logHandler)
# -----------------------------

def main():
    externalIP = GetExternalIP()
    records = GetZoneRecords()

    if (records.get('success')):
        record = records.get('result')[0]
        recordID = record.get('id')
        recordIP = record.get('content')

        if (recordIP == externalIP):
            logger.info('Record is up to date.')
            sys.exit()

        logger.info('Record does not match external IP.')

        payload = {
            'type': 'A',
            'name': RECORD_NAME,
            'content': externalIP,
            'ttl': record.get('ttl'),
            'proxied': record.get('proxied')
        }

        try:
            result = requests.put(API_ENDPOINT + 'zones/' + DNS_ZONE_ID + '/dns_records/' + recordID, headers = API_HEADERS, json = payload, timeout = 5).json()
        except requests.Timeout as ex:
                logger.error('Record update timed out. {}'.format(ex))
                sys.exit()
        else:
            success = result.get('success')
            if not success:
                logger.error('There was an issue updating the record. {}'.format(result))
            else:
                logger.info('Record was successfully updated.')
    else:
        logger.error('There was a problem fetching the record data. {}'.format(records))

def GetExternalIP():
    try:
        result = requests.get('https://ipv4.icanhazip.com', timeout = 5)
    except requests.Timeout as ex:
        logger.error('External IP lookup timed out. {}'.format(ex))
        sys.exit()
    else:
        return result.text.rstrip()

def GetZoneRecords():
    payload = {'type': 'A', 'name': RECORD_NAME}
    try:
        result = requests.get(API_ENDPOINT + 'zones/' + DNS_ZONE_ID + '/dns_records/', headers = API_HEADERS, params = payload, timeout = 5).json()
    except requests.Timeout as ex:
        logger.error('Zone record lookup timed out. {}'.format(ex))
        sys.exit()
    else:
        return result

if __name__ == "__main__":
    main()
