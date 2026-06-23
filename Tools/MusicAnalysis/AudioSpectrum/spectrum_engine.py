"""
频谱分析引擎 - 音频频谱分析核心模块
"""
import wave
import numpy as np
from collections import deque
from typing import Optional, List, Tuple
from dataclasses import dataclass, field


# 频段定义 (名称, 最低频率, 最高频率)
FREQUENCY_BANDS = [
    ("Sub-bass", 20, 60),
    ("Bass", 60, 250),
    ("Low-mid", 250, 500),
    ("Mid", 500, 2000),
    ("High-mid", 2000, 4000),
    ("High", 4000, 8000),
    ("Ultra-high", 8000, 20000),
]


@dataclass
class SpectrumFrame:
    """一帧频谱数据"""
    frequencies: np.ndarray       # 频率轴
    magnitudes: np.ndarray        # 幅值谱 (dB)
    band_energies: List[float]    # 各频段能量 (0~1)
    peak_frequency: float         # 峰值频率 (Hz)
    peak_magnitude: float         # 峰值幅值 (dB)


class SpectrumEngine:
    """频谱分析引擎"""

    def __init__(self, fft_size: int = 2048):
        self.fft_size = fft_size
        self.sample_rate: int = 0
        self.audio_data: Optional[np.ndarray] = None
        self.total_frames: int = 0
        self.channels: int = 1
        self.current_position: int = 0

        # 瀑布图数据缓冲区
        self.waterfall_buffer: deque = deque(maxlen=self.waterfall_max_lines)
        self.waterfall_max_lines = 200

        # Hanning窗函数
        self._window = np.hanning(fft_size)

    def set_fft_size(self, size: int):
        """设置FFT大小"""
        self.fft_size = size
        self._window = np.hanning(size)

    def load_audio(self, filepath: str) -> dict:
        """加载音频文件 (WAV/MP3/FLAC/OGG/AAC)"""
        from pathlib import Path
        ext = Path(filepath).suffix.lower()
        if ext == '.wav':
            return self._load_wav_native(filepath)
        else:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))
            from utils.audio_loader import load_audio as _load
            result = _load(filepath)
            if not result['success']:
                raise ValueError(result['message'])
            self.audio_data = result['samples'].astype(np.float64)
            self.sample_rate = result['sample_rate']
            self.total_frames = len(self.audio_data)
            self.channels = result['channels']
            self.current_position = 0
            self.waterfall_buffer.clear()
            return {"sample_rate": self.sample_rate, "total_frames": self.total_frames,
                    "channels": self.channels, "duration": result['duration']}

    def _load_wav_native(self, filepath: str) -> dict:
        """加载WAV文件，返回音频信息"""
        with wave.open(filepath, 'rb') as wf:
            self.channels = wf.getnchannels()
            self.sample_rate = wf.getframerate()
            self.total_frames = wf.getnframes()
            raw = wf.readframes(self.total_frames)
            sampwidth = wf.getsampwidth()

        # 转换为numpy数组
        if sampwidth == 2:
            data = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
        elif sampwidth == 4:
            data = np.frombuffer(raw, dtype=np.int32).astype(np.float64) / 2147483648.0
        elif sampwidth == 1:
            data = (np.frombuffer(raw, dtype=np.uint8).astype(np.float64) - 128.0) / 128.0
        else:
            raise ValueError(f"不支持的采样位深: {sampwidth * 8}位")

        # 多声道取均值
        if self.channels > 1:
            data = data.reshape(-1, self.channels).mean(axis=1)

        self.audio_data = data
        self.current_position = 0
        self.waterfall_buffer.clear()

        return {
            "sample_rate": self.sample_rate,
            "total_frames": self.total_frames,
            "channels": self.channels,
            "duration": self.total_frames / self.sample_rate,
        }

    def get_audio_info(self) -> Optional[dict]:
        """获取当前加载音频的信息"""
        if self.audio_data is None:
            return None
        return {
            "sample_rate": self.sample_rate,
            "total_frames": self.total_frames,
            "channels": self.channels,
            "duration": self.total_frames / self.sample_rate,
        }

    def process_frame(self) -> Optional[SpectrumFrame]:
        """
        处理当前音频位置的一帧数据，返回频谱信息
        """
        if self.audio_data is None:
            return None

        # 取一段数据
        end_pos = self.current_position + self.fft_size
        if end_pos > len(self.audio_data):
            self.current_position = 0
            end_pos = self.fft_size

        chunk = self.audio_data[self.current_position:end_pos].copy()
        self.current_position = end_pos

        # 窗函数
        windowed = chunk * self._window[:len(chunk)]

        # FFT
        fft_result = np.fft.rfft(windowed)
        magnitudes = np.abs(fft_result)
        # 转dB, 避免log(0)
        magnitudes_db = 20 * np.log10(magnitudes + 1e-10)

        # 频率轴
        freqs = np.fft.rfftfreq(self.fft_size, 1.0 / self.sample_rate)

        # 计算频段能量
        band_energies = self._calc_band_energies(freqs, magnitudes)

        # 峰值检测
        peak_idx = np.argmax(magnitudes[1:]) + 1  # 跳过DC分量
        peak_freq = float(freqs[peak_idx])
        peak_mag = float(magnitudes_db[peak_idx])

        frame = SpectrumFrame(
            frequencies=freqs,
            magnitudes=magnitudes_db,
            band_energies=band_energies,
            peak_frequency=peak_freq,
            peak_magnitude=peak_mag,
        )

        # 更新瀑布图缓冲
        self.waterfall_buffer.append(magnitudes_db.copy())

        return frame

    def _calc_band_energies(self, freqs: np.ndarray, magnitudes: np.ndarray) -> List[float]:
        """计算各频段的归一化能量 (0~1)"""
        energies = []
        mag_max = magnitudes.max() if magnitudes.max() > 0 else 1.0

        for name, f_low, f_high in FREQUENCY_BANDS:
            mask = (freqs >= f_low) & (freqs <= f_high)
            if mask.any():
                band_energy = np.mean(magnitudes[mask]) / mag_max
            else:
                band_energy = 0.0
            energies.append(float(np.clip(band_energy, 0.0, 1.0)))

        return energies

    def get_waterfall_data(self) -> Optional[np.ndarray]:
        """获取瀑布图数据矩阵 (行=时间, 列=频率), 值为dB"""
        if not self.waterfall_buffer:
            return None
        return np.array(self.waterfall_buffer)

    def seek(self, position: int):
        """跳转到指定采样位置"""
        if self.audio_data is not None:
            self.current_position = max(0, min(position, len(self.audio_data) - self.fft_size))

    def reset(self):
        """重置播放位置和缓冲"""
        self.current_position = 0
        self.waterfall_buffer.clear()
