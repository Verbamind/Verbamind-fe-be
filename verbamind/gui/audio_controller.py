"""Real-time audio input controller for the GUI — level metering and mic testing.

Wraps PyAudio in a QThread; emits RMS level updates for volume sliders/waveform.
"""

from PySide6.QtCore import QObject, QThread, Signal


class _MicMonitor(QThread):
    """Reads chunks from an input device and emits RMS levels (0.0–1.0)."""

    level_updated = Signal(float)

    def __init__(self, device_index: int | None, parent=None):
        super().__init__(parent)
        self._device_index = device_index
        self._running = False

    def run(self):
        import pyaudio

        self._running = True
        audio = pyaudio.PyAudio()
        try:
            kwargs = dict(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024,
            )
            if self._device_index is not None:
                kwargs["input_device_index"] = self._device_index
            stream = audio.open(**kwargs)
            try:
                while self._running:
                    data = stream.read(1024, exception_on_overflow=False)
                    rms = _rms(data)
                    self.level_updated.emit(rms)
            finally:
                stream.stop_stream()
                stream.close()
        except OSError:
            # Device is unavailable or unsupported — stop silently.
            self._running = False
        finally:
            audio.terminate()

    def stop(self):
        self._running = False
        self.wait(2000)


def _rms(data: bytes) -> float:
    import array
    import math

    samples = array.array("h", data)
    if not samples:
        return 0.0
    peak = 32767.0
    return min(1.0, math.sqrt(sum(s * s for s in samples) / len(samples)) / (peak * 0.5))


def _apply_gain(data: bytes, gain: float) -> bytes:
    """Scale int16 PCM samples by a gain factor (0.0–1.0)."""
    if gain >= 1.0:
        return data
    import array

    samples = array.array("h", data)
    out = array.array("h", (int(s * gain) for s in samples))
    return out.tobytes()


def list_input_devices() -> list[dict]:
    """Enumerate real input devices via PyAudio.

    Skips virtual/proxy devices (Sound Mapper, Primary Sound), Bluetooth
    Hands-Free profile devices (often disconnected), and empty placeholder
    names. The same physical device reported by multiple host APIs is
    consolidated to a single entry (MME truncates names to 31 chars).
    """
    import pyaudio

    audio = pyaudio.PyAudio()
    devices = []
    try:
        for host_api_idx in range(audio.get_host_api_count()):
            ha = audio.get_host_api_info_by_index(host_api_idx)
            for dev_idx in range(ha.get("deviceCount", 0)):
                info = audio.get_device_info_by_host_api_device_index(host_api_idx, dev_idx)
                if int(info.get("maxInputChannels", 0)) <= 0:
                    continue
                name = str(info.get("name", "")).strip()
                lowered = name.lower()
                if not name:
                    continue
                if "sound mapper" in lowered or "primary sound" in lowered:
                    continue
                if "bthhfenum" in lowered:
                    continue
                if "(" in name and ")" in name:
                    inner = name[name.index("(") + 1 : name.index(")")]
                    if not inner.strip():
                        continue
                devices.append(
                    {
                        "index": info.get("index"),
                        "name": name,
                        "channels": int(info.get("maxInputChannels", 0)),
                        "sample_rate": int(info.get("defaultSampleRate", 44100)),
                    }
                )
    finally:
        audio.terminate()

    # Consolidate duplicate host-API entries for the same device (keep full name).
    devices.sort(key=lambda d: -len(d["name"]))
    consolidated = []
    for d in devices:
        base = d["name"].rstrip()
        if base and any(base in c["name"] for c in consolidated):
            continue
        consolidated.append(d)

    consolidated.sort(key=lambda d: int(d["index"] or 0))
    return consolidated


class MicMonitorController(QObject):
    """Owns the monitor thread; call set_device/stop from the GUI thread."""

    level_updated = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread: _MicMonitor | None = None

    def set_device(self, device_index: int | None) -> None:
        self.stop()
        self._thread = _MicMonitor(device_index)
        self._thread.level_updated.connect(self.level_updated)
        self._thread.start()

    def stop(self) -> None:
        if self._thread is not None:
            self._thread.stop()
            self._thread = None


