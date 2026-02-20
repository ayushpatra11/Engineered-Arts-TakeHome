import asyncio
import json
import websockets
import logging
import uuid
from status_codes import StatusCode
import base64

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
PORT = 8765

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s][%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/clients.log')
    ]
)


async def run_client():
    retries = 0
    client_id = str(uuid.uuid4())
    while True:
        try:
            async with websockets.connect(f"ws://localhost:{PORT}", ping_timeout = None) as websocket:
                logging.info(f"[Client {client_id}]: Client connected to server")
                retries = 0  # reset retries after successful connection

                try:
                    await websocket.send(json.dumps({"client_id": client_id}))
                    while True:
                        text = input("Client: ").strip()
                        if not text:
                            continue

                        try:
                            await websocket.send(json.dumps({"client_id": client_id, "data": text}))
                            logging.info(f"[Client {client_id}] : Waiting for server response...")
                        except websockets.ConnectionClosed:
                            logging.error(f"[Client {client_id}] : Connection closed by server during send. Reconnecting...")
                            break
                        except Exception:
                            logging.error(f"[Client {client_id}] : Unable to send message to server")
                            break

                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=10)
                        except asyncio.TimeoutError:
                            logging.info(f"[Client {client_id}] : No response from server, will retry...")
                            continue  
                        except websockets.ConnectionClosed:
                            logging.warning(f"[Client {client_id}] : Server closed connection unexpectedly, reconnecting...")
                            break  
                        except Exception as e:
                            logging.error(f"[Client {client_id}] : Unexpected error: {e}")
                            continue

                        try:
                            message_body = json.loads(message)
                            status = message_body.get("status", StatusCode.INTERNAL_ERROR.value)
                            payload = message_body.get("payload", {})

                            if status != StatusCode.OK.value:
                                logging.error(f"[Client {client_id}] : Server error (status {status}): {message_body.get('error')}")
                            else:
                                if "audio_base64" in payload:
                                    audio_data = payload["audio_base64"]
                                    if isinstance(audio_data, str):
                                        audio_bytes = base64.b64decode(audio_data)
                                        logging.info(f"[Client {client_id}] : Received audio data of {len(audio_bytes)} bytes")
                                        with open(f"temp/output_{client_id}.wav", "wb") as f:
                                            f.write(audio_bytes)
                                    else:
                                        logging.warning(f"[Client {client_id}] : Unexpected audio data format")
                                logging.debug(f"[Client {client_id}] : Server payload: {payload}")
                        except json.JSONDecodeError:
                            logging.error(f"[Client {client_id}] : Server (raw): {message}")

                except KeyboardInterrupt:
                    logging.error(f"[Client {client_id}] : Disconnected from server.")
                    break

        ## I have used this concept during my time at my prev org. We used to have heart beat messages because in rare cases, some calls would hang. 
        ## To allow retrying connection while a subsystem switches over, I tried to have a simple implementation. 
        except (ConnectionRefusedError, OSError) as err:
            retries += 1
            if retries > MAX_RETRIES:
                logging.error(f"[Client {client_id}] : Maximum retries reached. Exiting client.")
                break
            logging.info(f"[Client {client_id}] : Connection failed. Retrying in {RETRY_DELAY} seconds... "
                  f"\nAttempt {retries}/{MAX_RETRIES}")
            await asyncio.sleep(RETRY_DELAY)
        except websockets.ConnectionClosed:
            logging.info(f"[Client {client_id}] : Connection closed by server. Retrying in {RETRY_DELAY} seconds...")
            await asyncio.sleep(RETRY_DELAY)
        except KeyboardInterrupt:
            logging.error(f"[Client {client_id}] : Disconnected from server.")

if __name__ == "__main__":
    try:
        asyncio.run(run_client())
    except KeyboardInterrupt:
        logging.info("\n\nClient: Exiting gracefully.")