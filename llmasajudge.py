from models import Evaluation
import json

def get_evaluation(user_input, metadata, client, data):
    system_prompt = f"Given the question, the head of the orginal dataframe, and the head, tail and description extracted dataframe in response to the query below, can you describe if the data extracted is correct and provide a justification for your response."
    messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Question:  {user_input}  \n  Extracted Data Head: `{data.head().to_string()}`  \n Extracted Data Tail: `{data.tail().to_string()}`  \n Extracted Data Description: `{data.describe().to_string()}`  \n Original DataFrame Head: `{metadata}` "},
        ]
    chat_completion = client.chat.completions.create(
        messages=messages,
        model="gpt-4o",
        response_format={
            "name": "evaluation",
            "schema": {
                "type": "object",
                "properties": {
                "evaluation": {
                    "type": "boolean",
                    "description": "A boolean value representing the outcome of the evaluation."
                },
                "justification": {
                    "type": "string",
                    "description": "A string providing the justification or reasoning behind the evaluation."
                }
                },
                "required": [
                "evaluation",
                "justification"
                ],
                "additionalProperties": False
            },
            "strict": True
            },
        temperature=0    
    )
    try:
        evaluation  = Evaluation.model_validate_json(chat_completion.choices[0].message.content)
        return evaluation
    except Exception as e:
        messages+= [{"role": "assistant", "content": chat_completion.choices[0].message.content}, 
                    {"role": "user", "content": f"This generated the following Exception: {str(e)}. Can you please return just the corrected json"}] 
        chat_completion = client.chat.completions.create(
            messages = messages,         
            model="gpt-4o",
            temperature=0, 
            response_format={
            "name": "evaluation",
            "schema": {
                "type": "object",
                "properties": {
                "evaluation": {
                    "type": "boolean",
                    "description": "A boolean value representing the outcome of the evaluation."
                },
                "justification": {
                    "type": "string",
                    "description": "A string providing the justification or reasoning behind the evaluation."
                }
                },
                "required": [
                "evaluation",
                "justification"
                ],
                "additionalProperties": False
            },
            "strict": True
            }
    )
        try:
            evaluation  = Evaluation.model_validate_json(chat_completion.choices[0].message.content)
            return evaluation
        except Exception as e:
            messages+= [{"role": "assistant", "content": chat_completion.choices[0].message.content}, 
                        {"role": "user", "content": f"This generated the following Exception: {str(e)}. Can you please return just the corrected json"}] 
            chat_completion = client.chat.completions.create(
                messages = messages,         
                model="gpt-4o",
                temperature=0, 
                response_format={
            "name": "evaluation",
            "schema": {
                "type": "object",
                "properties": {
                "evaluation": {
                    "type": "boolean",
                    "description": "A boolean value representing the outcome of the evaluation."
                },
                "justification": {
                    "type": "string",
                    "description": "A string providing the justification or reasoning behind the evaluation."
                }
                },
                "required": [
                "evaluation",
                "justification"
                ],
                "additionalProperties": False
            },
            "strict": True
            }
            )
            evaluation  = Evaluation.model_validate_json(chat_completion.choices[0].message.content)
            return evaluation
