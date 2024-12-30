import pandas as pd

def update_heatmap_data(data, bounds):
    if bounds:
        sw_lat = bounds['_southWest']['lat']
        sw_lng = bounds['_southWest']['lng']
        ne_lat = bounds['_northEast']['lat']
        ne_lng = bounds['_northEast']['lng']
        data = data[(data['latitude'] >= sw_lat) & (data['latitude'] <= ne_lat) &
                    (data['longitude'] >= sw_lng) & (data['longitude'] <= ne_lng)]
    return data

def filter_data(data, selected_year, selected_date_range, selected_neighborhoods):
    filtered_data = data[data['year'] == selected_year] if selected_year != 'Total' else data
    filtered_data = filtered_data[(pd.to_datetime(filtered_data['diagnosis_date']) >= selected_date_range[0]) & 
                                  (pd.to_datetime(filtered_data['diagnosis_date']) <= selected_date_range[1])]
    if 'All' not in selected_neighborhoods:
        filtered_data = filtered_data[filtered_data['neighborhood'].isin(selected_neighborhoods)]
    return filtered_data
