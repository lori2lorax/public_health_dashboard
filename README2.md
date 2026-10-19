# EpiCentre interactive website

This folder adds a browser-based version of the EpiCentre NSW Public Health
Intelligence Dashboard. It is a static website: there is no database, package
installation, or web framework required.

## What is included

- `dist/` — ready-to-run website, styles, JavaScript and generated data
- `serve.mjs` — small local web server
- `serve-dashboard.cmd` — Windows launcher
- `serve-dashboard.sh` — macOS/Linux launcher
- `tools/build-data.mjs` — rebuilds the website data from the repository CSV and GeoJSON files
- `tools/validate-site.mjs` — checks data integrity and website file references
- `package.json` — convenient start, rebuild and validation commands

## Requirements

- Node.js 18 or newer: <https://nodejs.org/>
- An internet connection for the OpenStreetMap background tiles and the hosted
  Leaflet/font assets. The health data and NSW district boundaries are included
  locally in `dist/data/`.

No `npm install` command is needed because the website has no npm dependencies.

## Run on Windows

Open PowerShell or Command Prompt in the repository folder and run:

```powershell
.\serve-dashboard.cmd
```

Alternatively:

```powershell
npm start
```

## Run on macOS or Linux

Open Terminal in the repository folder and run:

```bash
chmod +x serve-dashboard.sh
./serve-dashboard.sh
```

Alternatively:

```bash
npm start
```

## Open the website

After starting the server, open:

<http://127.0.0.1:4173>

Keep the terminal open while using the dashboard. Press `Ctrl+C` in the terminal
to stop it. If an older version appears, refresh with `Ctrl+F5` on Windows/Linux
or `Command+Shift+R` on macOS.

## Rebuild website data

The repository must contain these original source files in its root:

- `nsw_admissions.csv`
- `nsw_ed_presentations.csv`
- `nsw_waiting_time.csv`
- `nsw_asthma_hospitalisation_rates.csv`
- `nsw_smoking.csv`
- `nsw_lhd_boundaries.geojson`

Then run:

```bash
npm run build:data
```

This recreates `dist/data/health-data.json` and the simplified
`dist/data/nsw-lhds.geojson` map file.

## Validate before committing

```bash
npm run validate
```

A successful result reports the number of observations, districts, indicators
and reporting years. The current package validates 780 observations across 15
Local Health Districts, five indicators and 24 reporting years.

## Add this update to the GitHub repository

1. Extract the update archive into the root of the existing repository.
2. Allow folders such as `dist/` and `tools/` to merge with the repository.
3. Review the new files with `git status`.
4. Run `npm run validate`.
5. Commit and push the update:

```bash
git add README2.md package.json serve.mjs serve-dashboard.cmd serve-dashboard.sh dist tools
git commit -m "Add interactive EpiCentre web dashboard"
git push
```

The archive intentionally contains only the new website files. It does not
duplicate or replace the existing Streamlit application, Python files, or raw
source datasets already in the repository.
