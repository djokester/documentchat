import openai
import requests
from bs4 import BeautifulSoup
import plotly.express as px
import math
import json

def fetch_documentation(plot_type):
    """
    Fetches the documentation for a given plot type from Plotly's Python API reference.

    Parameters:
    - plot_type: The type of plot for which to fetch documentation.

    Returns:
    - A tuple containing the documentation text and the blockquote text.
    """
    # URL of the page to scrape
    url = f'https://plotly.com/python-api-reference/generated/plotly.express.{plot_type}.html'

    # Fetch the webpage
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content of the page using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the <blockquote> tag and extract its text
        blockquote = soup.find('blockquote')
        blockquote_text = blockquote.text.strip() if blockquote else "No blockquote found"

        # Remove the <blockquote> from the document
        if blockquote:
            blockquote.decompose()

        # Find all the <dd> tags where the documentation is contained after removing <blockquote>
        documentation_tags = soup.find_all('dd')

        # Extract and print the text from each <dd> tag
        documentation_text = "\n\n".join([doc.text.strip() for doc in documentation_tags])

        return documentation_text, blockquote_text
    else:
        return f"Failed to retrieve the page. Status code: {response.status_code}", "No blockquote found"

def trim_documentation(documentation, client):
    """
    Trims the documentation text to under 6000 tokens without compromising key information.

    Parameters:
    - documentation: The full documentation text.
    - client: The OpenAI client for generating the trimmed documentation.

    Returns:
    - The trimmed documentation text.
    """
    system_prompt = (
        "Summarize this Documentation to be under 6000 tokens without compromising on information available. "
        "Do not send any other additional information or context. Remove the dataframe parameter."
    )

    user_message = f"Documentation: {documentation}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    chat_completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0
    )

    return chat_completion.choices[0].message.content

def get_token_count(prompt):
    """
    Estimates the token count for a given prompt.

    Parameters:
    - prompt: The input text prompt.

    Returns:
    - The estimated token count.
    """
    return sum([math.ceil(len(item) / 4) for item in prompt.split()])

def get_data_visualisation(data, viz, client, st):
    """
    Generates a Plotly visualization based on a dataframe and Plotly documentation.

    Parameters:
    - data: The dataframe to visualize.
    - viz: An object containing the visualization method and type.
    - client: The OpenAI client for generating visualization arguments.

    Returns:
    - A Plotly visualization.
    """
    documentation, _ = fetch_documentation(viz.Method)

    system_prompt = (
        "You are given a dataframe and documentation for a chart function. "
        "Your task is to return a JSON object that can be loaded as a dictionary and used directly "
        "as keyword arguments for the function without any modifications. "
        "Focus only on arguments that can be single values (i.e., strings, numbers, boolean). "
        "When an argument accepts a Pandas Series, use the name of the column in the dataframe. "
        "Do not send back the key-value pair for the data_frame argument."
    )

    user_message = (
        f"DataFrame Top 20 Rows: {data.head(20).to_string()}, "
        f"Data Description: {data.describe().to_string()}, "
        f"Visualization: {viz.Type}, "
        f"Documentation: {documentation}"
    )

    token_limit = get_token_count(system_prompt + user_message)
    if token_limit > 6000:
        documentation = trim_documentation(documentation, client)
        user_message = (
            f"DataFrame Top 20 Rows: {data.head(20).to_string()}, "
            f"Data Description: {data.describe().to_string()}, "
            f"Visualization: {viz.Type}, "
            f"Documentation: {documentation}"
        )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    chat_completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        response_format={
            "type": "json_object"
        },
        temperature=0
    )

    try:
        plot_function = getattr(px, viz.Method, None)
        return plot_function(data, **json.loads(chat_completion.choices[0].message.content))

    except Exception as e:
        # Handle exceptions and attempt to correct the arguments
        error_message = (
            f"This generated the following Exception: {str(e)}. "
            "Can you please return just the corrected keyword arguments JSON."
        )

        messages.append({"role": "assistant", "content": chat_completion.choices[0].message.content})
        messages.append({"role": "user", "content": error_message})

        chat_completion = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            response_format={
                "type": "json_object"
            },
            temperature=0
        )

        return getattr(px, viz.Method, None)(data, **json.loads(chat_completion.choices[0].message.content))
