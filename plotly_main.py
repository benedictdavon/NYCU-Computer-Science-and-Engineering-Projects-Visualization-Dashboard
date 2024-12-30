import pandas as pd
import folium
from folium.plugins import HeatMap
import branca.colormap as cm

# Load the data
data = pd.read_csv("datasets/dengue_fever_cases_by_area.csv")

# Create a color scale for the legend based on the 'cases' column
min_cases = data['cases'].min()
max_cases = data['cases'].max()

# Create a linear colormap for the legend, representing the range of 'cases'
colormap = cm.LinearColormap(["blue", "cyan", "green", "yellow", "red"]).scale(min_cases, max_cases) # Creates 5 discrete steps in the color scale
print(colormap)
# Create the map
m = folium.Map(location=[23.12303, 119.9416977], zoom_start=10, control_scale=True)

# Prepare the data for the HeatMap plugin using 'cases' for color mapping
map_values = data[['latitude', 'longitude', 'cases']].values

# Define the gradient for the HeatMap
gradient = {0: '#0000FF', 0.2: '#00FFFF', 0.4: '#00FF00', 0.6: '#FFFF00', 1: '#FF0000'}


# Enhance the heatmap appearance with a smoother gradient and clearer transition
hm = HeatMap(
    map_values, 
    min_opacity=0.4, 
    max_opacity=0.7, 
    radius=25,
    gradient=gradient
).add_to(m)

# Add the colormap legend to the map based on the 'cases' values
colormap.caption = 'Number of Dengue Cases'
colormap.add_to(m)

# Save the map as an HTML file
m.save('datasets/map.html')
