from models import Explanation
import json

def get_explanation(user_input, metadata, client, data):
    flag_format = "{\"explanation\": string}"
    system_prompt = f"Given the question, the head of the orginal dataframe, and the head, tail and description extracted dataframe in response to the query below, can you write the worded answer to the question for which the dataframe was extracted? Your response needs to be in the JSON format: {json.dumps(flag_format)}."
    messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Question:  {user_input}  \n  Extracted Data Head: `{data.head().to_string()}`  \n Extracted Data Tail: `{data.tail().to_string()}`  \n Extracted Data Description: `{data.describe().to_string()}`  \n Original DataFrame Head: `{metadata}` "},
        ]
    chat_completion = client.chat.completions.create(
        messages=messages,
        model="gpt-4o",
        response_format={"type": "json_schema",
    "json_schema": {
      "name": "textual_explanation",
      "strict": True,
      "schema": {
        "type": "object",
        "properties": {
          "explanation": {
            "type": "string",
            "description": "A textual explanation."
          }
        },
        "required": [
          "explanation"
        ],
        "additionalProperties": False
      }
    }},
        temperature=0    
    )
    try:
        explanation  = Explanation.model_validate_json(chat_completion.choices[0].message.content)
        return explanation
    except Exception as e:
        messages+= [{"role": "assistant", "content": chat_completion.choices[0].message.content}, 
                    {"role": "user", "content": f"This generated the following Exception: {str(e)}. Can you please return just the corrected explanation json"}] 
        chat_completion = client.chat.completions.create(
            messages = messages,         
            model="gpt-4o",
            temperature=0, 
            response_format={
      "name": "textual_explanation",
      "strict": True,
      "schema": {
        "type": "object",
        "properties": {
          "explanation": {
            "type": "string",
            "description": "A textual explanation."
          }
        },
        "required": [
          "explanation"
        ],
        "additionalProperties": False
      }
    }
        )
        try:
            explanation  = Explanation.model_validate_json(chat_completion.choices[0].message.content)
            return explanation
        except Exception as e:
            messages+= [{"role": "assistant", "content": chat_completion.choices[0].message.content}, 
                        {"role": "user", "content": f"This generated the following Exception: {str(e)}. Can you please return just the corrected explanation json"}] 
            chat_completion = client.chat.completions.create(
                messages = messages,         
                model="gpt-4o",
                temperature=0, 
                response_format={
      "name": "textual_explanation",
      "strict": True,
      "schema": {
        "type": "object",
        "properties": {
          "explanation": {
            "type": "string",
            "description": "A textual explanation."
          }
        },
        "required": [
          "explanation"
        ],
        "additionalProperties": False
      }
    } 
            )
            explanation  = Explanation.model_validate_json(chat_completion.choices[0].message.content)
            return explanation
