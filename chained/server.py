import asyncio
import json
import os
from io import BytesIO

import uvicorn
from aiortc import RTCPeerConnection, RTCSessionDescription
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")  # Get API key from environment variable
)

if not os.getenv("OPENAI_API_KEY"):
    print("OPENAI_API_KEY environment variable is not set!")
    raise ValueError(
        "Please set OPENAI_API_KEY environment variable"
    )


def transcribe_audio(audio_data: bytes) -> str:
    buffer = BytesIO(audio_data)
    buffer.name = "audio.webm"
    transcription = client.audio.transcriptions.create(
        model="gpt-4o-mini-transcribe",
        file=buffer
    )
    result = transcription.text
    print(f"STT result: {result}")
    return result


def generate_response(user_text: str) -> str:
    chat_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": user_text}]
    )
    result = chat_response.choices[0].message.content
    print(f"LLM result: {result}")
    return result


def synthesize_speech(text: str) -> bytes:
    speech_response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=text,
        response_format="mp3"
    )
    audio_data = speech_response.content
    print(f"TTS result: {len(audio_data)} bytes of audio")
    return audio_data


# WebRTC data channel has size limits, so we need to chunk large audio data
CHUNK_SIZE = 16384  # 16KB chunks to stay well under WebRTC limits
MAX_CHUNK_DELAY = 0.001  # 1ms delay between chunks for smooth transmission


async def send_audio_chunks(channel, audio_data: bytes):
    """
    Send audio data in chunks over WebRTC data channel with proper protocol
    """
    total_size = len(audio_data)
    total_chunks = (total_size + CHUNK_SIZE - 1) // CHUNK_SIZE  # Ceiling division

    # Send header with metadata
    header = {
        "type": "audio_start",
        "total_size": total_size,
        "total_chunks": total_chunks,
        "chunk_size": CHUNK_SIZE
    }
    header_json = json.dumps(header)
    channel.send(header_json)

    # Send audio chunks
    for chunk_index in range(total_chunks):
        start_pos = chunk_index * CHUNK_SIZE
        end_pos = min(start_pos + CHUNK_SIZE, total_size)
        chunk_data = audio_data[start_pos:end_pos]

        # Send chunk with metadata
        chunk_header = json.dumps({
            "type": "audio_chunk",
            "chunk_index": chunk_index,
            "chunk_size": len(chunk_data)
        }).encode() + b"\n"  # Delimiter

        # Send header + data as single message
        message = chunk_header + chunk_data
        channel.send(message)

        # Small delay to prevent overwhelming the channel
        if chunk_index < total_chunks - 1:  # No delay after last chunk
            await asyncio.sleep(MAX_CHUNK_DELAY)

    # Send completion signal
    completion = {"type": "audio_complete", "total_chunks": total_chunks}
    completion_json = json.dumps(completion)
    channel.send(completion_json)
    print(f"Audio transmission complete: {total_chunks} chunks sent")

app = FastAPI(title="Voice AI Chat", description="Real-time voice AI chat with WebRTC")
pcs = set()  # keep track of peer connections to prevent garbage collection

# Serve the main HTML file at root
@app.get("/")
async def read_index():
    """Serve the main HTML page"""
    return FileResponse("index.html")

# Mount static files (for any additional assets if needed)
app.mount("/static", StaticFiles(directory="."), name="static")

@app.post("/offer")
async def offer(request: Request):
    data = await request.json()
    # Set up WebRTC peer connection with incoming offer
    pc = RTCPeerConnection()
    pcs.add(pc)
    offer = RTCSessionDescription(sdp=data["sdp"], type=data["type"])
    await pc.setRemoteDescription(offer)

    # Create a return data channel for sending responses back to client
    response_channel = pc.createDataChannel("audio_response")

    # When a data channel is opened by the client:
    @pc.on("datachannel")
    def on_datachannel(channel):

        @channel.on("message")
        async def on_message(message):
            # Expect binary audio data from client
            if not isinstance(message, bytes):
                print(f"Received non-binary message: {message}")
                return

            print(f"Received audio data: {len(message)} bytes")

            # Step 1: Speech-to-Text - Convert audio to text
            user_text = transcribe_audio(message)

            # Step 2: Language Model - Generate AI response
            reply_text = generate_response(user_text)

            # Step 3: Text-to-Speech - Convert response to audio
            audio_data = synthesize_speech(reply_text)

            # Send audio back in chunks via the response channel
            await send_audio_chunks(response_channel, audio_data)

    # Create and return answer SDP to establish the WebRTC connection
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
