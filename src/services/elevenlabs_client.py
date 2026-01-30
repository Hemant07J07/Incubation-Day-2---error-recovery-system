from src.exceptions import TransientServiceError, PermanentServiceError

class ElevenLabsClient:
    def __init__(self, api_key=None):
        self.api_key = api_key

    def synthesize(self, text):
        """
        In production: call ElevenLabs TTS API.
        For testing: this method may raise TransientServiceError or PermanentServiceError.
        """
        # This placeholder should be replaced with real HTTP calls.
        # For now, simulate success
        return b"AUDIO_BYTES"
