"""Offline WMS evidence inspector; no networking or production eligibility decision."""
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

NS = '{http://www.opengis.net/wms}'
MAX_BYTES = 3_000_000


def inspect_capabilities(payload: bytes) -> dict:
    """Preserve advertised evidence without treating ranges as available products."""
    if not isinstance(payload, bytes) or len(payload) > MAX_BYTES:
        raise ValueError('Expected bounded XML bytes')
    try:
        source = payload.decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise ValueError('Expected UTF-8 XML') from exc
    if '\x00' in source or '<!DOCTYPE' in source.upper() or '<!ENTITY' in source.upper():
        raise ValueError('Unsupported XML declarations')
    parser = ET.XMLPullParser(events=('start', 'end'))
    root = None
    depth = nodes = 0
    try:
        for offset in range(0, len(source), 4096):
            parser.feed(source[offset:offset + 4096])
            for event, element in parser.read_events():
                if event == 'start':
                    root = element if root is None else root
                    depth += 1
                    nodes += 1
                    if depth > 32 or nodes > 30_000:
                        raise ValueError('XML structure exceeds limits')
                else:
                    depth -= 1
        parser.close()
    except ET.ParseError as exc:
        raise ValueError('Malformed XML') from exc
    if root is None or root.tag != NS + 'WMS_Capabilities' or root.get('version') != '1.3.0':
        raise ValueError('Expected WMS 1.3.0 capabilities, not an error document')
    matches = [e for e in root.iter(NS + 'Layer')
               if e.findtext(NS + 'Name') == 'ecmwf.fwi']
    if len(matches) != 1:
        raise ValueError('Expected exactly one ecmwf.fwi layer')
    layer = matches[0]
    # Do not guess inherited attributes: missing queryability remains unknown.
    queryable = {'0': False, '1': True}.get(layer.get('queryable'))
    dimensions = [e for e in layer.findall(NS + 'Dimension') if e.get('name') == 'time']
    if len(dimensions) > 1:
        raise ValueError('Ambiguous time dimension')
    dimension = dimensions[0] if dimensions else None
    return {
        'layer': 'ecmwf.fwi',
        'queryable_explicit': queryable,
        'time_expression': dimension.text.strip() if dimension is not None and dimension.text else None,
        'time_default': dimension.get('default') if dimension is not None else None,
        'abstract': layer.findtext(NS + 'Abstract'),
        'feature_info_formats': [e.text for e in root.findall('.//' + NS + 'GetFeatureInfo/' + NS + 'Format')],
        'production_ready': False,
        'unresolved': ['actual_product_dates', 'model_issuance', 'numeric_or_class_semantics',
                       'nodata_and_failure_distinction', 'operational_availability'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capabilities', type=Path)
    args = parser.parse_args()
    with args.capabilities.open('rb') as stream:
        result = inspect_capabilities(stream.read(MAX_BYTES + 1))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
