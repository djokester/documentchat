import pandas as pd
import json

def get_datetime_columns(metadata, client):
    """
    Determines which columns in a dataframe should be of type datetime
    and returns a dictionary with the column names as keys and their respective datetime formats as values.

    Parameters:
    - dataframe (pd.DataFrame): The input dataframe.
    - client: The OpenAI client object.

    Returns:
    - dict: A dictionary where keys are column names and values are the inferred datetime formats.
    """
    # Extract metadata: column names and their first few non-null values    
    # OpenAI system prompt
    system_prompt = (
        "Given the metadata of a dataframe (column names and their sample values), identify which columns "
        "are most likely to represent datetime data like time, date, day, month and year and the strftime format codes of the datetime values. "
        "Return the result in JSON format as follows: "
        "{\"datetime_columns\": [{\"column_name\": \"datetime_format\"}}, {\"column_name\": \"datetime_format\"}}]"
        "where 'datetime_format' is the strftime format codes for parsing the datetime values in the column."
    )

    # Call the OpenAI client
    try:
        chat_completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Metadata: {metadata}"}
            ],
            response_format=
            {
            "type": "json_schema",
            "json_schema": {
                "name": "datetime_columns",
                "schema": {
                    "type": "object",
                    "properties": {
                    "columns": {
                        "type": "array",
                        "description": "A collection of columns  most likely to represent datetime data defined by their name and format.",
                        "items": {
                        "type": "object",
                        "properties": {
                            "column_name": {
                            "type": "string",
                            "description": "The name of the datetime column."
                            },
                            "datetime_format": {
                            "type": "string",
                            "description": "The  strftime format codes of the datetime for this column."
                            }
                        },
                        "required": [
                            "column_name",
                            "datetime_format"
                        ],
                        "additionalProperties": False
                        }
                    }
                    },
                    "required": [
                    "columns"
                    ],
                    "additionalProperties": False
                },
                "strict": True
                }
        },
                
                    
            temperature=0,
            max_completion_tokens=2048,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        result = json.loads(chat_completion.choices[0].message.content)
        print(result)
        
        # Parse and return the dictionary of datetime columns with formats
        return result["columns"]

    except Exception as e:
        print(f"Error processing the response: {e}")
        return {}


def convert_string_columns(
    df: pd.DataFrame, 
    datetime_columns: list = None,
    threshold: float = 0.8, 
) -> pd.DataFrame:
    """
    Converts string columns in a DataFrame to the most appropriate type 
    (int, float, datetime, bool, or valid JSON strings), with the ability 
    to specify columns to be directly treated as datetime.
    
    Parameters:
    - df: pd.DataFrame - The input DataFrame with all columns as strings.
    - threshold: float - The minimum proportion of valid conversions required to change a column's type.
    - datetime_columns: list - List of column names to be directly converted to datetime.
    
    Returns:
    - pd.DataFrame - The DataFrame with converted columns.
    """
    datetime_columns = datetime_columns or []
    print(datetime_columns)
    for column in df.columns:
        # Directly convert specified datetime columns
        datetime_column_names = [item["column_name"] for item in datetime_columns]
        datetime_columns_dict = {item["column_name"]: item["datetime_format"] for item in datetime_columns}
        if column in datetime_column_names:
            try:
                df[column] = pd.to_datetime(df[column], errors='coerce', format=datetime_columns_dict[column])
                print(f"Column {column} directly converted to datetime")
            except Exception as e:
                print(f"Column {column} could not be converted to datetime: {e}")
            continue  # Skip further checks for this column
        
        conversion_success = {}
        
        # Attempt integer conversion
        try:
            temp = pd.to_numeric(df[column], errors='coerce', downcast='integer')
            success_rate = temp.notna().mean()
            conversion_success['integer'] = (success_rate, temp)
        except Exception:
            conversion_success['integer'] = (0, None)
        
        # Attempt float conversion
        try:
            temp = pd.to_numeric(df[column], errors='coerce', downcast='float')
            success_rate = temp.notna().mean()
            conversion_success['float'] = (success_rate, temp)
        except Exception:
            conversion_success['float'] = (0, None)
        
        # Attempt boolean conversion
        try:
            truthy_falsy_map = {'true': True, 'false': False, '1': True, '0': False, 'yes': True, 'no': False}
            temp = df[column].str.strip().str.lower().map(truthy_falsy_map)
            success_rate = temp.notna().mean()
            conversion_success['boolean'] = (success_rate, temp.fillna(False).astype(bool))
        except Exception:
            conversion_success['boolean'] = (0, None)
        
        # Attempt JSON conversion (ensure valid JSON strings)
        try:
            def to_json_string(x):
                try:
                    x = x.replace("'", '"')  # Replace single quotes with double quotes
                    json.loads(x)  # Validate JSON structure
                    return x  # Return as a valid JSON string
                except Exception:
                    return None  # If invalid JSON, return None
            
            temp = df[column].apply(lambda x: to_json_string(x) if pd.notna(x) else None)
            success_rate = temp.notna().mean()
            conversion_success['json_string'] = (success_rate, temp)
        except Exception:
            conversion_success['json_string'] = (0, None)
        
        # Identify the best conversion based on the threshold
        best_conversion = max(conversion_success.items(), key=lambda x: x[1][0])
        if best_conversion[1][0] >= threshold:  # If success rate meets the threshold
            df[column] = best_conversion[1][1]
            print(f"Column {column} converted to {best_conversion[0]}")
        else:
            print(f"Column {column} could not be reliably converted and remains as string")
    
    return df
