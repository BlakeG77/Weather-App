import streamlit as st
import requests
import pandas as pd
from streamlit_folium import folium_static
import folium
from datetime import datetime

# API details
weather_url = "https://weatherapi-com.p.rapidapi.com/forecast.json"
weather_headers = {
    "x-rapidapi-key": "8523b56546msh7c41dedca271445p178031jsn1f64124b8f5d",
    "x-rapidapi-host": "weatherapi-com.p.rapidapi.com"
}

air_quality_api_key = "66e34f22-de8b-496c-a1f0-cbebac2de781"

# Initialize session state for unit selection
if 'unit' not in st.session_state:
    st.session_state.unit = 'Metric'  # Default unit


def get_weather_data(lat, lon, days=3):
    querystring = {"q": f"{lat},{lon}", "days": days}
    response = requests.get(weather_url, headers=weather_headers, params=querystring)
    return response.json()


def display_weather_data(weather_data, unit):
    if unit == 'Metric':
        temp = weather_data['current']['temp_c']
        feels_like = weather_data['current']['feelslike_c']
        wind_speed = weather_data['current']['wind_kph']
        wind_unit = 'kph'
        temp_unit = 'C'
    else:
        temp = weather_data['current']['temp_f']
        feels_like = weather_data['current']['feelslike_f']
        wind_speed = weather_data['current']['wind_mph']
        wind_unit = 'mph'
        temp_unit = 'F'

    st.write(f"**Temperature:** {temp} °{temp_unit}")
    st.write(f"**Feels Like:** {feels_like} °{temp_unit}")
    st.write(f"**Humidity:** {weather_data['current']['humidity']}%")
    st.write(f"**Wind Speed:** {wind_speed} {wind_unit}")
    st.write(f"**Pressure:** {weather_data['current']['pressure_mb']} mb / {weather_data['current']['pressure_in']} in")
    st.write(
        f"**Precipitation:** {weather_data['current']['precip_mm']} mm / {weather_data['current']['precip_in']} in")
    st.write(f"**Cloud Cover:** {weather_data['current']['cloud']}%")
    st.write(f"**UV Index:** {weather_data['current']['uv']}")


def display_hourly_forecast(weather_data, selected_date, unit):
    selected_day = next(day for day in weather_data["forecast"]["forecastday"] if day["date"] == selected_date)
    hourly = selected_day["hour"]

    # Prepare data for the line chart
    times = [datetime.strptime(hour["time"], "%Y-%m-%d %H:%M") for hour in hourly]
    formatted_times = [time.strftime("%H:%M") for time in times]

    if unit == 'Metric':
        temps = [hour["temp_c"] for hour in hourly]
        feels_like = [hour["feelslike_c"] for hour in hourly]
        humidity = [hour["humidity"] for hour in hourly]
    else:
        temps = [hour["temp_f"] for hour in hourly]
        feels_like = [hour["feelslike_f"] for hour in hourly]
        humidity = [hour["humidity"] for hour in hourly]

    # Create a DataFrame for the line chart
    df = pd.DataFrame({
        "Time": formatted_times,
        "Temperature": temps,
        "Feels Like": feels_like,
        "Humidity (%)": humidity
    })

    # Plot the line chart
    st.line_chart(df.set_index("Time"))


def display_weekly_temperatures(weather_data, unit):
    forecast_days = weather_data["forecast"]["forecastday"]
    dates = [day["date"] for day in forecast_days]
    max_temps = [day["day"]["maxtemp_c"] if unit == 'Metric' else day["day"]["maxtemp_f"] for day in forecast_days]
    min_temps = [day["day"]["mintemp_c"] if unit == 'Metric' else day["day"]["mintemp_f"] for day in forecast_days]

    # Create a DataFrame for the bar chart
    df = pd.DataFrame({
        "Date": dates,
        "Max Temperature": max_temps,
        "Min Temperature": min_temps
    })

    # Add radio button for selecting the temperature to display
    temp_selection = st.radio("Select Temperature Type:", ["Max Temperature", "Min Temperature"])

    if temp_selection == "Max Temperature":
        st.bar_chart(df[["Date", "Max Temperature"]].set_index("Date"))
    else:
        st.bar_chart(df[["Date", "Min Temperature"]].set_index("Date"))


@st.cache_data
def map_creator(latitude, longitude):
    m = folium.Map(location=[latitude, longitude], zoom_start=10)
    folium.Marker([latitude, longitude], popup="Station", tooltip="Station").add_to(m)
    folium_static(m)


@st.cache_data
def generate_list_of_countries():
    countries_url = f"https://api.airvisual.com/v2/countries?key={air_quality_api_key}"
    countries_dict = requests.get(countries_url).json()
    return countries_dict


@st.cache_data
def generate_list_of_states(country_selected):
    states_url = f"https://api.airvisual.com/v2/states?country={country_selected}&key={air_quality_api_key}"
    states_dict = requests.get(states_url).json()
    return states_dict


@st.cache_data
def generate_list_of_cities(state_selected, country_selected):
    cities_url = f"https://api.airvisual.com/v2/cities?state={state_selected}&country={country_selected}&key={air_quality_api_key}"
    cities_dict = requests.get(cities_url).json()
    return cities_dict

st.title("Weather and Air Quality Dashboard")
st.write("This web application provides weather and air quality data for a selected location.")


# Sidebar for selecting options and units
st.sidebar.title("Weather and Air Quality Options")
category = st.sidebar.selectbox("Select an option", ["By City, State, and Country", "By Nearest City (IP Address)",
                                                     "By Latitude and Longitude"])

