# -*- coding: utf-8 -*-
"""
通用音频加载器
支持: WAV / MP3 / FLAC / OGG / AAC / M4A / WMA
使用 miniaudio 解码非WAV格式
"""
import wave
import numpy as np
from pathlib import Path

SUPPORTED_FORMATS = {'.wav', '.mp3', '.flac', '.ogg', '.aac', '.m4a', '.wma'}


def load_audio(file_path: str) -> dict:
    """
    加载音频文件，返回单声道 float32 样本
    返回: {success, samples(np.float32), sample_rate(int), duration(float), channels(int), message(str)}
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext not in SUPPORTED_FORMATS:
        return {'success': False, 'message': f'不支持的格式: {ext}，支持: WAV/MP3/FLAC/OGG/AAC'}

    if ext == '.wav':
        return _load_wav(file_path)
    else:
        return _load_miniaudio(file_path)


def _load_wav(file_path: str) -> dict:
    """加载WAV文件"""
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
            return {'success': False, 'message': f'不支持的采样位深: {sw*8}bit'}

        if n_ch > 1:
            samples = samples.reshape(-1, n_ch).mean(axis=1)

        return {
            'success': True, 'samples': samples, 'sample_rate': sr,
            'duration': len(samples) / sr, 'channels': n_ch, 'message': '加载成功'
        }
    except Exception as e:
        return {'success': False, 'message': f'WAV加载失败: {e}'}


def _load_miniaudio(file_path: str) -> dict:
    """使用miniaudio加载MP3/FLAC/OGG/AAC (内存解码，兼容中文路径)"""
    try:
        import miniaudio
    except ImportError:
        return {'success': False, 'message': '缺少miniaudio库，请运行: pip install miniaudio'}
    try:
        # 先读取文件字节，再内存解码 (避免中文路径问题)
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
            'duration': len(raw) / sr, 'channels': n_ch, 'message': '加载成功'
        }
    except Exception as e:
        return {'success': False, 'message': f'解码失败: {e}'}
