"""One bounded, offline Victoria research report; no production readiness claim."""
import argparse
import json
import sys
from victoria_feed import inspect_feed, InvalidFeed
from victoria_records import summarize_records
from victoria_spatial import summarize_spatial


def inspect_report(payload: bytes, *, max_bytes=1_048_576, max_records=10_000):
    """Validate the entire envelope before reporting any count.

    Dimensions overlap: category, location and time counts are not additive.
    Reports never contain raw IDs, text, coordinates or dates.
    """
    records=inspect_feed(payload,max_bytes=max_bytes,max_records=max_records)
    identity_time=summarize_records(records)
    spatial=summarize_spatial(records)
    return {
        'schema_version':1,
        'purpose':'offline_source_research',
        'provider':'victoria',
        'status':'experimental',
        'production_readiness':'not_established',
        'record_count':len(records),
        'identity':identity_time['identity'],
        'duplicate_id_groups':identity_time['duplicate_id_groups'],
        'update_times':identity_time['update_times'],
        'categories':spatial['categories'],
        'locations':spatial['locations'],
        'limitations':[
            'dimensions_overlap',
            'developer_reuse_permission_unverified',
            'timestamp_semantics_unverified',
            'identity_lifetime_unverified',
            'taxonomy_incomplete',
            'position_accuracy_unverified',
            'feed_completeness_unverified',
            'not_an_active_fire_or_safety_assessment',
        ],
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',help='Local JSON file, or - for standard input; no network access')
    args=parser.parse_args(argv)
    try:
        if args.input=='-':
            payload=sys.stdin.buffer.read(1_048_577)
        else:
            with open(args.input,'rb') as source:
                payload=source.read(1_048_577)
        report=inspect_report(payload)
    except (InvalidFeed,OSError):
        # Do not echo a source path, payload, parser message or partial counts.
        print(json.dumps({'status':'failed','reason':'input_unreadable_or_invalid'}))
        return 2
    print(json.dumps(report,sort_keys=True))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
