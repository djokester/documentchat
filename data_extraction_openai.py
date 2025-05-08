import openai
import re
import json

def create_metadata(df):
    return df.head().to_string()

def clean_query(text: str) -> str:
    """
    Extracts the SQL query from a string by removing 'sql' tags, triple backticks, 
    and any other unwanted prefixes, ensuring no leftover SQL formatting remains.
    """
    # Remove 'sql' or similar tags, triple backticks, and empty lines
    clean_text = re.sub(r"^.*?sql\s*\n", "", text, flags=re.IGNORECASE | re.DOTALL)
    clean_text = re.sub(r"```", "", clean_text.strip())
    return clean_text.strip()

def get_data(viz, user_input, session_state, client, connectdf):
    """
    Generates and executes an SQL query (DuckDB) for the requested visualisation.
    Automatically detects whether a forecast table is available by reading
    `session_state.forecast` (True/False).

    Parameters
    ----------
    viz : str
        Visualisation type requested by the user.
    user_input : str
        Free‑form user prompt.
    session_state : streamlit.session_state
        Holds df / forecast_df / forecast flag.
    client : OpenAI
        OpenAI client used to draft the SQL.
    connectdf : duckdb.DuckDBPyConnection
        Connection on which the query will be executed.

    Returns
    -------
    pandas.DataFrame
        Result of the generated SQL query.
    """
    # 1) Detect whether forecasting is in play
    forecasting = bool(getattr(session_state, "forecast", False))

    # 2) Build metadata and system prompt accordingly
    if forecasting:
        md_main = create_metadata(session_state.df)
        md_fore = create_metadata(session_state.forecast_df)
        retrieved_context = (
            f"Main DataFrame Metadata:\n{md_main}\n\n"
            f"Forecast DataFrame Metadata:\n{md_fore}"
        )
        table_names = (
            "Table names: 'dataframe' (main dataset) and 'forecast_dataframe' "
            "(forecasted data)."
        )
        system_prompt = (
            "Given the prompt, the metadata of two dataframes below, and the "
            "desired form of a data visualisation, write a DuckDB‑compatible "
            "SQL query that returns the data needed. Use 'dataframe' for the "
            "main data and 'forecast_dataframe' for the forecast. "
            "Return *only* the query—no backticks, no commentary."
        )
    else:
        md_main = create_metadata(session_state.df)
        retrieved_context = f"Main DataFrame Metadata:\n{md_main}"
        table_names = "Table name: 'dataframe'."
        system_prompt = (
            "Given the prompt, the dataframe metadata below, and the desired "
            "visualisation, write a DuckDB‑compatible SQL query that returns "
            "the needed data. Return *only* the query—no backticks, no commentary."
        )

    # 3) Retry loop (max 5)
    attempts, prior_sql, prior_err = 0, [], []

    while attempts < 5:
        attempts += 1

        # Assemble messages
        if attempts == 1:
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"Visualisation: {viz}\n"
                        f"Prompt: {user_input}\n"
                        f"{retrieved_context}\n"
                        f"{table_names}"
                    ),
                },
            ]
        else:
            msg_prev = "\n\n".join(
                f"Attempt {i+1} SQL:\n{sql}" for i, sql in enumerate(prior_sql)
            )
            msg_err = "\n\n".join(
                f"Attempt {i+1} Error:\n{err}" for i, err in enumerate(prior_err)
            )
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"Visualisation: {viz}\n"
                        f"Prompt: {user_input}\n"
                        f"{retrieved_context}\n"
                        f"{table_names}\n\n"
                        f"Previous attempts:\n{msg_prev}\n\n"
                        f"Errors:\n{msg_err}\n\n"
                        "Please fix the query."
                    ),
                },
            ]

        # Call the model
        resp = client.chat.completions.create(
            model="gpt-4o",
            temperature=0,
            messages=messages,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "sql_query_schema",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "DuckDB SQL query.",
                            }
                        },
                        "required": ["query"],
                        "additionalProperties": False,
                    },
                    "strict": True,
                },
            },
        )

        sql_query = clean_query(json.loads(resp.choices[0].message.content)["query"])
        prior_sql.append(sql_query)

        try:
            return connectdf.execute(sql_query).fetchdf()
        except Exception as e:
            prior_err.append(str(e))
            if attempts >= 5:
                raise RuntimeError(f"Failed after 5 attempts: {e}")

