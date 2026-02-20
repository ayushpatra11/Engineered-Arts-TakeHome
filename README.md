### Installation and Running Instructions

---

#### Prerequisites

- Python 3.8 or higher installed on your system.
- `pip` package manager available.

#### Setup

1. Clone the repository or download the project files.
2. Navigate to the project directory in your terminal.
3. Create a virtual environment (optional but recommended):

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

4. Install required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

#### Setting the OPENAI_API_KEY Environment Variable (Linux/MacOS bash)

1. Export your OpenAI API key in the terminal:

   ```bash
   export OPENAI_API_KEY="your_api_key_here"
   ```

2. To make this change persistent across sessions, add the export line to your `~/.bashrc` or `~/.bash_profile` file:

   ```bash
   echo 'export OPENAI_API_KEY="your_api_key_here"' >> ~/.bashrc
   source ~/.bashrc
   ```

3. Verify the environment variable is set:

   ```bash
   echo $OPENAI_API_KEY
   ```

4. In my Python code, I have accessed the API key using the `os` module, so please make sure that the above command shows the right output:

   ```python
   import os
   api_key = os.getenv("OPENAI_API_KEY")
   ```

#### Running the Server

1. Start the WebSocket server by running:

   ```bash
   python src/server.py
   ```

   The server will listen for client connections on the configured host and port.

#### Running the Client

1. Run the client application:

   ```bash
   python src/client.py
   ```
2. Use the CLI to input text, to receive real-time synthesized speech audio stream.

---

### Low-Level Design (LLD) Document for Real-Time Text-to-Speech Service

---

#### 1. Overview

This document details the low-level design for the real-time text-to-speech (TTS) service that converts user input text into speech audio streamed over WebSocket connections. The system is designed to handle multiple concurrent clients efficiently, enforce rate limiting, and provide clear JSON-based communication protocols. The backend integrates modular components for large language model (LLM) and TTS API interactions, ensuring extensibility and maintainability.

---

#### 2. Server Concurrency Model

The server leverages Python's `asyncio` library to implement asynchronous concurrency. Each client connection is managed as an independent coroutine, allowing the server to multiplex I/O-bound operations without blocking or spawning multiple threads/processes.

I read about this from the official websockets documentation: 

