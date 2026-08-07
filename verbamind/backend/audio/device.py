"""Audio device enumeration and dual-channel microphone configuration."""

from typing import Any

_CHANNEL_CONFIG = {
    "patient_input": 0,
    "psychologist_input": 1,
}


def _get_pyaudio():
    import pyaudio
    return pyaudio


def list_input_devices() -> list[dict[str, Any]]:
    pyaudio = _get_pyaudio()
    devices = []
    audio = pyaudio.PyAudio()
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        if int(info.get("maxInputChannels", 0)) > 0:
            devices.append({
                "index": i,
                "name": info.get("name", ""),
                "channels": int(info.get("maxInputChannels", 0)),
                "sample_rate": float(info.get("defaultSampleRate", 44100)),
            })
    audio.terminate()
    return devices


def get_channel_config() -> dict[str, int]:
    return dict(_CHANNEL_CONFIG)


def set_channel_config(patient_input: int, psychologist_input: int) -> None:
    _CHANNEL_CONFIG["patient_input"] = patient_input
    _CHANNEL_CONFIG["psychologist_input"] = psychologist_input
