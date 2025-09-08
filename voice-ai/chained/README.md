# Voice AI Chat - Chained

This is a complete voice AI chat application that chains together three AI services:
1. **Speech-to-Text** (OpenAI gpt-4o-mini-transcribe) - transcribes your voice to text
2. **Language Model** (gpt-4o-mini) - generates AI response to your message  
3. **Text-to-Speech** (OpenAI gpt-4o-mini-tts) - synthesizes the response into speech

The application uses WebRTC for real-time communication between the browser and server.

## Features

- **Automatic Voice Activity Detection (VAD)** - No need to press buttons! The system automatically detects when you start and stop speaking
- Real-time voice conversation with AI
- WebRTC-based streaming
- Web interface with real-time speech detection indicators
- Intelligent silence detection for natural conversation flow

## Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- OpenAI API key
- Modern web browser with WebRTC support

## Setup

1. **Clone and navigate to the project:**
   ```bash
   cd voice-ai/chained
   ```

2. **Install dependencies using uv:**
   ```bash
   uv sync
   ```

3. **Set your OpenAI API key:**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

## Running the Application

1. **Start the server:**
   ```bash
   uv run server.py
   ```
   
   The server will start on `http://localhost:8000`

2. **Open the web interface:**
   - Navigate to `http://localhost:8000` in your browser

3. **Click "Start Voice Chat"** and allow microphone access when prompted

4. **Start talking!** The AI will respond with voice in real-time

5. **Just start speaking naturally!** The system will automatically:
   - Detect when you start talking
   - Record your speech
   - Stop recording when you finish speaking
   - Process your message and respond with audio

6. **Click "Stop Chat"** when you're done
