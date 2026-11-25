# geo.py
# The areas from Magasinstatistikk as GeoJSON (part 4). The file project_data/areas.geojson is
# made from the NVE shapefiles by scripts/make_geojson.py, with the same area labels as in
# Magasinstatistikk ('EL 1'-'EL 5', 'VASS 1'-'VASS 3' and 'NO 0').
import json

import streamlit as st

from modules.weather import DATA_DIR

GEOJSON_FILE = DATA_DIR / 'areas.geojson'


@st.cache_data(show_spinner=False)
def load_geojson(area_type):
    """GeoJSON FeatureCollection with only the areas of one type ('EL', 'VASS' or 'NO')."""
    with open(GEOJSON_FILE, encoding='utf-8') as f:
        geo = json.load(f)
    features = [ft for ft in geo['features'] if ft['properties']['area_type'] == area_type]
    return {'type': 'FeatureCollection', 'features': features}
