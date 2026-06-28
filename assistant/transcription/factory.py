def get_transcriber(settings):
    t = settings.transcription
    if getattr(t, "mode", "local") == "remote":
        from assistant.transcription.remote_transcriber import RemoteTranscriber
        return RemoteTranscriber(t.remote_url)
    from assistant.transcription.whisper_transcriber import FasterWhisperTranscriber
    return FasterWhisperTranscriber(t.model_size, t.device, t.compute_type)
