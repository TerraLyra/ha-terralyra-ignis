import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
for (const name of ['ignis-bm-reports.js','ignis-location-summary.js','ignis-report-map.js']) {
  test(`HACS bundle matches tested source: ${name}`, () => {
    assert.deepEqual(readFileSync(`custom_components/terralyra_ignis/www/${name}`),
      readFileSync(`frontend/${name}`), 'Run python3 tools/sync_frontend.py');
  });
}
