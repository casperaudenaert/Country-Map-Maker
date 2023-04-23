from flask import Flask, render_template, request, send_file
import folium
from geopy.geocoders import Nominatim
import time
import os
from bs4 import BeautifulSoup
import requests
import re
from difflib import SequenceMatcher

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching of map HTML files
def addButton(html, onclick):
    with open(html) as fp:
        soup = BeautifulSoup(fp, "html.parser")

# create a new button tag
    button_tag = soup.new_tag("button")
    button_tag.string = "Return"
    button_tag['onclick'] = onclick
    button_tag['style'] = "background-color: #4CAF50; color: white; padding: 12px 20px; border: none; border-radius: 4px; cursor: pointer;"
# find the script tag
    script_tag = soup.find("script", text=re.compile("L_NO_TOUCH"))

# insert the button before the script tag
    script_tag.insert_before(button_tag)

# save the modified HTML
    with open(html, "w") as fp:
        fp.write(str(soup)) 
#test comment
@app.route('/', methods=['GET', 'POST'])
def index():
    path = "./templates/"

# Set the list of files you want to keep
    keep_files = ["index.html", "map.html","style.css"]

# Loop through all the files in the directory
    for file in os.listdir(path):
    # Check if the file is not in the list of files to keep
        if file not in keep_files:
        # If it's not, remove the file
            os.remove(os.path.join(path, file))
    if request.method == 'POST':
        timestamp = int(time.time())
        filename = f"map_{timestamp}.html"
        # Get the form data
        country_names = request.form.get('country').split(',')
        city_names = request.form.get('cities').split(',')
        marker_color = request.form.get('marker_color', '#000000')
        line_color = request.form.get('line_color', '#000000')
        line_style = request.form.get('line_style')

        # Create a Map object centered on the country with a white background
        geolocator = Nominatim(user_agent="my_map")
        location = geolocator.geocode(country_names[0])
        map_obj = folium.Map(location=[location.latitude, location.longitude], zoom_start=6, tiles='cartodbpositron')
        map_obj.get_root().html.add_child(folium.Element("<style>.folium-map {cursor: crosshair;}</style>"))

        # Add circles with labels for each city to the map
        locations = []
        for country_name in country_names:
            for i, city_name in enumerate(city_names):
                response = requests.request("GET", f"https://www.geonames.org/search.html?q={city_name}&country=")
                country = re.findall("/countries.*\.html", response.text)[0].strip(".html").split("/")[-1]
                s = SequenceMatcher(None, country_name, country)
                if s.ratio() >= 0.75:
                    location = geolocator.geocode(city_name + ", " + country_name)
                    if location and location.latitude and location.longitude:
                        # Define the circle style
                        circle_style = "background-color:{};border-radius:50%;text-align:center;display:inline-block".format(marker_color)
                        # Add the circle
                        folium.CircleMarker(
                            location=[location.latitude, location.longitude],
                            radius=7,
                            fill=True,
                            fill_opacity=1,
                            color=marker_color,
                            fill_color=marker_color,
                            popup=city_name,
                            tooltip=city_name,
                            overlay=True,
                            show=True,
                            style= circle_style,
                            z_index=99999
                        ).add_to(map_obj)
                        locations.append([location.latitude, location.longitude])
                    else:
                        print("Error geocoding city:", city_name)
        # Connect the circles with a line
        if line_style == "on":  
            folium.PolyLine(
                locations,
                color=line_color,
                weight=2,
                opacity=0.7,
                z_index=0
            ).add_to(map_obj)
        else:
            folium.PolyLine(
                locations,
                color=line_color,
                weight=2,
                opacity=0.7,
                dash_array='5,10',
                z_index=0
            ).add_to(map_obj)
        # Save the map to an HTML file
        map_obj.save(f'templates/{filename}')

        addButton(f'templates/{filename}', "history.go(-1)")
        addButton(f'templates/{filename}', "location.href = 'https://country-map-maker.herokuapp.com/download?filename={filename}';")
        # Render the map HTML file to the user
        return render_template(filename)
    return render_template('index.html')

@app.route('/download', methods=['GET', 'POST'])
def download():
    filename = request.args.get('filename')
    return send_file(f'templates/{filename}', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)