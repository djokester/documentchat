from models import ForecastFlag, ForecastRequestFlag
import json
import pandas as pd
from collections import deque
import tiktoken  
import time
from stqdm import stqdm

enc = tiktoken.encoding_for_model("gpt-4o")

def tokens_in_text(txt: str) -> int:
    return len(enc.encode(txt))

def tokens_in_messages(messages) -> int:
    """Count GPT token cost for a list-of-dict messages."""
    # gpt-4o uses the standard chat format cost formula (© OpenAI docs)
    TOK_PER_MSG  = 3
    TOK_PER_NAME = 1
    total = 0
    for m in messages:
        total += TOK_PER_MSG
        for k, v in m.items():
            total += tokens_in_text(v)
            if k == "name":
                total += TOK_PER_NAME
    total += 3  #  every reply primed with <|assistant|>
    return total

# ─────────────────────────────────────────────────────────────────────────
# 2)  rolling 60‑s token counter (“token bucket”)
# ─────────────────────────────────────────────────────────────────────────
TPM_LIMIT = 30_000                  # gpt‑4o org‑wide default
history: deque[tuple[float, int]] = deque()   # (ts, n_tokens)

def tokens_last_minute() -> int:
    """Return tokens in the previous 60 s; purge stale records."""
    now = time.time()
    while history and history[0][0] < now - 60:
        history.popleft()
    return sum(t for _, t in history)

def wait_for_quota(tokens_needed: int):
    """Sleep precisely until `tokens_needed` will fit into the bucket."""
    while tokens_last_minute() + tokens_needed > TPM_LIMIT:
        head_ts, _ = history[0]
        sleep_for = (head_ts + 60) - time.time() + 0.05  # +ε safety
        if sleep_for > 0:
            time.sleep(sleep_for)
        else:                                            # should rarely hit
            break

def log_tokens(n: int):
    history.append((time.time(), n))


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


# ─────────────────────────────────────────────────────────────────────────
#  NEW  — helper to detect seasonality with GPT‑4o
# ─────────────────────────────────────────────────────────────────────────
def detect_seasonality(df, datetime_column, client, max_rows: int = 200):
    """
    Ask GPT‑4o to infer the dominant season length (in rows).

    Returns
    -------
    int  – positive integer ≥ 1
    """
    sample = df[[datetime_column]].head(max_rows).to_json(orient="records")

    system_prompt = (
        "You are an expert time‑series analyst. The user will give you a list "
        "of timestamped rows from a dataset.  Infer the dominant seasonality "
        "*in number of rows* (e.g. hourly data with daily cycle → 24). "
        "Respond ONLY in JSON:\n"
        '{ "season_length": <positive integer> }'
    )

    resp = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": sample}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "seasonality_schema",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "season_length": {  # ← only the allowed keywords
                            "type": "integer",
                            "description": "Dominant season length in rows"
                        }
                    },
                    "required": ["season_length"],
                    "additionalProperties": False
                }
            }
        },
    )

    season_len = int(json.loads(resp.choices[0].message.content)["season_length"])
    return max(1, season_len)           # final sanity‑check in Python

# ─────────────────────────────────────────────────────────────────────────
#  UPDATED  — iterative_forecasting uses the season length
# ─────────────────────────────────────────────────────────────────────────
def iterative_forecasting(df, datetime_column, client):
    df = df.sort_values(datetime_column).reset_index(drop=True)
    df[datetime_column] = pd.to_datetime(df[datetime_column])

    # 1)  Ask GPT‑4o for the season length
    try:
        season_len = detect_seasonality(df, datetime_column, client)
    except Exception as err:
        print(f"⚠️  Seasonality detection failed: {err}.  Using default=48.")
        season_len = 48

    # 2)  Calculate the lead time (step) for the *next* timestamp
    step = df[datetime_column].iloc[-1] - df[datetime_column].iloc[-2]

    forecasts = []
    hop = season_len  * 2                     # hop size and window size are the same
    n_iters = (len(df) - 1 + hop - 1) // hop    # ceil division for tqdm bar
    original_cols = [c for c in df.columns if c != datetime_column]

    for end in stqdm(range(hop, len(df) + 1, hop),
                     total=n_iters,
                     desc=f"Forecasting (window={season_len})"):
        subset = df.iloc[:end]
        ts = (df[datetime_column].iloc[-1] + step
              if end >= len(df) else df[datetime_column].iloc[end])

        try:
            fc = chat_with_backpressure(subset,
                                         ts,
                                         datetime_column,
                                         client,
                                         original_cols,
                                         base_window=season_len)
            forecasts.append(fc)
        except Exception as err:
            print(f"⚠️  Forecast failed for {ts}: {err}")

    if not forecasts:
        raise RuntimeError("No forecasts were produced.")

    return pd.concat(forecasts, ignore_index=True)

# ─────────────────────────────────────────────────────────────────────────
#  chat_with_backpressure stays exactly as in your previous version.
#  (Its `base_window` is now driven by season_len from detect_seasonality.)
# ─────────────────────────────────────────────────────────────────────────



def chat_with_backpressure(df,
                           timestamp,
                           datetime_column,
                           client,
                           original_cols,
                           base_window: int = 48):
    """
    Forecast a single timestamp with strict column enforcement and
    rate‑limit safety.
    """
    # 0)  Build the column‑specific JSON schema once
    col_props = {c: {"type": "number"} for c in original_cols}
    col_props["forecast_time"] = {"type": "string"}       # ISO 8601
    row_schema = {
        "type": "object",
        "properties": col_props,
        "required": list(col_props.keys()),               # ALL columns required
        "additionalProperties": False
    }
    response_schema = {
        "name": "single_forecast_row",
        "strict": True,
        "schema": row_schema
    }

    window = base_window
    while True:
        df_slice = df.tail(window)
        payload_json = df_slice.to_json()

        messages = [
            {
                "role": "system",
                "content": (
                    f"Predict the next time {base_window*2} step for **all** numeric columns "
                    f"exactly as named here: {', '.join(original_cols)}.\n"
                    "Return a single JSON object with those keys **plus** "
                    f"'forecast_time' equal to {timestamp.isoformat()}.\n"
                    "Do NOT rename, pluralise or add suffixes."
                )
            },
            {"role": "user", "content": payload_json}
        ]

        n_tokens_in = tokens_in_messages(messages)
        estimated_out = 200                     # much smaller now
        tokens_total = n_tokens_in + estimated_out

        if tokens_total > TPM_LIMIT:
            if window == 1:
                raise ValueError("Even a 1‑row payload exceeds token limit.")
            window = max(1, window // 2)
            continue

        wait_for_quota(tokens_total)            # rate‑limit throttle

        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0,
            response_format={"type": "json_schema",
                             "json_schema": response_schema},
            max_completion_tokens=estimated_out,
        )

        log_tokens(n_tokens_in +
                   tokens_in_text(resp.choices[0].message.content))

        row = json.loads(resp.choices[0].message.content)
        return pd.DataFrame([row])              # already tidy
