from models import ForecastFlag, ForecastRequestFlag
import json
import pandas as pd

def is_forecast_request(prompt, client):
    """
    Determines if the provided prompt is asking for a forecast.

    Parameters:
    - prompt (str): The user input to analyze.
    - client: The client object for making chat completion requests.

    Returns:
    - bool: True if the prompt is asking for a forecast, False otherwise.
    """
    flag_format = "{\"forecast_request\": flag}"
    system_prompt = (
        "Analyze the given prompt and determine if it is requesting a forecast. "
        "A forecast request involves asking about predictions, future trends, or extrapolation of data. "
        "Focus solely on the intent of the prompt and ignore any associated data or metadata. "
        f"Your response needs to be in a JSON format: {flag_format}. "
        "`forecast_request` should be True if the prompt asks for a forecast; otherwise, it should be False."
    )

    chat_completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Prompt: `{prompt}`"}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "forecast_request_flag",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "forecast_request": {
                            "type": "boolean",
                            "description": "Indicates whether the prompt is requesting a forecast or not."
                        }
                    },
                    "required": [
                        "forecast_request"
                    ],
                    "additionalProperties": False
                }
            }
        },
        temperature=0,
        max_completion_tokens=2048,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    try:
        result = chat_completion.choices[0].message.content
        print(result)
        return ForecastRequestFlag.model_validate_json(result).forecast_request
    except Exception as e:
        return False


def potential_timeseries_forecasting(metadata, client):
    flag_format = "{\"forecasting_possible\": flag}"
    system_prompt = (
        f"Given the head of a dataframe below, can you determine if the data is suitable for time series forecasting? "
        "The decision should be based on whether the data represents a time series with a timestamp or similar time-related information and contains more than one data point for the same variable or entity over time. "
        "The assessment should consider the presence of temporal attributes and sufficient data points. "
        f"Your response needs to be in a JSON format: {flag_format}. `forecasting_possible` represents whether forecasting is possible or not with a boolean flag. "
        "True means that forecasting is possible; otherwise, forecasting_possible should be marked False."
        "The dataframe's head below is just to represent the nature of data available but should be sufficient to identify time series properties."
    )

    chat_completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Retrieved Context: `{metadata}`"}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "forecasting_flag",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "forecasting_possible": {
                            "type": "boolean",
                            "description": "Indicates whether time series forecasting is possible or not."
                        }
                    },
                    "required": [
                        "forecasting_possible"
                    ],
                    "additionalProperties": False
                }
            }
        },
        temperature=0,
        max_completion_tokens=2048,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    try:
        print(chat_completion.choices[0].message.content)
        return ForecastFlag.model_validate_json(chat_completion.choices[0].message.content).forecasting_possible
    except Exception as e:
        return False


def identify_timeseries_datetime_column(metadata, client):
    """
    Identifies the datetime column in a DataFrame suitable for time series forecasting.
    
    Parameters:
        df (pd.DataFrame): The input DataFrame.
        client: The OpenAI client instance.

    Returns:
        str: The name of the datetime column if identified, otherwise None.
    """
    # Extract the head of the dataframe to send as context
    system_prompt = (
        "Given the head of a dataframe below, identify which column represents the datetime or timestamp information "
        "suitable for time series forecasting. If no such column exists, respond with None. "
        "The column should have values representing time in a consistent and valid datetime format."
        "\n\nYour response should be a JSON object with the format:\n"
        "{ \"datetime_column\": column_name }\n"
        "where column_name is the name of the datetime column, or null if no such column exists."
    )

    # Prepare the chat completion request
    chat_completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Retrieved Context: `{metadata}`"}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "datetime_column_identifier",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "datetime_column": {
                            "type": ["string", "null"],
                            "description": "The name of the datetime column, or null if no such column exists."
                        }
                    },
                    "required": ["datetime_column"],
                    "additionalProperties": False
                }
            }
        },
        temperature=0,
        max_completion_tokens=2048,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    try:
        # Parse the response
        response_content = chat_completion.choices[0].message.content
        response_json = json.loads(response_content)

        # Return the identified column or None
        return response_json.get("datetime_column")
    except Exception as e:
        print(f"Error processing the response: {e}")
        return None


def iterative_forecasting(df, datetime_column, client):
    """
    Iteratively forecasts and stores results in a DataFrame.

    Parameters:
        df (pd.DataFrame): The input DataFrame containing the time series data.
        datetime_column (str): The name of the datetime column.
        client: The OpenAI client instance.

    Returns:
        pd.DataFrame: A DataFrame containing the forecasted results for each step.
    """
    # Ensure the DataFrame is sorted by the datetime column
    df[datetime_column] = pd.to_datetime(df[datetime_column])
    df.sort_values(by=datetime_column, inplace=True)

    # Calculate the time difference between the last two timestamps
    df.reset_index(drop=True, inplace=True)
    time_diff = df[datetime_column].iloc[-1] - df[datetime_column].iloc[-2]

    # Initialize a list to store forecasted results
    forecasts = []

    # Iteratively forecast
    for i in range(2, len(df) + 1):
        # Subset the DataFrame up to the current row
        subset = df.iloc[:i]
        
        # Define the target timestamp for the prediction
        if i == len(df):
            target_timestamp = df[datetime_column].iloc[-1] + time_diff
        else:
            target_timestamp = df[datetime_column].iloc[i]

        # Call the forecasting function
        try:
            forecast = get_forecast(subset, target_timestamp, datetime_column, client)
            forecast["forecast_time"] = target_timestamp
            forecasts.append(forecast)
        except Exception as e:
            print(f"Error during forecasting for timestamp {target_timestamp}: {e}")
            continue

    # Combine all forecasts into a single DataFrame
    print(forecasts)
    forecast_df = pd.concat(forecasts, ignore_index=True)
    return forecast_df


def get_forecast(df, timestamp,datetime_column, client):
    response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
        "role": "system",
        "content": [
            {
            "type": "text",
            "text": f"Given the dataframe please provide the forecast for {timestamp} in the format proviided. Use forecast_time for the forecast timestamp and drop  {datetime_column}"
            }
        ]
        },
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": df.to_json()
            }
        ]
        },
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {
        "name": "dataframe",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
            "data": {
                "type": "array",
                "description": "An array of objects representing rows in the dataframe.",
                "items": {
                "type": "object",
                "properties": {
                    "column_name": {
                    "type": "string",
                    "description": "The name of the column."
                    },
                    "value": {
                    "type": "string",
                    "description": "The value corresponding to the column name."
                    }
                },
                "required": [
                    "column_name",
                    "value"
                ],
                "additionalProperties": False
                }
            }
            },
            "required": [
            "data"
            ],
            "additionalProperties": False
        }
        }
    },
    temperature=1,
    max_completion_tokens=2048,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
    )
    data = json.loads(response.choices[0].message.content)
    df = pd.DataFrame(data["data"])
    df_pivoted = df.set_index('column_name').T
    df_pivoted.reset_index(drop=True, inplace=True)
    return df_pivoted