class RecordingWorker(QThread):
    """Real recording via backend Recorder (encrypted .vera output).

    Emits levelUpdated during recording and finished_ok(filepath, key, seconds,
    channels) when stopped. If both patient/psychologist device indexes are given,
    records two mono streams and interleaves them into one stereo stream
    (left = patient, right = psychologist).
    """

    level_updated = Signal(float)
    finished_ok = Signal(str, bytes, int, int)  # filepath, session key, seconds, channels

    def __init__(
        self,
        filepath: str,
        patient_device: int | None = None,
        psychologist_device: int | None = None,
        volume: float = 1.0,
        parent=None,
    ):
        super().__init__(parent)
        self._filepath = filepath
        self._patient_device = patient_device
        self._psychologist_device = psychologist_device
        self._volume = max(0.0, float(volume))
        self._stop_requested = False
        self._started = None

    def request_stop(self):
        self._stop_requested = True

    def _open_input(self, audio, channels: int, device: int | None):
        import pyaudio

        kwargs = dict(
            format=pyaudio.paInt16,
            channels=channels,
            rate=self._sample_rate,
            input=True,
            frames_per_buffer=self._chunk,
        )
        if device is not None:
            kwargs["input_device_index"] = device
        return audio.open(**kwargs)

    def run(self):
        import time

        import pyaudio

        from verbamind.config.config import get_config
        from verbamind.security.encryptor import encrypt_bytes, generate_aes_key

        cfg = get_config()["recording"]
        self._sample_rate = cfg["sample_rate"]
        self._chunk = cfg["chunk_size"]

        audio = pyaudio.PyAudio()
        frames: list[bytes] = []
        key = generate_aes_key()
        channels = 1
        streams = []

        dual = (
            self._patient_device is not None
            and self._psychologist_device is not None
            and self._patient_device != self._psychologist_device
        )

        def open_mono(dev):
            return self._open_input(audio, 1, dev)

        try:
            if dual:
                # Two mono streams interleaved into stereo (L=patient, R=psychologist)
                channels = 2
                s1 = open_mono(self._patient_device)
                s2 = open_mono(self._psychologist_device)
                streams = [s1, s2]
                self._started = time.time()
                import array

                while not self._stop_requested:
                    d1 = s1.read(self._chunk, exception_on_overflow=False)
                    d2 = s2.read(self._chunk, exception_on_overflow=False)
                    a1, a2 = (
                        array.array("h", _apply_gain(d1, self._volume)),
                        array.array("h", _apply_gain(d2, self._volume)),
                    )
                    n = min(len(a1), len(a2))
                    inter = array.array("h")
                    for i in range(n):
                        inter.append(a1[i])
                        inter.append(a2[i])
                    frames.append(inter.tobytes())
                    self.level_updated.emit(max(_rms(d1), _rms(d2)))
            else:
                # Single device (selected mic or system default), fall back to mono
                device = (
                    self._patient_device
                    if self._patient_device is not None
                    else self._psychologist_device
                )
                try:
                    stream = self._open_input(audio, int(cfg["channels"]), device)
                    channels = int(cfg["channels"])
                except OSError:
                    stream = self._open_input(audio, 1, device)
                    channels = 1
                streams = [stream]
                self._started = time.time()
                while not self._stop_requested:
                    data = stream.read(self._chunk, exception_on_overflow=False)
                    frames.append(_apply_gain(data, self._volume))
                    self.level_updated.emit(_rms(data))
        finally:
            for s in streams:
                try:
                    s.stop_stream()
                    s.close()
                except Exception:
                    pass
            audio.terminate()

        encrypted = encrypt_bytes(b"".join(frames), key)
        with open(self._filepath, "wb") as f:
            f.write(encrypted)
        seconds = int(time.time() - self._started)
        self.finished_ok.emit(self._filepath, key, seconds, channels)


class PlaybackWorker(QThread):
    """Decrypts a .vera file in memory and plays it via PyAudio."""

    position_updated = Signal(float, float)  # seconds elapsed, total seconds
    finished_ok = Signal()

    def __init__(
        self,
        filepath: str,
        key: bytes,
        channels: int | None = None,
        speed: float = 1.0,
        parent=None,
    ):
        super().__init__(parent)
        self._filepath = filepath
        self._key = key
        self._channels = channels
        self._speed = max(0.25, float(speed))
        self._stop_requested = False

    def request_stop(self):
        self._stop_requested = True

    def run(self):
        import array
        import time

        import pyaudio

        from verbamind.config.config import get_config
        from verbamind.security.encryptor import decrypt_bytes

        cfg = get_config()["recording"]
        sample_rate, chunk = cfg["sample_rate"], cfg["chunk_size"]
        channels = self._channels or int(cfg["channels"])

        with open(self._filepath, "rb") as f:
            raw = decrypt_bytes(f.read(), self._key)

        samples = array.array("h", raw)
        total = len(samples) / (sample_rate * channels)
        # Playback speed: resample by writing at a scaled rate (simple, artifact-free
        # pitch shift acceptable for preview).
        play_rate = int(sample_rate * self._speed)
        audio = pyaudio.PyAudio()
        try:
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=play_rate,
                output=True,
                frames_per_buffer=chunk,
            )
            try:
                byte_pos = 0
                start = time.time()
                while not self._stop_requested and byte_pos < len(raw):
                    stream.write(raw[byte_pos : byte_pos + chunk * 2 * channels])
                    byte_pos += chunk * 2 * channels
                    self.position_updated.emit(
                        (time.time() - start) * self._speed, total
                    )
            finally:
                stream.stop_stream()
                stream.close()
        finally:
            audio.terminate()
        if not self._stop_requested:
            self.finished_ok.emit()
