import openai

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

## Error handling in case the OpenAI key is not set in the environment. 
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set")

## init variables that will be used by both the services. 
openai.api_key = OPENAI_API_KEY