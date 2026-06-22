"""
节拍检测引擎 - WAV加载、起始检测、峰值拾取、节拍分组
"""
import wave
import struct
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class Beat:
    """单个节拍"""
    timestamp: float      # 秒
    strength: float       # 0.0-1.0 归一化强度
    beat_number: int      # 小节内编号 (1-based)
    bar_number: int       # 小节编号 (1-based)
    is_downbeat: bool     # 是否为强拍


@dataclass
class BeatAnalysisResult:
    """分析结果"""
    beats: List[Beat] = field(default_factory=list)
    bpm: float = 0.0
    time_signature: Tuple[int, int] = (4, 4)
    sample_rate: int = 44100
    duration: float = 0.0

    @property
    def beat_count(self) -> int:
        return len(self.beats)

    @property
    def bar_count(self) -> int:
        if not self.beats:
            return 0
        return self.beats[-1].bar_number


class BeatEngine:
    """节拍检测引擎"""

    def load_audio(self, filepath: str) -> Tuple[np.ndarray, int]:
        """加载音频文件 (WAV/MP3/FLAC/OGG/AAC)"""
        from pathlib import Path
        ext = Path(filepath).suffix.lower()
        if ext == '.wav':
            return self._load_wav_native(filepath)
        else:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))
            from utils.audio_loader import load_audio
            result = load_audio(filepath)
            if not result['success']:
                raise ValueError(result['message'])
            return result['samples'].astype(np.float64), result['sample_rate']

    def _load_wav_native(self, filepath: str) -> Tuple[np.ndarray, int]:
        """加载WAV文件，返回 (单声道float数组, 采样率)"""
        with wave.open(filepath, 'rb') as wf:
            sr = wf.getframerate()
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            n_frames = wf.getnframes()
            raw = wf.readframes(n_frames)

        if sampwidth == 2:
            dtype = np.int16
            max_val = 32768.0
        elif sampwidth == 1:
            dtype = np.uint8
            max_val = 128.0
        elif sampwidth == 4:
            dtype = np.int32
            max_val = 2147483648.0
        else:
            raise ValueError(f"不支持的采样位深: {sampwidth * 8}位")

        samples = np.frombuffer(raw, dtype=dtype).astype(np.float64) / max_val

        if n_channels > 1:
            samples = samples.reshape(-1, n_channels).mean(axis=1)

        return samples, sr

    def detect_beats(self, filepath: str,
                     beats_per_bar: int = 4,
                     sensitivity: float = 0.5) -> BeatAnalysisResult:
        """
        完整节拍检测流程:
        1. 加载音频
        2. 计算频谱通量
        3. 峰值拾取
        4. 估计BPM
        5. 节拍分组与强度分类
        """
        audio, sr = self.load_audio(filepath)
        duration = len(audio) / sr

        # 频谱通量
        flux = self._spectral_flux(audio, sr)

        # 峰值拾取
        peaks, strengths = self._peak_picking(flux, sr, sensitivity)

        if len(peaks) < 2:
            return BeatAnalysisResult(beats=[], bpm=0, time_signature=(beats_per_bar, 4),
                                      sample_rate=sr, duration=duration)

        # 估计BPM
        bpm = self._estimate_bpm(peaks, sr)

        # 分组到小节 & 分类强度
        beats = self._group_beats(peaks, strengths, sr, beats_per_bar)

        return BeatAnalysisResult(
            beats=beats,
            bpm=bpm,
            time_signature=(beats_per_bar, 4),
            sample_rate=sr,
            duration=duration
        )

    def _spectral_flux(self, audio: np.ndarray, sr: int,
                       frame_size: int = 2048, hop_size: int = 512) -> np.ndarray:
        """计算频谱通量 (Spectral Flux)"""
        n_frames = (len(audio) - frame_size) // hop_size + 1
        if n_frames < 1:
            return np.array([])

        # 预计算汉明窗
        window = np.hamming(frame_size)

        flux = np.zeros(n_frames)
        prev_spectrum = None

        for i in range(n_frames):
            start = i * hop_size
            frame = audio[start:start + frame_size] * window
            spectrum = np.abs(np.fft.rfft(frame))

            if prev_spectrum is not None:
                diff = spectrum - prev_spectrum
                # 半波整流 - 只保留能量增加
                flux[i] = np.sum(np.maximum(diff, 0))

            prev_spectrum = spectrum

        # 归一化
        max_flux = np.max(flux)
        if max_flux > 0:
            flux /= max_flux

        return flux

    def _peak_picking(self, flux: np.ndarray, sr: int,
                      sensitivity: float = 0.5,
                      hop_size: int = 512) -> Tuple[np.ndarray, np.ndarray]:
        """
        峰值拾取: 自适应阈值 + 局部最大值检测
        返回: (帧索引数组, 归一化强度数组)
        """
        if len(flux) < 10:
            return np.array([]), np.array([])

        # 自适应阈值 (滑动窗口中位数)
        win_len = int(sr / hop_size * 0.5)  # 0.5秒窗口
        win_len = max(win_len, 5)
        threshold_mult = 1.0 - sensitivity * 0.5  # sensitivity 0-1 -> threshold 1.0-0.5

        peaks = []
        strengths = []

        for i in range(1, len(flux) - 1):
            # 局部窗口
            half_w = win_len // 2
            lo = max(0, i - half_w)
            hi = min(len(flux), i + half_w + 1)
            local_median = np.median(flux[lo:hi])

            threshold = local_median * threshold_mult + 0.02

            # 局部最大值 & 超过阈值
            if flux[i] > flux[i - 1] and flux[i] > flux[i + 1] and flux[i] > threshold:
                peaks.append(i)
                strengths.append(flux[i])

        if not peaks:
            return np.array([]), np.array([])

        peaks = np.array(peaks)
        strengths = np.array(strengths)

        # 去除太近的峰值 (最小间隔100ms)
        min_gap = int(0.1 * sr / hop_size)
        filtered_peaks = [peaks[0]]
        filtered_strengths = [strengths[0]]

        for j in range(1, len(peaks)):
            if peaks[j] - filtered_peaks[-1] >= min_gap:
                filtered_peaks.append(peaks[j])
                filtered_strengths.append(strengths[j])
            elif strengths[j] > filtered_strengths[-1]:
                filtered_peaks[-1] = peaks[j]
                filtered_strengths[-1] = strengths[j]

        peaks = np.array(filtered_peaks)
        strengths = np.array(filtered_strengths)

        # 归一化强度
        if np.max(strengths) > 0:
            strengths = strengths / np.max(strengths)

        return peaks, strengths

    def _estimate_bpm(self, peaks: np.ndarray, sr: int,
                      hop_size: int = 512) -> float:
        """从峰值间隔估计BPM"""
        # 转换为秒
        times = peaks * hop_size / sr
        intervals = np.diff(times)

        if len(intervals) == 0:
            return 0.0

        # 过滤合理间隔 (40-240 BPM -> 0.25-1.5秒)
        valid = intervals[(intervals > 0.25) & (intervals < 1.5)]

        if len(valid) == 0:
            return 0.0

        # 用中位数更稳健
        median_interval = np.median(valid)
        bpm = 60.0 / median_interval

        # 调整到合理范围
        while bpm < 60:
            bpm *= 2
        while bpm > 200:
            bpm /= 2

        return round(bpm, 1)

    def _group_beats(self, peaks: np.ndarray, strengths: np.ndarray,
                     sr: int, beats_per_bar: int,
                     hop_size: int = 512) -> List[Beat]:
        """
        将检测到的峰值分组为小节，标记强拍/弱拍
        """
        timestamps = peaks * hop_size / sr
        n_beats = len(timestamps)

        if n_beats == 0:
            return []

        # 计算期望的节拍间隔
        intervals = np.diff(timestamps)
        if len(intervals) > 0:
            expected_interval = np.median(intervals)
        else:
            expected_interval = 0.5

        # 基于强度识别强拍: 在每个 beats_per_bar 的窗口中，强度最高的是强拍
        beats = []
        beat_in_bar = 0
        bar_number = 1

        for i in range(n_beats):
            beat_in_bar = (i % beats_per_bar) + 1

            if beat_in_bar == 1 and i > 0:
                bar_number = i // beats_per_bar + 1

            # 判断是否为强拍: 小节第一拍 或 强度显著高于同小节平均
            bar_start = (i // beats_per_bar) * beats_per_bar
            bar_end = min(bar_start + beats_per_bar, n_beats)
            bar_strengths = strengths[bar_start:bar_end]
            bar_mean = np.mean(bar_strengths) if len(bar_strengths) > 0 else 0
            is_downbeat = (beat_in_bar == 1) or (strengths[i] > bar_mean * 1.3)

            beats.append(Beat(
                timestamp=round(float(timestamps[i]), 4),
                strength=round(float(strengths[i]), 4),
                beat_number=beat_in_bar,
                bar_number=i // beats_per_bar + 1,
                is_downbeat=bool(is_downbeat)
            ))

        return beats
