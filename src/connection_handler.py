import asyncio
from websockets.exceptions import ConnectionClosed
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/server.log')
    ]
)

async def connection_handler(websocket, limiter):
    # init client_id to None to ensure it's always defined and it is expected to be 
    # sent by client as soon as connection is init
    client_id = None

    try:
        async for message in websocket:
            try:
                message_body = json.loads(message)
                ## this is because we are expecting a message to only have client id.. this will be the first message on connection opening. 
                if "client_id" in message_body:
                    client_id = message_body['client_id']

                ## RATE LIMITER LOGIC: although I know this is a websocket server, I rate limited because
                ## we do not want too many calls to the LLM. 
                if not await limiter.allow(client_id):
                    logging.warning(f"Rate limit exceeded for client: {client_id}")
                    await websocket.send(
                        json.dumps({"error": f"Rate limit exceeded for client: {client_id}"})
                    )
                    # Skip processing this message but keep connection open
                    continue

                ## this will basically be the message body that we will get text grom and then
                ## send to our llm. 
                if "data" in message_body:
                    data = message_body['data']

                    ## this is where we will implement the llm calls. TODO. 
                    await websocket.send(
                        json.dumps({"payload": "sample audio bits"})
                    )

                    logging.info(f"Sent placeholder audio to client {client_id}")

            except json.JSONDecodeError:
                logging.error(f"JSON decode error from client {client_id}: {message}")
                #DEBUG: print(f"Client (raw): {message}")
                await websocket.send(
                    json.dumps({"error": "unexpected data format"})
                )
            except Exception as e:
                logging.error(f"Unexpected error processing message from client {client_id}: {e}")
                # Do not close the connection; continue listening for messages

            # llm_text = await call_llm(text)
            # audio = await call_tts(llm_text)
            # await websocket.send(audio)
    except ConnectionClosed:
        logging.info(f"Client disconnected: {client_id}")
