import pandas as pd
import streamlit as st
from typing import (
    Any,
    Set,
)
import pydeck as pdk
import plotly.express as px
import json
from collections import defaultdict
import plotly.graph_objects as go

state_to_code = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
    "District of Columbia": "DC",
    "American Samoa": "AS",
    "Guam": "GU",
    "Northern Mariana Islands": "MP",
    "Puerto Rico": "PR",
    "United States Minor Outlying Islands": "UM",
    "U.S. Virgin Islands": "VI",
}


def draw_barplot():
    df = pd.read_csv('shootings_with_geocode.csv')
    state_to_shooting_case = defaultdict(dict)
    for _, row in df.iterrows():
        state, race = row['state'], row['race']
        state_to_shooting_case[state][race] = state_to_shooting_case[state].get(race, 0) + 1
    shooting_case = []
    for state, d in state_to_shooting_case.items():
        for race, count in d.items():
            shooting_case.append([state, race, count])


    states = sorted(list(state_to_shooting_case.keys()))
    races = set([i for [i] in df[['race']].values])
    colors = ['#003f5c', '#444e86', '#955196', '#dd5182', '#ff6e54', '#ffa600']
    fig = go.Figure()

    for color, race in zip(colors, races):
        fig.add_trace(go.Bar(
            x=states,
            y=[state_to_shooting_case[state].get(race, 0) for state in states],
            name=race,
            marker_color=color
        ))

    # Here we modify the tickangle of the xaxis, resulting in rotated labels.
    fig.update_layout(barmode='group', xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=False)

def draw_map() -> None:
    shootings_df = pd.read_csv("shootings_with_geocode.csv")
    st.sidebar.title("What shooting data you want to observe?")
    selected_race = st.sidebar.radio(
        "Select race",
        ('White', 'Black', 'Asian', 'Hispanic'))
    selected_armed = st.sidebar.radio(
        "Select armed type",
        ('Armed', 'Unarmed', 'Unknown', 'Both'), index=3)

    st.sidebar.title("Notes for bias ratio")
    st.sidebar.write("lighter color -> higher bias ratio -> higher possibility of racism against selected race at this state")

    if selected_armed == 'Armed':
        shootings_df = shootings_df[shootings_df['armed'] != 'unarmed']
    elif selected_armed == 'Unarmed':
        shootings_df = shootings_df[shootings_df['armed'] == 'unarmed']
    elif selected_armed == 'Unknown':
        shootings_df = shootings_df[shootings_df['armed'] == 'unknown']

    # Scatter
    fig = px.scatter_mapbox(shootings_df[shootings_df['race'] == selected_race],
                            lat="latitude",
                            lon="longitude",
                            hover_name="name",
                            hover_data=["state", "city", "armed", "age", "gender", "signs_of_mental_illness","threat_level"],
                            color_discrete_sequence=["red"],
                            zoom=3, center={"lat": 37.0902, "lon": -95.7129},
                            height=600,
                            width=800)
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    # Choropleth
    state_geodata = open('state_geodata.json')
    states = json.load(state_geodata)

    for i in states['features']:
        i['id'] = i['properties']['name']
    races_df = pd.read_csv("races.csv", dtype={"white": str})
    complete_shootings_df = pd.read_csv("shootings_with_geocode.csv")

    def get_shooting_percentage(race: str, state_code: str) -> float:
        complete_state_df = complete_shootings_df[complete_shootings_df['state'] == state_code]
        state_df = shootings_df[shootings_df['state'] == state_code]
        count_df = state_df[state_df['race'] == race]

        if state_df.shape[0] == 0:
            return 0

        shot_percentage = count_df.shape[0] / complete_state_df.shape[0]
        population_percentage = races_df[races_df['State Code'] == state_code][race].values[0]
        return shot_percentage / population_percentage

    # Calculate shooting_percentage / population_percentage
    percentage_list = []

    for _, row in races_df.iterrows():
        percentage_list.append([row['State'], get_shooting_percentage(selected_race, row['State Code'])])
    curr_df = pd.DataFrame(data=percentage_list, columns=['State', selected_race])

    fig2 = px.choropleth_mapbox(curr_df, geojson=states, locations='State', color=selected_race,
                                color_continuous_scale="agsunset",
                                range_color=(0, 5),
                                mapbox_style="carto-positron",
                                zoom=3, center={"lat": 37.0902, "lon": -95.7129},
                                opacity=0.5,
                                labels={selected_race: 'bias_ratio'}
                                )
    # fig2.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    # fig.add_trace(fig2.data[0])
    # st.plotly_chart(fig, use_container_width=False)
    fig2.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig2.add_trace(fig.data[0])
    st.plotly_chart(fig2, use_container_width=False)
    

# Title
st.set_page_config(page_title='Police Shooting')
st.title('Data Visualization of US Police Shooting')
st.header('Does US Police Shooting reflect racism?')
st.write('Made by Vanessa Yin (yuey4@andrew.cmu.edu) for 05839-Fall21 Assignment2')
'''
---
'''
# Data introduction
st.subheader('Introduction')
st.write('Our visualization is built on the US police shooting data from January 2015 to June 2020. ')
shootings_columns = pd.read_csv('shootings_with_geocode.csv').columns
st.write("Overview of data features:")
st.dataframe(shootings_columns[1:])
st.write('Data resource: https://www.kaggle.com/ahsen1330/us-police-shootings')
st.write('A naive approach to visualize such data is a barplot or pieplot to show the \
    count or percentage of people shot by police in each state, grouped by people’s races. \
    Such a design is not sufficient enough since we didn’t consider the fact that the race \
    population in each state can be very different. ')

st.write('Take an extreme example here: for people shot by police in Pennsylvania, \
    70% of them are white people and 30% of them are black people. If we only see \
    such a percentage, we may think there is no bias or racism against black people \
    at all. However, assume extremely that 95% of the population in Pennsylvania are \
    white and only 5% of the population are black. Then obviously a racism problem will be raised. ')

st.write('Therefore, we introduced a new measurement in our visualization: Bias ratio.')

# Formula
st.subheader('Bias ratio')

latex_formula = r'''
$$ 
\text{bias ratio of race R at state S} = \frac{\text{shooting percentage of people of race R at state S}}{\text{population percentage of people of race R at state S}} 
$$ 
NOTE: higher ratio has lighter color in the graph, and can roughly represent a higher possibility of racism against race R at state S.
'''
st.write(latex_formula)

# Visualization
st.subheader('Visualization')
st.write('How to use this graph?')
'''
* Each red point: one person shot by police at that city (location is city based).
* Color of each state: bias ratio (lighter color -> higher ratio -> higher possibility of racism against R at this state)
* Mouse over either the red point or the state to see a box pop up with further information.
* Choose the race of people shot you want to observe in the left sidebar (default = white).
* If you are interested in the armed type of people shot, choose the armed type in the left sidebar (default = both).
* Feel free to zoom in/out, move the map to see what you're curious about. Maybe Hawaii!
* Enjoy :)
'''
draw_map()
# draw_barplot()

# race_options2 = st.multiselect(
#     'Select races',
#     ['White', 'Black', 'Asian', 'Hispanic'],
#     key=2)

# if race_options2:
#     races_df = pd.read_csv("races.csv", dtype={"white": str})
#     fig = px.bar(races_df, x="State", y=race_options2, title="US race distribution")
#     st.plotly_chart(fig, use_container_width=True)
