from pathlib import Path
import openai
import os
import asyncio

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

## Error handling in case the OpenAI key is not set in the environment. 
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set")

## init variables that will be used by both the services. 
openai.api_key = OPENAI_API_KEY


class OAITTSCaller:
    def __init__(self):
        pass
    async def call_tts(self, text):
        with openai.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=text,
            response_format="wav",
            stream_format="audio",  
            speed=1.0
        ) as response:
            audio_bytes = await asyncio.to_thread(response.read)
        return audio_bytes