from base64 import b64encode
import requests
from requests_oauthlib import OAuth1Session
from config import CLIENT_KEY, CLIENT_SECRET, BASE_URL, REQUEST_TOKEN_URL, ACCESS_TOCKEN_URL, FIELDS_LIST, USER, PASSWORD
import csv, json
import sys, os.path
import datetime
import pytz


user_pwd = b64encode(bytes('%s:%s' % (USER, PASSWORD), 'utf-8')).decode('ascii')
headers = {'Authorization': 'Basic %s' % user_pwd}


def prepare_connection():
    oauth_session = OAuth1Session(CLIENT_KEY, client_secret=CLIENT_SECRET)
    oauth_session.fetch_request_token('{0}/{1}'.format(BASE_URL, REQUEST_TOKEN_URL))
    oauth_session.fetch_access_token('{0}/{1}'.format(BASE_URL, ACCESS_TOCKEN_URL), 'verifier')
    return oauth_session


def get_accomodation(**kw):
    try:
        #oauth_session = prepare_connection()
        #response = oauth_session.get('{}/TurismoDrone.svc/accomodations?{}'.format(BASE_URL, '&'.join(['{}={}'.format(k,w) for k, w in kw.items()])))
        response = requests.get(
            '{}/TurismoDrone.svc/accomodations?{}'.format(BASE_URL, '&'.join(['{}={}'.format(k,w) for k, w in kw.items()])),
            headers=headers
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(e)
    return


def set_accomodation(accomodation):
    try:
        #oauth_session = prepare_connection()
        #response = oauth_session.put(
        #    '{}/TurismoDrone.svc/accomodations'.format(BASE_URL),
        #    data=json.dumps(accomodation, ensure_ascii=False),
        #    headers={'Content-Type': 'application/json'}
        #)
        put_headers = headers
        put_headers['Content-Type'] = 'application/json; charset=utf-8'
        response = requests.put(
            '{}/TurismoDrone.svc/accomodations?'.format(BASE_URL),
            data=json.dumps(accomodation, ensure_ascii=False).encode('utf8'),
            headers=put_headers
        )
        print(response.status_code)
        if response.status_code == 201:
            return response.json()
    except Exception as e:
        print(e)


def update_accomodation(accomodation, updates):
    try:
        #print('Before')
        #print(accomodation)
        for k, v in updates.items():
            if v:
                if k == 'IsAttivo':
                    accomodation[k + '_ISTAT'] = True if v == 'Attiva' else False
                    accomodation[k + '_Tariffe'] = True if v == 'Attiva' else False
                elif k == 'Apertura1Da' or k == 'Apertura1A':
                    date_v = datetime.datetime.strptime(v, '%d/%m/%Y')
                    date_v.replace(tzinfo=pytz.timezone('Europe/Rome'))
                    accomodation[k] = '/Date(' + str(date_v.timestamp() * 1000) + datetime.datetime.strftime(date_v, '%z)/')
                elif k == 'TotaleCamere':
                    accomodation[k + '_ISTAT'] = v
                    accomodation[k + '_Tariffe'] = v
                elif k.startswith('Is'):
                    accomodation[k] = True if v == '1' else False
                elif k == 'Id1' and v == '""':
                    accomodation[k] = None
                else:
                    accomodation[k] = v
        #print('After')
        #print(accomodation)
        return accomodation
    except Exception as e:
        print('Exception reading updates: ' + str(e))


if __name__ == '__main__':
    try:
        accomodations_filename = sys.argv[1]
        accomodations_reader = csv.DictReader(open(accomodations_filename))
        accomodations_writer = csv.DictWriter(
            open('out/' + os.path.basename(accomodations_filename), 'w'),
            fieldnames=FIELDS_LIST
        )
        accomodations_writer.writeheader()
        for accomodation in accomodations_reader:
            try:
                print('Get accomodation {0} {1} {2}'.format(
                    accomodation['Provincia'],
                    accomodation['Anno'],
                    accomodation['CodiceRegione']
                ))
                source_accomodations = get_accomodation(
                    provincia=accomodation['Provincia'],
                    anno=accomodation['Anno'],
                    codiceregione=accomodation['CodiceRegione'],
                    alldata='true'
                )
                if source_accomodations and len(source_accomodations) == 1:
                    print('Retreived one accomodation. Update accomodation.')
                    updated_accomodation = set_accomodation(update_accomodation(source_accomodations[0], accomodation))
                    if not updated_accomodation:
                        print('Error updating accomodation ' + accomodation['CodiceRegione'])
            except Exception as e:
                print('Exception: ' + str(e))
                print(accomodation['CodiceRegione'])
                #accomodations_writer.writerow(accomodation)
    except Exception as e:
        print('Exception: ' + str(e))


