"""Audio I/O helpers — raw PCM <-> WAV conversion and channel splitting.

Recordings are raw PCM int16 (16 kHz, mono or interleaved stereo) encrypted in
.vera files. Whisper and librosa both need valid WAV containers, and the
dual-channel design (L=patient, R=psychologist) needs channel splitting.
"""

import io
import wave
from array import array

DEFAULT_SAMPLE_RATE = 16000
DEFAULT_SAMPLE_WIDTH = 2  # int16


def pcm_to_wav_bytes(pcm: bytes, channels: int = 1, sample_rate: int = DEFAULT_SAMPLE_RATE) -> bytes:
    """Wrap raw PCM int16 in a WAV container (in-memory)."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(DEFAULT_SAMPLE_WIDTH)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm)
    return buf.getvalue()


def wav_bytes_to_pcm(wav: bytes) -> tuple[bytes, int, int]:
    """Unwrap WAV bytes -> (raw PCM, channels, sample_rate)."""
    with wave.open(io.BytesIO(wav), "rb") as wf:
        return (
            wf.readframes(wf.getnframes()),
            wf.getnchannels(),
            wf.getframerate(),
        )


def split_stereo_pcm(pcm: bytes) -> tuple[bytes, bytes]:
    """Split interleaved stereo int16 PCM -> (left, right) mono PCM.

    Left = patient (channel 0), right = psychologist (channel 1).
    """
    samples = array("h", pcm)
    if len(samples) % 2 != 0:
        samples = samples[:-1]
    left = array("h", samples[0::2])
    right = array("h", samples[1::2])
    return left.tobytes(), right.tobytes()


def detect_format(data: bytes) -> str:
    """Heuristically detect whether bytes are WAV or raw PCM."""
    if len(data) >= 44 and data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return "wav"
    return "pcm"


def to_mono_wav_bytes(data: bytes, channels: int = 1, sample_rate: int = DEFAULT_SAMPLE_RATE) -> bytes:
    """Normalize any supported input (WAV or raw PCM) to mono WAV bytes.

    For stereo input, mixes down to mono by averaging both channels.
    """
    if detect_format(data) == "wav":
        pcm, ch, sr = wav_bytes_to_pcm(data)
    else:
        pcm, ch, sr = data, channels, sample_rate

    if ch == 2:
        samples = array("h", pcm)
        if len(samples) % 2 != 0:
            samples = samples[:-1]
        left = samples[0::2]
        right = samples[1::2]
        mono = array("h", (int((lf + rt) / 2) for lf, rt in zip(left, right)))
        pcm = mono.tobytes()

    if sr != DEFAULT_SAMPLE_RATE:
        pcm = _resample_nearest(pcm, sr, DEFAULT_SAMPLE_RATE)

    return pcm_to_wav_bytes(pcm, channels=1, sample_rate=DEFAULT_SAMPLE_RATE)


def split_to_channel_wavs(
    data: bytes, channels: int = 1, sample_rate: int = DEFAULT_SAMPLE_RATE
) -> list[bytes]:
    """Split input audio into per-channel mono WAV byte strings.

    Returns a list: index 0 = patient (left), index 1 = psychologist (right).
    Mono input returns a single-element list.
    """
    if detect_format(data) == "wav":
        pcm, ch, sr = wav_bytes_to_pcm(data)
    else:
        pcm, ch, sr = data, channels, sample_rate

    if ch == 1:
        if sr != DEFAULT_SAMPLE_RATE:
            pcm = _resample_nearest(pcm, sr, DEFAULT_SAMPLE_RATE)
            sr = DEFAULT_SAMPLE_RATE
        return [pcm_to_wav_bytes(pcm, 1, sr)]

    left, right = split_stereo_pcm(pcm)
    if sr != DEFAULT_SAMPLE_RATE:
        left = _resample_nearest(left, sr, DEFAULT_SAMPLE_RATE)
        right = _resample_nearest(right, sr, DEFAULT_SAMPLE_RATE)
        sr = DEFAULT_SAMPLE_RATE
    return [pcm_to_wav_bytes(left, 1, sr), pcm_to_wav_bytes(right, 1, sr)]


def _resample_nearest(pcm: bytes, from_rate: int, to_rate: int) -> bytes:
    """Cheap nearest-neighbor resampling of int16 mono PCM (dev-quality)."""
    if from_rate == to_rate:
        return pcm
    samples = array("h", pcm)
    n_out = int(len(samples) * to_rate / from_rate)
    out = array("h", (samples[min(len(samples) - 1, int(i * from_rate / to_rate))] for i in range(n_out)))
    return out.tobytes()
