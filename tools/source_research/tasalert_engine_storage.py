"""Single offline envelope for HTTP state and retained records. No HA I/O."""
from copy import deepcopy
from datetime import datetime
import json
from xml.etree.ElementTree import Element, SubElement, tostring
from tasalert_engine import Engine
from tasalert_kml import parse_kml
from tasalert_retention import MAX_RECORDS
from tasalert_storage import decode as decode_response, encode as encode_response
from tasalert_storage import atomic_write

LIMIT = 16 * 1024 * 1024


def validate_record(record, identifier):
    if not isinstance(record,dict) or set(record)!={'id','name','fields','record_times','point','has_polygon'}:
        raise ValueError('Invalid retained record shape')
    if record['id']!=identifier or not isinstance(record['name'],str) or type(record['has_polygon']) is not bool:
        raise ValueError('Invalid record identity')
    if not isinstance(record['fields'],dict) or not all(isinstance(k,str) and isinstance(v,str) for k,v in record['fields'].items()):
        raise ValueError('Invalid fields')
    root=Element('kml',xmlns='http://www.opengis.net/kml/2.2')
    mark=SubElement(root,'Placemark',id=identifier)
    SubElement(mark,'name').text=record['name']
    data=SubElement(mark,'ExtendedData')
    for key,value in record['fields'].items():
        SubElement(SubElement(data,'Data',name=key),'value').text=value
    point=record['point']
    if point is not None:
        if not isinstance(point,dict) or set(point)!={'latitude','longitude'} or not all(type(v) in (int,float) for v in point.values()):
            raise ValueError('Invalid retained point')
        SubElement(SubElement(mark,'Point'),'coordinates').text=f"{point['longitude']},{point['latitude']}"
    if record['has_polygon']:SubElement(mark,'Polygon')
    if parse_kml(tostring(root))[0]!=record:
        raise ValueError('Inconsistent normalized record')


def decode(raw):
    if len(raw)>LIMIT:raise ValueError('Envelope exceeds limit')
    data=json.loads(raw)
    if not isinstance(data,dict) or set(data)!={'version','response','ledger','review'} or type(data['version']) is not int or data['version']!=1:
        raise ValueError('Invalid envelope')
    response=decode_response(json.dumps(data['response']).encode())
    ledger=data['ledger']
    if not isinstance(ledger,dict) or len(ledger)>MAX_RECORDS:raise ValueError('Invalid ledger')
    for identifier,entry in ledger.items():
        if not identifier.strip() or not isinstance(entry,dict) or set(entry)!={'record','last_seen','presence'}:
            raise ValueError('Invalid ledger entry')
        validate_record(entry['record'],identifier)
        if entry['presence'] not in ('in_snapshot','not_in_snapshot','review_required'):raise ValueError('Invalid presence')
        entry['last_seen']=datetime.fromisoformat(entry['last_seen'])
        if entry['last_seen'].utcoffset() is None:raise ValueError('Naive last-seen clock')
    review=data['review']
    expected={key for key,value in ledger.items() if value['presence']=='review_required'}
    if not isinstance(review,list) or not all(isinstance(v,str) for v in review) or len(set(review))!=len(review) or set(review)!=expected:
        raise ValueError('Inconsistent review state')
    if ledger and response.snapshot is None:raise ValueError('Ledger without accepted representation')
    return Engine(response,ledger,tuple(review),())  # Expiry is not replayed after restart.


def encode(engine):
    ledger=deepcopy(engine.ledger)
    for entry in ledger.values():entry['last_seen']=entry['last_seen'].isoformat()
    raw=json.dumps({'version':1,'response':json.loads(encode_response(engine.response)),
                    'ledger':ledger,'review':list(engine.review)},sort_keys=True,allow_nan=False).encode()
    decode(raw)
    return raw


def save(path,engine):
    atomic_write(path,encode(engine))


def load(path):
    with open(path,'rb') as stream:return decode(stream.read(LIMIT+1))
