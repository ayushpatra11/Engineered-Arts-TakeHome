from oai_llm_caller import OAILLMCaller
from oai_tts_caller import OAITTSCaller
import json
import logging
import base64
from status_codes import StatusCode

logger = logging.getLogger(__name__)


class MessageCreator:
    def __init__(self):
        self.llm_handler = OAILLMCaller()
        self.tts_handler = OAITTSCaller()

    def _extract_error(self, llm_response):
        if hasattr(llm_response, 'error') and llm_response.error is not None:
            return llm_response.error.message
        if hasattr(llm_response, 'status') and llm_response.status in ["failed", "canceled"]:
            return f"LLM API returned status {llm_response.status}"
        return None

    def _extract_text(self, llm_response):
        texts = []

        for output in llm_response.output:
            if output.type == "message":
                for item in output.content:
                    if item.type == "output_text":
                        texts.append(item.text)

        return "\n".join(texts)
    

    def pack_message(self, status_code, error, payload):
        return json.dumps({"status": status_code, "error": error, "payload": payload})


    async def create_message(self, data):
        """
        This function is basically responsible for creating the message for
        both success and failure scenarios. 
        """
        llm_response = await self.llm_handler.call_llm(data)

        #DEBUG: 
        logger.debug(f"llm_response: {llm_response}")

        # I want to first check whether the response from the llm api is successful or not. 
        # This is to create a message accordingly. 
        error = self._extract_error(llm_response)
        if error is not None:
            return self.pack_message(status_code=StatusCode.INTERNAL_ERROR.value, error=error, payload=[])
    
        text = self._extract_text(llm_response)
        if len(text) > 4096:
            return self.pack_message(status_code=StatusCode.BAD_REQUEST.value, error="Response too long", payload=[])
        
        try:
            audio_bytes = await self.tts_handler.call_tts(text)
            if audio_bytes is None or len(audio_bytes) == 0:
                raise ValueError("TTS returned empty audio")
        except Exception as e:
            logger.error(f"TTS service failed: {e}")
            return self.pack_message(StatusCode.INTERNAL_ERROR.value, "TTS service error", [])

        try:
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding audio to base64: {e}")
            return self.pack_message(status_code=StatusCode.INTERNAL_ERROR.value, error="Audio encoding error", payload=[])

        payload = {"audio_base64": audio_b64}

        response = self.pack_message(StatusCode.OK.value, None, payload)

        #logger.debug(f"resp: {response}")

        return response