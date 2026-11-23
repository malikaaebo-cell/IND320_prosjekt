"""
Convert the NVE shapefiles from part 3 to GeoJSON for the map in the Streamlit app (part 4).

The areas are built exactly as in the part 3 notebook:
  - EL 1-5:   the electricity price areas (Budområder), 'NO 1' -> 'EL 1'
  - VASS 1-3: NVE's regions merged as East = RØ + RS, West = RV, North = RM + RN
  - NO 0:     Norway as a whole, the union of the price areas
The geometries are converted to longitude/latitude (WGS84, which web maps use) and
simplified (about 1 km tolerance) so the file stays small enough for the app.

Run from the project folder in the environment with geopandas (the notebook environment):
    ~/venvs/ind320/bin/python scripts/make_geojson.py
"""
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SHAPE_DIR = ROOT / 'project_data' / 'shapefiles'
OUT = ROOT / 'project_data' / 'areas.geojson'

# Read the zipped shapefiles (UTF-8, so that 'RØ' is read correctly)
elspot = gpd.read_file(f"zip://{SHAPE_DIR / 'budomrader.zip'}")
regions = gpd.read_file(f"zip://{SHAPE_DIR / 'nve_region.zip'}", encoding='utf-8')

# Electricity price areas: 'NO 1' -> 'EL 1'
el = elspot[['budomr', 'geometry']].copy()
el['area'] = el['budomr'].str.replace('NO', 'EL')

# Water (precipitation) areas: merge NVE's regions
vass_map = {'RØ': 'VASS 1', 'RS': 'VASS 1', 'RV': 'VASS 2', 'RM': 'VASS 3', 'RN': 'VASS 3'}
regions['area'] = regions['REGION'].map(vass_map)
vass = regions.dropna(subset=['area']).dissolve(by='area').reset_index()[['area', 'geometry']]

# Norway as a whole
no0 = gpd.GeoDataFrame({'area': ['NO 0']}, geometry=[el.union_all()], crs=el.crs)

areas = gpd.GeoDataFrame(pd.concat([el[['area', 'geometry']], vass.to_crs(el.crs), no0],
                                   ignore_index=True), crs=el.crs)
areas['area_type'] = areas['area'].str.split().str[0]

# To WGS84 and simplify (0.01° ≈ 1 km), keeping neighbouring areas consistent
areas = areas.to_crs(epsg=4326)
areas['geometry'] = areas.geometry.simplify(0.01, preserve_topology=True)

areas[['area', 'area_type', 'geometry']].to_file(OUT, driver='GeoJSON')
print(areas[['area', 'area_type']])
print(f"Saved {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)")
