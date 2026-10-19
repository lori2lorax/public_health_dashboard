import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '..');
const data = JSON.parse(fs.readFileSync(path.join(root, 'dist/data/health-data.json'), 'utf8'));
const geo = JSON.parse(fs.readFileSync(path.join(root, 'dist/data/nsw-lhds.geojson'), 'utf8'));
const html = fs.readFileSync(path.join(root, 'dist/index.html'), 'utf8');
const js = fs.readFileSync(path.join(root, 'dist/app.js'), 'utf8');
const errors = [];

const required = ['year', 'LHD', 'indicator', 'value'];
data.forEach((row, index) => {
  required.forEach((key) => { if (row[key] === undefined || row[key] === '') errors.push(`Row ${index + 1} has no ${key}`); });
  if (!Number.isFinite(row.value)) errors.push(`Row ${index + 1} has a non-numeric value`);
});

const keys = data.map(row => `${row.year}|${row.LHD}|${row.indicator}`);
if (new Set(keys).size !== keys.length) errors.push('Duplicate year/LHD/indicator records found');

const districts = [...new Set(data.map(row => row.LHD))].sort();
const mapDistricts = geo.features.map(feature => feature.properties.lhd_name.replace(' Local Health District', '')).sort();
if (JSON.stringify(districts) !== JSON.stringify(mapDistricts)) errors.push('Data and map district names do not match');

const htmlIds = new Set([...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]));
const duplicateIds = [...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]).filter((id, i, all) => all.indexOf(id) !== i);
if (duplicateIds.length) errors.push(`Duplicate HTML IDs: ${[...new Set(duplicateIds)].join(', ')}`);
for (const match of js.matchAll(/els\.([A-Za-z0-9_]+)/g)) if (!htmlIds.has(match[1])) errors.push(`JavaScript references missing #${match[1]}`);

for (const file of ['styles.css', 'app.js', 'data/health-data.json', 'data/nsw-lhds.geojson']) {
  if (!fs.existsSync(path.join(root, 'dist', file))) errors.push(`Missing dist/${file}`);
}

if (errors.length) {
  console.error(errors.join('\n'));
  process.exit(1);
}

console.log(`Validated ${data.length} observations, ${districts.length} districts, ${new Set(data.map(row => row.indicator)).size} indicators and ${new Set(data.map(row => row.year)).size} reporting years.`);
