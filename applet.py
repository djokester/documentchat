import streamlit as st
import pandas as pd
from io import StringIO
from visualization import potential_data_visualisation
from data_extraction_openai import get_data
from data_correction import get_datetime_columns, convert_string_columns
from explanation import get_explanation
import duckdb, os
from openai import OpenAI
from data_visualisation_openai import get_data_visualisation

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# DuckDB Connection
def get_duckdb_connection():
    if "duckdb_con" not in st.session_state:
        st.session_state.duckdb_con = duckdb.connect()
    return st.session_state.duckdb_con

def create_metadata(df):
    return df.head().to_string()

# ────────────────────────────────────────────────────────────────────────
def main():
    st.title("InsightSense: Deep Dive into your Data")

    if "df" not in st.session_state:
        st.session_state.df = None
    if "metadata" not in st.session_state:
        st.session_state.metadata = None

    uploaded = st.file_uploader("Upload a CSV file", type="csv")
    if uploaded is not None:
        if st.session_state.df is None:           # first load only
            df = pd.read_csv(uploaded)
            dt_cols = get_datetime_columns(df.head(), client)
            df = convert_string_columns(df, dt_cols)
            st.session_state.df = df
            st.session_state.metadata = create_metadata(df)

        con = get_duckdb_connection()
        con.register("dataframe", st.session_state.df)

        st.subheader("Uploaded Data")
        st.write(st.session_state.df)

    # ── user query ───────────────────────────────────────────────────────
    user_query = st.text_input("Ask questions about your data")

    if st.button("Get Answer!") and st.session_state.df is not None and user_query:
        con = get_duckdb_connection()
        con.register("dataframe", st.session_state.df)

        visualisation = potential_data_visualisation(
            user_query, st.session_state, client
        )
        data = get_data(
            visualisation, user_query, st.session_state, client, con
        )

        st.subheader("Response")
        st.write(data)
        st.write(get_explanation(user_query, st.session_state, client, data).explanation)

        if visualisation is not None:
            fig = get_data_visualisation(data, visualisation, client, st)
            st.plotly_chart(fig)
    elif uploaded is None:
        st.write("Please upload a CSV file first.")

if __name__ == "__main__":
    main()
