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

def get_data(viz, user_input, session_state, forecasting, client, connectdf):
    """
    Generates and executes an SQL query for a data visualization with up to three retries.

    Parameters:
    - viz: The type of visualization requested.
    - user_input: The user's prompt for the visualization.
    - session_state: An object containing the state, including dataframes and metadata.
    - client: The OpenAI client for generating queries.
    - connectdf: A database connection object supporting execute().
    - forecasting: A boolean indicating if forecasting-related data is included.

    Returns:
    - A DataFrame containing the query result.
    """
    # Create metadata based on the forecasting flag
    if forecasting:
        metadata_df = create_metadata(session_state.df)
        metadata_forecast_df = create_metadata(session_state.forecast_df)
        retrieved_context = (
            f"Main DataFrame Metadata:\n{metadata_df}\n\n"
            f"Forecast DataFrame Metadata:\n{metadata_forecast_df}"
        )
        table_names = "Table Names: 'dataframe' (main dataset), 'forecast_dataframe' (forecasted data)"
        system_prompt = (
            "Given the prompt, the metadata of two dataframes below, and the form of a data visualization, "
            "can you write an SQL query that joins or uses both dataframes to produce the data required for visualization? "
            "'dataframe' represents the main dataset, while 'forecast_dataframe' represents data derived from forecasting. "
            "Your response should be a valid DuckDB SQL query. Avoid any backtick formatting. "
            "Please ensure the query is executable and returns the desired output for visualization."
        )
    else:
        metadata_df = create_metadata(session_state.df)
        retrieved_context = f"Main DataFrame Metadata:\n{metadata_df}"
        table_names = "Table Name: 'dataframe'"
        system_prompt = (
            "Given the prompt, the metadata of a dataframe below, and the form of a data visualization, "
            "can you write an SQL query for the dataframe that would return the data needed for visualization? "
            "Your response should be a valid DuckDB SQL query. Avoid any backtick formatting. "
            "Please ensure the query is executable and returns the desired output for visualization."
        )

    attempt_count = 0
    previous_responses = []
    previous_errors = []

    while attempt_count < 5:
        attempt_count += 1
        try:
            # Initial message setup
            if attempt_count == 1:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": (
                            f"Data Visualization: {viz}\nPrompt: `{user_input}`\nRetrieved Context: `{retrieved_context}`\n{table_names}"
                        ),
                    },
                ]
            else:
                # On subsequent retries, include all previous attempts and errors
                assistant_history = "\n\n".join(
                    [f"Attempt {i+1} Response:\n{response}" for i, response in enumerate(previous_responses)]
                )
                error_history = "\n\n".join(
                    [f"Attempt {i+1} Error:\n{error}" for i, error in enumerate(previous_errors)]
                )
                messages = [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": (
                            f"Data Visualization: {viz}\nPrompt: `{user_input}`\nRetrieved Context: `{retrieved_context}`\n{table_names}\n"
                            f"Previous Responses:\n{assistant_history}\n\n"
                            f"Errors Encountered:\n{error_history}\n\n"
                            f"Please correct the query and return a valid SQL query supported by DuckDB."
                        ),
                    },
                ]

            print(f"ATTEMPT {attempt_count}")

            # Generate SQL query using GPT-4
            chat_completion = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "sql_query_schema",
                        "schema": {
                            "type": "object",
                            "properties": {
                            "query": {
                                "type": "string",
                                "description": "The SQL query string used to retrieve or manipulate data."
                            }
                            },
                            "required": [
                            "query"
                            ],
                            "additionalProperties": False
                        },
                        "strict": True
                        }
                                        },
            )
            sql_query = clean_query(json.loads(chat_completion.choices[0].message.content)["query"])
            print(f"Generated Query (Attempt {attempt_count}):\n{sql_query}")
            previous_responses.append(sql_query)

            # Execute the query
            return connectdf.execute(sql_query).fetchdf()

        except Exception as e:
            print(f"Error (Attempt {attempt_count}): {str(e)}")
            previous_errors.append(str(e))

            if attempt_count == 3:
                print("Maximum retries reached.")
                raise Exception(f"Final Exception: {str(e)}")