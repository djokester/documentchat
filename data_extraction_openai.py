import openai
import re

def clean_query(text: str) -> str:
    """
    Extracts the SQL query from a string by removing 'sql' tags, triple backticks, 
    and any other unwanted prefixes, ensuring no leftover SQL formatting remains.
    """
    # Remove 'sql' or similar tags, triple backticks, and empty lines
    clean_text = re.sub(r"^.*?sql\s*\n", "", text, flags=re.IGNORECASE | re.DOTALL)
    clean_text = re.sub(r"```", "", clean_text.strip())
    return clean_text.strip()

def get_data(viz, user_input, metadata, client, connectdf):
    """
    Generates and executes an SQL query for a data visualization with up to three retries.

    Parameters:
    - viz: The type of visualization requested.
    - user_input: The user's prompt for the visualization.
    - metadata: Retrieved metadata or schema information.
    - client: The OpenAI client for generating queries.
    - connectdf: A database connection object supporting execute().

    Returns:
    - A DataFrame containing the query result.
    """
    system_prompt = (
        "Given the prompt, the head of a dataframe below, and the form of a data visualization, "
        "can you write an SQL query for the dataframe that would return the data needed for visualization? "
        "Your response needs to be just the SQL query with no other comments or information "
        "so as to facilitate direct usage of your response. Avoid any backtick formatting. Just the SQL query. "
        "Please remember that your SQL queries will be executed in DuckDB and as such should be supported by DuckDB."
    )

    attempt_count = 0
    previous_responses = []
    previous_errors = []

    while attempt_count < 3:
        attempt_count += 1
        try:
            # Initial message setup
            if attempt_count == 1:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Data Visualization: {viz}\nPrompt: `{user_input}`\nRetrieved Context: `{metadata}`\nTable Name: \"dataframe\""}
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
                    {"role": "user", "content": (
                        f"Data Visualization: {viz}\nPrompt: `{user_input}`\nRetrieved Context: `{metadata}`\nTable Name: \"dataframe\"\n"
                        f"Previous Responses:\n{assistant_history}\n\n"
                        f"Errors Encountered:\n{error_history}\n\n"
                        f"Please correct the query and return a valid SQL query supported by DuckDB."
                    )}
                ]

            print(f"ATTEMPT {attempt_count}")

            # Generate SQL query using GPT-4
            print(messages[1:])
            chat_completion = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0
            )

            sql_query = clean_query(chat_completion.choices[0].message.content)
            print(f"Generated Query (Attempt {attempt_count}):\n{sql_query}")
            previous_responses.append(sql_query)

            # Execute the query
            return connectdf.execute(sql_query).fetchdf()

        except Exception as e:
            print(f"Error (Attempt {attempt_count}): {str(e)}")
            previous_errors.append(str(e))

            if attempt_count == 3:
                print("Maximum retries reached.")
                import pdb; pdb.set_trace()

                raise Exception(f"Final Exception: {str(e)}")
