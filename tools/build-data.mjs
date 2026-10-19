import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '..');
const out = path.join(root, 'dist', 'data');
fs.mkdirSync(out, { recursive: true });

const csvFiles = [
  'nsw_admissions.csv',
  'nsw_ed_presentations.csv',
  'nsw_waiting_time.csv',
  'nsw_asthma_hospitalisation_rates.csv',
  'nsw_smoking.csv'
];

function parseCsvLine(line) {
  const fields = [];
  let value = '';
  let quoted = false;
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (char === '"') {
      if (quoted && line[i + 1] === '"') { value += '"'; i++; }
      else quoted = !quoted;
    } else if (char === ',' && !quoted) {
      fields.push(value);
      value = '';
    } else value += char;
  }
  fields.push(value);
  return fields;
}

const rows = csvFiles.flatMap((file) => {
  const lines = fs.readFileSync(path.join(root, file), 'utf8').trim().split(/\r?\n/);
  const headers = parseCsvLine(lines.shift());
  return lines.filter(Boolean).map((line) => {
    const values = parseCsvLine(line);
    const record = Object.fromEntries(headers.map((h, i) => [h, values[i]]));
    return { year: record.year, LHD: record.LHD, indicator: record.indicator, value: Number(record.value) };
  });
});
fs.writeFileSync(path.join(out, 'health-data.json'), JSON.stringify(rows));

function sqDist(a, b) {
  const x = a[0] - b[0];
  const y = a[1] - b[1];
  return x * x + y * y;
}

function sqSegDist(p, a, b) {
  let x = a[0], y = a[1];
  let dx = b[0] - x, dy = b[1] - y;
  if (dx || dy) {
    const t = ((p[0] - x) * dx + (p[1] - y) * dy) / (dx * dx + dy * dy);
    if (t > 1) { x = b[0]; y = b[1]; }
    else if (t > 0) { x += dx * t; y += dy * t; }
  }
  dx = p[0] - x; dy = p[1] - y;
  return dx * dx + dy * dy;
}

function simplify(points, tolerance = 0.01) {
  if (points.length <= 4) return points;
  const sqTolerance = tolerance * tolerance;
  const radial = [points[0]];
  let previous = points[0];
  for (let i = 1; i < points.length; i++) {
    if (sqDist(points[i], previous) > sqTolerance) {
      radial.push(points[i]); previous = points[i];
    }
  }
  if (previous !== points.at(-1)) radial.push(points.at(-1));
  const keep = new Uint8Array(radial.length);
  keep[0] = keep[radial.length - 1] = 1;
  const stack = [[0, radial.length - 1]];
  while (stack.length) {
    const [first, last] = stack.pop();
    let index = 0, max = sqTolerance;
    for (let i = first + 1; i < last; i++) {
      const d = sqSegDist(radial[i], radial[first], radial[last]);
      if (d > max) { index = i; max = d; }
    }
    if (index) { keep[index] = 1; stack.push([first, index], [index, last]); }
  }
  const result = radial.filter((_, i) => keep[i]);
  if (result.length > 2 && (result[0][0] !== result.at(-1)[0] || result[0][1] !== result.at(-1)[1])) result.push(result[0]);
  return result;
}

function simplifyCoords(type, coords) {
  if (type === 'Polygon') return coords.map((ring) => simplify(ring));
  if (type === 'MultiPolygon') return coords.map((poly) => poly.map((ring) => simplify(ring)));
  return coords;
}

const geo = JSON.parse(fs.readFileSync(path.join(root, 'nsw_lhd_boundaries.geojson'), 'utf8'));
geo.features = geo.features.map((feature) => ({
  type: 'Feature',
  properties: { lhd_name: feature.properties.lhd_name },
  geometry: { type: feature.geometry.type, coordinates: simplifyCoords(feature.geometry.type, feature.geometry.coordinates) }
}));
fs.writeFileSync(path.join(out, 'nsw-lhds.geojson'), JSON.stringify(geo));
console.log(`Built ${rows.length} records and ${geo.features.length} map regions.`);
