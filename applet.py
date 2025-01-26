import streamlit as st
import pandas as pd
from io import StringIO
from visualization import potential_data_visualisation
from data_extraction_openai import get_data
from data_correction import get_datetime_columns, convert_string_columns
from explanation import get_explanation
import duckdb
import os
from openai import OpenAI
from data_visualisation_openai import get_data_visualisation
from data_forecast import potential_timeseries_forecasting, identify_timeseries_datetime_column, iterative_forecasting, is_forecast_request

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# DuckDB Connection
def get_duckdb_connection():
    if "duckdb_con" not in st.session_state:
        st.session_state.duckdb_con = duckdb.connect()
    return st.session_state.duckdb_con

def create_metadata(df):
    return df.head().to_string()

# Streamlit app
def main():
    st.title("InsightSense: Deep Dive into your Data")

    # Initialize session state for dataframe and metadata
    if "df" not in st.session_state:
        st.session_state.df = None
    if "metadata" not in st.session_state:
        st.session_state.metadata = None
    if "forecast_df" not in st.session_state:
        st.session_state.forecast_df = None

    uploaded_file = st.file_uploader("Upload a CSV file", type="csv")

    if uploaded_file is not None:
        if st.session_state.df is None:  # Load and clean the dataframe only once
            df = pd.read_csv(uploaded_file)
            datetime_cols = get_datetime_columns(df.head(), client)
            print(datetime_cols, 'main')
            df = convert_string_columns(df, datetime_cols)
            st.session_state.df = df
            st.session_state.metadata = create_metadata(df)

        # Re-register dataframe to DuckDB
        con = get_duckdb_connection()
        con.register('dataframe', st.session_state.df)

        
        st.write("Uploaded Data")
        st.write(st.session_state.df)

        forecasting_flag = potential_timeseries_forecasting(st.session_state.metadata, client)
        if forecasting_flag:
            if st.session_state.forecast_df is None:  # Load and clean the dataframe only once
                timestamp_column = identify_timeseries_datetime_column(st.session_state.metadata, client)
                forecast_df = iterative_forecasting(st.session_state.df, timestamp_column, client)
                st.session_state.forecast_df = forecast_df
            st.write(st.session_state.forecast_df)
            con.register('forecast_dataframe', st.session_state.forecast_df)
        
    # User query input
    user_query = st.text_input("Ask questions about your data")

    if st.button("Get Answer!"):
        if st.session_state.df is not None and user_query:
            # Re-register the dataframe again to ensure persistence
            con = get_duckdb_connection()
            con.register('dataframe', st.session_state.df)
            con.register('forecast_dataframe', st.session_state.forecast_df)
            forecast_request = is_forecast_request(user_query, client)
            if forecasting_flag and forecast_request:
                forecasting = True
            else:
                forecasting = False
            # Generate response
            visualisation = potential_data_visualisation(user_query, st.session_state, forecasting, client)
            data = get_data(visualisation, user_query, st.session_state, forecasting, client, con)
            st.write("Response:")
            st.write(data)
            st.write(get_explanation(user_query, st.session_state, client, data).explanation)
            
            print(visualisation)
            if visualisation is not None:
                visualisation_figure = get_data_visualisation(data, visualisation, client, st)
                st.plotly_chart(visualisation_figure)

        else:
            st.write("Please upload a file and ask a question.")

if __name__ == "__main__":
    main()
