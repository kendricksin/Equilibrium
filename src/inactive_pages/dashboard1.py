import streamlit as st
import pandas as pd
import plotly.express as px
from inactive_pages.filters import get_filtered_data
import matplotlib.pyplot as plt

def load_dashboards(get_db_connection, filters):
    st.title("Project Dashboards")

    # Get the filtered data based on the current filters
    df = get_filtered_data(get_db_connection(), filters)

    # Generate dashboards based on the filtered data
    generate_dashboard(df)

def generate_dashboard(df):
    st.title("Project Analysis Dashboard")

    # Prepare the data
    df['year'] = pd.to_datetime(df['transaction_date']).dt.year
    df = df.groupby('year').agg({
        'sum_price_agree': 'sum',
        'project_id': 'count'
    }).reset_index()
    df = df[df['year'] >= 2019]

    # Create the combo plot using Matplotlib
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Bar chart
    bars = ax1.bar(df['year'], df['sum_price_agree'] / 1e6, color='blue')
    ax1.set_xlabel('Year')
    ax1.set_xlim([2019, 2024])
    ax1.set_ylabel('Sum of Sum_Price_Agree (Million THB)', color='blue')
    ax1.tick_params('y', colors='blue')

    # Annotate bars with values
    for bar in bars:
        height = bar.get_height()
        ax1.annotate(f'{height:.2f} MB',
                     xy=(bar.get_x() + bar.get_width() / 2, height),
                     xytext=(0, 3),  # 3 points vertical offset
                     textcoords="offset points",
                     ha='center', va='bottom')

    # Line chart on secondary y-axis
    ax2 = ax1.twinx()
    line, = ax2.plot(df['year'], df['project_id'], color='red')
    ax2.set_ylabel('Number of Projects', color='red')
    ax2.tick_params('y', colors='red')

    # Annotate line plot points
    for x, y in zip(df['year'], df['project_id']):
        ax2.annotate(str(y), xy=(x, y), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom')

    plt.title('Project Analysis Dashboard')
    st.pyplot(fig)