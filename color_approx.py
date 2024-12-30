import numpy as np

data = [i for i in range(100)]

import folium
from folium.plugins import HeatMap

m = folium.Map([48.0, 5.0], zoom_start=6)

HeatMap(data).add_to(m)