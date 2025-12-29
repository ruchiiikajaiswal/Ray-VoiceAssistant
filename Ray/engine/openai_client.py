import os
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletion

# --- 1. Initialization and Setup ---

# Load .env from project root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set. Add it to .env or set the environment variable.")

try:
    client = OpenAI(
        api_key=API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )
except Exception as e:
    raise RuntimeError(f"Failed to initialize OpenRouter client: {e}")

# --- 2. API Call Function (Using Modern Client) ---

def chat_completion(messages, model="xai/grok-4.1-fast:free", **kwargs) -> ChatCompletion:
    """
    Wrapper to call the OpenRouter Chat Completion API.

    Args:
        messages (list): List of message dicts like 
                         [{"role": "user", "content": "Hello"}]
        model (str): The model to use. Defaults to "xai/grok-4.1-fast:free".
        **kwargs: Additional parameters like temperature, max_tokens, etc.

    Returns:
        ChatCompletion: The response object (a Pydantic model).
    """
    print(f"--- Calling model: {model} via OpenRouter ---")
    
    return client.chat.completions.create(
        model=model, 
        messages=messages,
        extra_headers={
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Ray Voice Assistant",
        },
        **kwargs
    )

def chat_completion_stream(messages, model="xai/grok-4.1-fast:free", **kwargs):
    """
    Stream responses from OpenRouter API for real-time display.
    
    Args:
        messages (list): List of message dicts
        model (str): Model to use (default: xai/grok-4.1-fast:free via OpenRouter)
        **kwargs: Additional parameters
        
    Yields:
        str: Individual text chunks as they arrive
    """
    print(f"--- Streaming from model: {model} via OpenRouter ---")
    
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
        extra_headers={
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Ray Voice Assistant",
        },
        **kwargs
    )
    
    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

# --- 3. Reply Text Extraction Function (Corrected and Robust) ---

def get_reply_text(resp: ChatCompletion) -> str:
    """
    Extract assistant text from a ChatCompletion object (modern SDK format).

    Args:
        resp (ChatCompletion): The response object returned by chat_completion.

    Returns:
        str: The extracted and stripped text content, or an empty string on failure.
    """
    try:
        # The new SDK response is a Pydantic object, allowing direct,
        # safer attribute access:
        # resp.choices -> list of Choice objects
        # resp.choices[0].message -> ChatCompletionMessage object
        # resp.choices[0].message.content -> str (or None)
        
        # We ensure content is not None before stripping
        content = resp.choices[0].message.content
        return content.strip() if content else ""
        
    except (IndexError, AttributeError) as e:
        print(f"Error extracting reply text from response structure: {e}")
        # Return an empty string or handle the error as appropriate for your application
        return ""
    except Exception as e:
        print(f"An unexpected error occurred during extraction: {e}")
        return ""

# --- 4. Example Usage ---

if __name__ == "__main__":
    
    # 1. Define the conversation (messages)
    conversation_history = [
        {"role": "system", "content": "You are a helpful, brief, and slightly poetic assistant."},
        {"role": "user", "content": "Write a short haiku about code debugging."}
    ]

    # 2. Call the API
    try:
        completion_response = chat_completion(conversation_history)
        
        # 3. Extract the text
        reply_text = get_reply_text(completion_response)

        # 4. Print results
        print("\n[ Assistant Response ]")
        if reply_text:
            print(reply_text)
        else:
            print("Failed to get response text.")
            
        # Optional: Print the full raw object for inspection
        # print("\n[ Full Response Object (Pydantic model) ]")
        # print(completion_response.model_dump_json(indent=2)) 

    except RuntimeError as e:
        print(f"\nFATAL ERROR: {e}")
    except Exception as e:
        print(f"\nAPI Call Failed: {e}")
        print("Please ensure your internet connection is active and your API key is correct.")
