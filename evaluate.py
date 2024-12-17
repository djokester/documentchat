from llm_guard.input_scanners import Toxicity, Sentiment, PromptInjection, Gibberish
from llm_guard.input_scanners.toxicity import MatchType as InputToxicityMatchType
from llm_guard.input_scanners.prompt_injection import MatchType as InputPromptInjectionMatchType
from llm_guard.input_scanners.gibberish import MatchType as InputGibberishMatchType
from llm_guard.output_scanners import Bias, Gibberish as OutputGibberish, Toxicity as OutputToxicity
from llm_guard.output_scanners.bias import MatchType as OutputBiasMatchType
from llm_guard.output_scanners.gibberish import MatchType as OutputGibberishMatchType
from llm_guard.output_scanners.toxicity import MatchType as OutputToxicityMatchType

def evaluate_prompt(prompt):
    results = {}

    # Evaluate prompt for toxicity
    toxicity_scanner = Toxicity(threshold=0.5, match_type=InputToxicityMatchType.SENTENCE)
    sanitized_prompt, is_valid, risk_score = toxicity_scanner.scan(prompt)
    results['prompt_toxicity'] = {
        "sanitized_prompt": sanitized_prompt,
        "is_valid": is_valid,
        "risk_score": risk_score
    }

    # Evaluate prompt for sentiment
    sentiment_scanner = Sentiment(threshold=0)
    sanitized_prompt, is_valid, risk_score = sentiment_scanner.scan(prompt)
    results['prompt_sentiment'] = {
        "sanitized_prompt": sanitized_prompt,
        "is_valid": is_valid,
        "risk_score": risk_score
    }

    # Evaluate prompt for prompt injections
    prompt_injection_scanner = PromptInjection(threshold=0.5, match_type=InputPromptInjectionMatchType.FULL)
    sanitized_prompt, is_valid, risk_score = prompt_injection_scanner.scan(prompt)
    results['prompt_injection'] = {
        "sanitized_prompt": sanitized_prompt,
        "is_valid": is_valid,
        "risk_score": risk_score
    }

    # Evaluate prompt for gibberish
    gibberish_scanner = Gibberish(match_type=InputGibberishMatchType.FULL)
    sanitized_prompt, is_valid, risk_score = gibberish_scanner.scan(prompt)
    results['prompt_gibberish'] = {
        "sanitized_prompt": sanitized_prompt,
        "is_valid": is_valid,
        "risk_score": risk_score
    }

    return results

def evaluate_output(prompt, model_output):
    results = {}

    # Evaluate output for bias
    bias_scanner = Bias(threshold=0.5, match_type=OutputBiasMatchType.FULL)
    sanitized_output, is_valid, risk_score = bias_scanner.scan(prompt, model_output)
    results['output_bias'] = {
        "sanitized_output": sanitized_output,
        "is_valid": is_valid,
        "risk_score": risk_score
    }

    # Evaluate output for gibberish
    gibberish_scanner = OutputGibberish(match_type=OutputGibberishMatchType.FULL)
    sanitized_output, is_valid, risk_score = gibberish_scanner.scan(prompt, model_output)
    results['output_gibberish'] = {
        "sanitized_output": sanitized_output,
        "is_valid": is_valid,
        "risk_score": risk_score
    }

    # Evaluate output for toxicity
    toxicity_scanner = OutputToxicity(threshold=0.5, match_type=OutputToxicityMatchType.SENTENCE)
    sanitized_output, is_valid, risk_score = toxicity_scanner.scan(prompt, model_output)
    results['output_toxicity'] = {
        "sanitized_output": sanitized_output,
        "is_valid": is_valid,
        "risk_score": risk_score
    }

    return results