import pandas as pd
import numpy as np
import streamlit as st
import requests

# Title of the app
st.title("Player Involvement")

# Function to load data once per session
@st.cache_data
def load_data():
    file_url = "https://github.com/LeScott2406/StatsApp/raw/refs/heads/main/updated_player_stats.xlsx"
    response = requests.get(file_url)
    with open("/tmp/updated_player_stats.xlsx", "wb") as f:
        f.write(response.content)
    player_stats_df = pd.read_excel("/tmp/updated_player_stats.xlsx")
    return player_stats_df

# Load data and store it in session state
if "player_stats_df" not in st.session_state:
    st.session_state.player_stats_df = load_data()

player_stats_df = st.session_state.player_stats_df

# List of metrics for calculations
metrics = [
    "OBV", "Key Passes", "Shots", "xG", "Ball Recoveries",
    "Opposition Half Ball Recoveries", "Deep Completions",
    "Open Play Final Third Passes", "xGBuildup",
    "Defensive Action OBV", "Dribble & Carry OBV",
    "Pass OBV", "Shot OBV"
]

# Calculate Team Totals & Contribution %
for metric in metrics:
    if metric in player_stats_df.columns:
        player_stats_df[f"Team {metric}"] = player_stats_df.groupby("Team")[metric].transform("sum")
        player_stats_df[f"{metric} Contribution"] = (player_stats_df[metric] / player_stats_df[f"Team {metric}"]) * 100
        player_stats_df[f"{metric} Contribution"] = player_stats_df[f"{metric} Contribution"].round(2)  # Keep as float

# Sidebar Filters
st.sidebar.header("Filters")

# Age slider
age_min, age_max = st.sidebar.slider("Age Range", 15, 35, (15, 35), 1)

# Usage slider
usage_min, usage_max = st.sidebar.slider("Usage Range", 0, 140, (0, 140), 1)

# Primary Position multi-select dropdown
primary_positions = ['All'] + player_stats_df['Primary Position'].unique().tolist()
selected_primary_positions = st.sidebar.multiselect("Primary Position", primary_positions)

# Competition multi-select dropdown
competitions = ['All'] + player_stats_df['Competition'].unique().tolist()
selected_competitions = st.sidebar.multiselect("Competition", competitions)

# Team multi-select dropdown
if selected_competitions:
    if "All" in selected_competitions:
        teams = ['All'] + player_stats_df['Team'].unique().tolist()
    else:
        teams = ['All'] + player_stats_df[player_stats_df['Competition'].isin(selected_competitions)]['Team'].unique().tolist()
else:
    teams = ['All']

selected_teams = st.sidebar.multiselect("Team", teams)

# Round 'Minutes Played' column
if 'Minutes Played' in player_stats_df.columns:
    player_stats_df['Minutes Played'] = player_stats_df['Minutes Played'].round(0)

# Calculate Available Minutes and Usage
if 'Matches' in player_stats_df.columns:
    player_stats_df['Available Minutes'] = player_stats_df['Matches'] * 90
    if 'Minutes Played' in player_stats_df.columns:
        player_stats_df['Usage'] = ((player_stats_df['Minutes Played'] / player_stats_df['Available Minutes']) * 100).round(2)

# Filter based on user selections
filtered_df = player_stats_df[
    (player_stats_df['Age'] >= age_min) & (player_stats_df['Age'] <= age_max) &
    (player_stats_df['Usage'] >= usage_min) & (player_stats_df['Usage'] <= usage_max)
]

# Filter by Primary Position
if selected_primary_positions and "All" not in selected_primary_positions:
    filtered_df = filtered_df[filtered_df['Primary Position'].isin(selected_primary_positions)]

# Filter by Competition
if selected_competitions and "All" not in selected_competitions:
    filtered_df = filtered_df[filtered_df['Competition'].isin(selected_competitions)]

# Filter by Team
if selected_teams and "All" not in selected_teams:
    filtered_df = filtered_df[filtered_df['Team'].isin(selected_teams)]

# Define columns to display
display_columns = ['Name', 'Team', 'Age', 'Primary Position', 'Usage'] + [f"{metric} Contribution" for metric in metrics]

# Ensure only available columns are displayed
available_columns = [col for col in display_columns if col in filtered_df.columns]
filtered_df = filtered_df[available_columns]

# Display the filtered DataFrame with correctly formatted numeric values
st.write("Filtered Player Stats:")
st.dataframe(
    filtered_df.style.format({col: "{:.2f}%" for col in available_columns if "Contribution" in col})
)

# Option to download the filtered data as an Excel file
output_path = "/tmp/filtered_player_stats.xlsx"
filtered_df.to_excel(output_path, index=False)
st.download_button(
    label="Download Filtered Stats",
    data=open(output_path, "rb").read(),
    file_name="filtered_player_stats.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
