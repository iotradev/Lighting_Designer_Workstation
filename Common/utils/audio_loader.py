# -*- coding: utf-8 -*-
"""

: WAV / MP3 / FLAC / OGG / AAC / M4A / WMA
 miniaudio WAV
"""
import wave
import numpy as np
from pathlib import Path

SUPPORTED_FORMATS = {'.wav', '.mp3', '.flac', '.ogg', '.aac', '.m4a', '.wma'}


def load_audio(file_path: str) -> dict:
    """
     float32 
    : {success, samples(np.float32), sample_rate(int), duration(float), channels(int), message(str)}
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext not in SUPPORTED_FORMATS:
        return {'success': False, 'message': f': {ext}: WAV/MP3/FLAC/OGG/AAC'}

    if ext == '.wav':
        return _load_wav(file_path)
    else:
        return _load_miniaudio(file_path)


def _load_wav(file_path: str) -> dict:
    """WAV"""
    try:
        with wave.open(file_path, 'rb') as wf:
            sr = wf.getframerate()
            n_ch = wf.getnchannels()
            sw = wf.getsampwidth()
            n_frames = wf.getnframes()
            raw = wf.readframes(n_frames)

        if sw == 1:
            samples = np.frombuffer(raw, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0
        elif sw == 2:
            samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        elif sw == 4:
            samples = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
        else:
            return {'success': False, 'message': f': {sw*8}bit'}

        if n_ch > 1:
            samples = samples.reshape(-1, n_ch).mean(axis=1)

        return {
            'success': True, 'samples': samples, 'sample_rate': sr,
            'duration': len(samples) / sr, 'channels': n_ch, 'message': ''
        }
    except Exception as e:
        return {'success': False, 'message': f'WAV: {e}'}


def _load_miniaudio(file_path: str) -> dict:
    """miniaudioMP3/FLAC/OGG/AAC ()"""
    try:
        import miniaudio
    except ImportError:
        return {'success': False, 'message': 'miniaudio: pip install miniaudio'}
    try:
        #  ()
        with open(file_path, 'rb') as f:
            data = f.read()
        decoded = miniaudio.decode(data, output_format=miniaudio.SampleFormat.SIGNED16)
        sr = decoded.sample_rate
        n_ch = decoded.nchannels
        raw = np.array(decoded.samples, dtype=np.float32) / 32768.0
        if n_ch > 1:
            raw = raw.reshape(-1, n_ch).mean(axis=1)
        return {
            'success': True, 'samples': raw, 'sample_rate': sr,
            'duration': len(raw) / sr, 'channels': n_ch, 'message': ''
        }
    except Exception as e:
        return {'success': False, 'message': f': {e}'}