# Radio button for unit selection
st.session_state.unit = st.sidebar.radio(
    "Select unit:",
    ["Metric", "Imperial"]
)

if category == "By City, State, and Country":
    countries_dict = generate_list_of_countries()
    if countries_dict["status"] == "success":
        countries_list = [country["country"] for country in countries_dict["data"]]
        countries_list.insert(0, "")

        country_selected = st.sidebar.selectbox("Select a country", options=countries_list)
        if country_selected:
            states_dict = generate_list_of_states(country_selected)
            if states_dict["status"] == "success":
                states_list = [state["state"] for state in states_dict["data"]]
                states_list.insert(0, "")
                state_selected = st.sidebar.selectbox("Select a state", options=states_list)
                if state_selected:
                    cities_dict = generate_list_of_cities(state_selected, country_selected)
                    if cities_dict["status"] == "success":
                        cities_list = [city["city"] for city in cities_dict["data"]]
                        cities_list.insert(0, "")
                        city_selected = st.sidebar.selectbox("Select a city", options=cities_list)
                        if city_selected:
                            # Get coordinates for the selected city (assume coordinates are available)
                            city_coords = [25.7617, -80.1918]  # Example coordinates, replace with actual coordinates
                            aqi_data = {
                                "location": {"coordinates": city_coords}
                            }
                            st.subheader(
                                f"Weather and Air Quality in {city_selected}, {state_selected}, {country_selected}")
                            map_creator(aqi_data["location"]["coordinates"][0], aqi_data["location"]["coordinates"][1])

                            # Fetch weather data
                            weather_data = get_weather_data(aqi_data["location"]["coordinates"][0],
                                                            aqi_data["location"]["coordinates"][1])

                            # Display weather data
                            display_weather_data(weather_data, st.session_state.unit)

                            # Display weekly temperatures as bar chart
                            display_weekly_temperatures(weather_data, st.session_state.unit)

                            # Display hourly weather as line chart
                            forecast_dates = [day["date"] for day in weather_data["forecast"]["forecastday"]]
                            selected_date = st.sidebar.selectbox("Select a date for hourly forecast", forecast_dates)

                            if selected_date:
                                display_hourly_forecast(weather_data, selected_date, st.session_state.unit)
                            else:
                                st.warning("No data available for the selected date.")
                    else:
                        st.warning("No cities available for this state.")
            else:
                st.warning("No states available for this country.")
        else:
            st.warning("Please select a country.")
    else:
        st.error("Failed to retrieve countries.")

elif category == "By Nearest City (IP Address)":
    url = f"https://api.airvisual.com/v2/nearest_city?key={air_quality_api_key}"
    aqi_data_dict = requests.get(url).json()
    if aqi_data_dict["status"] == "success":
        aqi_data = aqi_data_dict["data"]
        st.subheader("Weather and Air Quality at Your Location")
        st.write(f"**City:** {aqi_data['city']}")
        map_creator(aqi_data["location"]["coordinates"][1], aqi_data["location"]["coordinates"][0])

        # Fetch weather data
        weather_data = get_weather_data(aqi_data["location"]["coordinates"][1],
                                        aqi_data["location"]["coordinates"][0])

        # Display weather data
        display_weather_data(weather_data, st.session_state.unit)

        # Display weekly temperatures as bar chart
        display_weekly_temperatures(weather_data, st.session_state.unit)

        # Display hourly weather as line chart
        forecast_dates = [day["date"] for day in weather_data["forecast"]["forecastday"]]
        selected_date = st.sidebar.selectbox("Select a date for hourly forecast", forecast_dates)

        if selected_date:
            display_hourly_forecast(weather_data, selected_date, st.session_state.unit)
        else:
            st.warning("No data available for the selected date.")
    else:
        st.error("Failed to retrieve nearest city data.")

elif category == "By Latitude and Longitude":
    latitude = st.sidebar.number_input("Enter Latitude", -90.0, 90.0, 0.0)
    longitude = st.sidebar.number_input("Enter Longitude", -180.0, 180.0, 0.0)

    if latitude and longitude:
        aqi_data = {
            "location": {"coordinates": [latitude, longitude]}
        }
        st.subheader("Weather and Air Quality at Coordinates")
        map_creator(aqi_data["location"]["coordinates"][0], aqi_data["location"]["coordinates"][1])

        # Fetch weather data
        weather_data = get_weather_data(aqi_data["location"]["coordinates"][0],
                                        aqi_data["location"]["coordinates"][1])

        # Display weather data
        display_weather_data(weather_data, st.session_state.unit)

        # Display weekly temperatures as bar chart
        display_weekly_temperatures(weather_data, st.session_state.unit)

        # Display hourly weather as line chart
        forecast_dates = [day["date"] for day in weather_data["forecast"]["forecastday"]]
        selected_date = st.sidebar.selectbox("Select a date for hourly forecast", forecast_dates)

        if selected_date:
            display_hourly_forecast(weather_data, selected_date, st.session_state.unit)
        else:
            st.warning("No data available for the selected date.")
    else:
        st.warning("Please enter valid latitude and longitude.")

# Checkbox for additional information
if st.checkbox("Show More Information"):
    st.info("This application provides weather and air quality information based on the selected criteria. " 
            "You can choose to view data by city, state, and country, by your nearest city based on IP address, "
            "or by entering latitude and longitude coordinates. Use the sidebar to select your preferred options and units.")