*websockets: Documentation* — [https://websockets.readthedocs.io/en/stable/topics/timeouts.html#keepalive](https://pypi.org/project/websockets/#:~:text=What%20is%20websockets%3F,an%20elegant%20coroutine%2Dbased%20API.)

**Key points:**

- WebSocket connections are accepted and handled asynchronously.
- Message receipt, processing, and response sending are non-blocking.
- Connection lifecycle (handshake, message handling, closure) is event-driven.

**Example code snippet illustrating concurrency:**

```python
import asyncio
import websockets

async def handle_client(websocket, path):
    async for message in websocket:
        response = await process_message(message)
        await websocket.send(response)

async def main():
    async with websockets.serve(handle_client, 'localhost', 8765):
        await asyncio.Future()  # Run forever

asyncio.run(main())
```

This design ensures high throughput and low latency, enabling support for many simultaneous clients.

Using coroutines with WebSocket connections allows the server to manage multiple clients concurrently without thread-based overhead. Each client handler coroutine can asynchronously wait for incoming messages and send responses, improving scalability and responsiveness. The `websockets` library from PyPI provides a stable asynchronous WebSocket implementation, documented at https://websockets.readthedocs.io/en/stable/.

---

#### 3. Message Protocol and Handling

Communication between client and server strictly follows a JSON schema for both success and error responses, facilitating straightforward client-side parsing and error handling.

**Success message schema:**

```json
{
  "status": 200,
  "error": null,
  "payload": {
    "audio_base64": "<encoded audio>"
  }
}
```

**Failure message schema:**

```json
{
  "status": <4xx or 5xx>,
  "error": "<error message>",
  "payload": {
    "audio_base64": ""
  }
}
```

**Message processing flow:**



1. Receive JSON-formatted text input from client.
2. Validate input and enforce rate limiting.
3. Forward input to LLM/TTS modules asynchronously.
4. Encode resulting audio to base64 and send in response.
5. On errors, send structured failure JSON with appropriate status and error messages.

![alt text](/images/data_flow.png)

I decided on creating the `MessageCreator` as a separate module since it encapsulates message formatting logic, promoting modularity and reusability. This separation allows consistent message construction across different parts of the system, simplifies maintenance, and facilitates unit testing by isolating message creation from business logic.

---

#### 4. Rate Limiting Implementation

To prevent abuse and ensure fair resource allocation, the server applies per-client rate limiting based on client identifiers (e.g., IP address or session token).

**Implementation details:**

- Uses a sliding window algorithm to track request quotas within 60 second windows.
- When quota is exceeded, server responds with status code 429 and descriptive error.
- Rate limiting logic is integrated as middleware in the request handling pipeline.

Rate limiting was implemented to safeguard the service against excessive or malicious usage that could degrade performance or availability. By enforcing per-client quotas, the system ensures equitable resource distribution, prevents denial-of-service scenarios, and maintains stable throughput under high load. This design choice balances user experience with operational reliability.

---

#### 5. Modular LLM and TTS Integration

The backend encapsulates interactions with LLM and TTS APIs into separate, modular service layers. This abstraction allows easy swapping or upgrading of models without modifying core server logic.

**Design considerations:**

- Each module handles authentication, request formatting, and response parsing.
- Supports asynchronous API calls to optimize throughput.
- Facilitates unit testing by isolating external dependencies.

**Example module interface:**

```python
class OAILLMHandler:
    async def call_llm(self, prompt: str) -> str:
        # Send prompt to LLM API asynchronously
        pass

class OAITTSHandler:
    async def call_tts(self, text: str) -> bytes:
        # Send text to TTS API asynchronously and return raw audio bytes
        pass
```

**Integration in message processing:**

Please consider this pseudocode since I wanted to define the structure of the response message here

```python
async def process_message(message: str) -> str:
    text = await llm_service.generate_text(message)
    audio_bytes = await tts_service.synthesize_audio(text)
    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    response = {
        "status": 200,
        "error": None,
        "payload": {"audio_base64": audio_base64}
    }
    return json.dumps(response)
```

---

#### 6. Client Handling and Retry Strategy

I have worked previously with retry mechanisms with exponential backoff to handle transient errors gracefully. I tried to implement the same with clients here by having an event loop implemented in the most basic manner using a while loop. The retries were performed using exception handling. The server provides clear status codes and error messages to distinguish recoverable from fatal errors.

**Server-side design:**

- Returns HTTP-like status codes (e.g., 429 for rate limiting, 500 for server errors).
- Provides descriptive error messages to guide client logic.

I preferred using a `StatusCode` enum for client communication, to standardise status representation across the system. This approach improves code readability, reduces integer numbers, and ensures consistency in status codes sent to clients, facilitating easier client-side interpretation and error handling.

---

#### 7. Full-Stack Integration Considerations

The backend is designed to integrate seamlessly with frontend applications for real-time interactive experiences.

**Typical frontend workflow:**

- Establish persistent WebSocket connection.
- Send user text input as JSON messages.
- Receive base64-encoded audio payloads incrementally or in full.
- Display error notifications and trigger retry logic based on server responses.
- Manage UI controls (start, stop, replay) synchronized with backend audio streaming.

---

#### 8. Scope of Enhancement: Justification for Not Using Flask/Django

This service prioritizes asynchronous, event-driven concurrency suitable for real-time streaming over WebSocket connections. Traditional synchronous web frameworks like Flask or Django are not ideal for this use case due to their blocking request handling model.

**Reasons for custom async server:**

- Native support for asynchronous WebSocket handling and concurrency via `asyncio`.
- Fine-grained control over connection lifecycle and message streaming.
- Lower latency and higher throughput without thread/process overhead.
- Easier integration of rate limiting and modular API components in an async context.

While Flask and Django excel in RESTful HTTP APIs and rapid development, they introduce complexity and performance bottlenecks for real-time streaming applications where non-blocking I/O and concurrency are critical.

---

#### 9. WebSocket Connection Configuration: Use of `ping_timeout=None`

"The server uses `ping_timeout=None` in the WebSocket configuration to disable automatic ping timeout disconnections. This setting functions as an equivalent to TCP keepalive by preventing premature connection closures due to transient network delays or client inactivity. According to the `websockets` library documentation, setting `ping_timeout=None` ensures that the server does not forcibly close the connection if a pong response is delayed, enhancing connection stability for long-lived streams essential in real-time audio transmission."

I gathered this information from the official `websockets` keepalive documentation:  
*websockets: Keepalive* — https://websockets.readthedocs.io/en/stable/topics/timeouts.html#keepalive

---

#### 10. Basic Architecture Diagram

![Architecture Diagram Placeholder](/images/hld_flow.png)

*Figure: High-level architecture illustrating client-server interactions, asynchronous processing, rate limiting, and modular API integration.*

---

This design ensures a scalable, maintainable, and performant real-time TTS service suitable for modern interactive voice applications.