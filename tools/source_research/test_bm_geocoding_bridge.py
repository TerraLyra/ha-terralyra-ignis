"""Isolated actual geocoder replay without importing the HA integration."""
import subprocess
import sys
import unittest
from pathlib import Path

class GeocoderBridgeTests(unittest.TestCase):
    def test_actual_resolver_preserves_centre_for_identity_bridge(self):
        root=Path(__file__).resolve().parents[2]
        script = '''
import asyncio, importlib.util, sys, types
from pathlib import Path
sys.path.insert(0, 'tools/source_research')
from bm_settlement_identity import bridge_identity, load_records
core=types.ModuleType('homeassistant.core'); core.HomeAssistant=object
sys.modules['homeassistant']=types.ModuleType('homeassistant')
sys.modules['homeassistant.core']=core
spec=importlib.util.spec_from_file_location('geocoder_under_test',Path('custom_components/terralyra_ignis/geocoding.py'))
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
class Hass:
    config=types.SimpleNamespace(language='hu')
    async def async_add_executor_job(self, func, *args):
        return func(*args)
async def run():
    resolver=m.PlaceNameResolver(Hass())
    await resolver.async_setup()
    records=load_records()
    # Use an actual shared record; an offset observation must retain its centre.
    import sqlite3
    with sqlite3.connect(m.DATABASE_PATH) as db:
        rows=db.execute("SELECT name,country_code,latitude,longitude FROM places WHERE country_code='HU'").fetchall()
    row=next(r for r in rows if bridge_identity(*r,records))
    name,country,lat,lon=row
    place=await resolver.async_resolve(lat+0.00001,lon)
    assert place.nearest_settlement == name
    assert place.settlement_latitude == lat
    assert place.settlement_longitude == lon
    assert place.settlement_distance_km > 0
    assert bridge_identity(place.nearest_settlement,place.settlement_country,place.settlement_latitude,place.settlement_longitude,records)==bridge_identity(*row,records)
    assert m.PlaceInfo(None,'Town','description').settlement_latitude is None
    # End-to-end identity/time policy against the actual context implementation.
    package=types.ModuleType('_bridge_context')
    package.__path__=[str(Path('custom_components/terralyra_ignis').resolve())]
    sys.modules['_bridge_context']=package
    from _bridge_context.bm_satellite_context import BMTownReport, bm_reports_for_satellite
    from _bridge_context.report_context import IncidentContext
    from datetime import datetime, UTC, timedelta
    now=datetime(2026,10,7,12,tzinfo=UTC)
    incident=IncidentContext('satellite-1',lat+0.00001,lon,now,now)
    town_ids=bridge_identity(place.nearest_settlement,place.settlement_country,place.settlement_latitude,place.settlement_longitude,records)
    report=BMTownReport('https://www.katasztrofavedelem.hu/modules/vesz/esemeny/1',now+timedelta(hours=2),town_ids,True)
    result=bm_reports_for_satellite(incident.incident_id,(incident,),{incident.incident_id:town_ids},(report,))
    assert result['reports'][0]['relation']=='probable'
    assert result['creates_incident'] is False
    assert incident.latitude==lat+0.00001
    assert not bm_reports_for_satellite(incident.incident_id,(incident,),{},(report,))['reports']

asyncio.run(run())
'''
        result=subprocess.run([sys.executable,'-c',script],cwd=root,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
