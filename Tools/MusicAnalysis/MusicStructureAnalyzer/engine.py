"""音乐结构分析引擎 - 分析音频结构段落"""

import numpy as np
import wave
from dataclasses import dataclass, field
from typing import List, Tuple
from enum import Enum


class SegmentType(Enum):
    INTRO = "Intro"
    VERSE = "Verse"
    CHORUS = "Chorus"
    BRIDGE = "Bridge"
    DROP = "Drop"
    OUTRO = "Outro"


SEGMENT_COLORS = {
    SegmentType.INTRO: (100, 149, 237),    # 蓝色
    SegmentType.VERSE: (60, 179, 113),     # 绿色
    SegmentType.CHORUS: (255, 165, 0),     # 橙色
    SegmentType.BRIDGE: (147, 112, 219),   # 紫色
    SegmentType.DROP: (220, 20, 60),       # 红色
    SegmentType.OUTRO: (105, 105, 105),    # 灰色
}

LIGHTING_SUGGESTIONS = {
    SegmentType.INTRO: "缓慢渐亮，暖色调淡入，使用慢速渐变效果",
    SegmentType.VERSE: "柔和主色调，中等亮度，缓慢流动效果",
    SegmentType.CHORUS: "高亮度，多彩变化，快节奏闪烁/追逐效果",
    SegmentType.BRIDGE: "变化色调，渐进过渡，光束交叉扫描",
    SegmentType.DROP: "全亮爆闪，快速颜色切换，频闪效果",
    SegmentType.OUTRO: "缓慢暗淡，减少颜色，最终渐灭效果",
}


@dataclass
class AudioSegment:
    segment_type: SegmentType
    start_time: float
    end_time: float
    energy_level: float
    spectral_centroid: float
    lighting_suggestion: str = ""

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


class MusicStructureEngine:
    """音乐结构分析引擎"""

    def __init__(self):
        self.sample_rate = 44100
        self.audio_data = None
        self.segments: List[AudioSegment] = []
        self.energy_curve: List[float] = []
        self.spectral_curve: List[float] = []

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
            return {"duration": result['duration'], "sample_rate": self.sample_rate,
                    "samples": len(self.audio_data), "channels": result['channels']}

    def _load_wav_native(self, filepath: str) -> dict:
        """加载WAV文件"""
        with wave.open(filepath, 'rb') as wf:
            self.sample_rate = wf.getframerate()
            n_channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            n_frames = wf.getnframes()
            raw_data = wf.readframes(n_frames)

        if sample_width == 2:
            dtype = np.int16
        elif sample_width == 4:
            dtype = np.int32
        else:
            dtype = np.uint8

        audio = np.frombuffer(raw_data, dtype=dtype).astype(np.float64)
        if n_channels > 1:
            audio = audio.reshape(-1, n_channels).mean(axis=1)

        # 归一化
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val

        self.audio_data = audio
        duration = len(audio) / self.sample_rate

        return {
            "duration": duration,
            "sample_rate": self.sample_rate,
            "samples": len(audio),
            "channels": n_channels,
        }

    def compute_rms_energy(self, frame_size: int = 2048, hop_size: int = 1024) -> List[float]:
        """计算RMS能量曲线"""
        if self.audio_data is None:
            return []

        energy = []
        for i in range(0, len(self.audio_data) - frame_size, hop_size):
            frame = self.audio_data[i:i + frame_size]
            rms = np.sqrt(np.mean(frame ** 2))
            energy.append(rms)

        self.energy_curve = energy
        return energy

    def compute_spectral_centroid(self, frame_size: int = 2048, hop_size: int = 1024) -> List[float]:
        """计算频谱质心曲线"""
        if self.audio_data is None:
            return []

        centroids = []
        freqs = np.fft.rfftfreq(frame_size, 1.0 / self.sample_rate)

        for i in range(0, len(self.audio_data) - frame_size, hop_size):
            frame = self.audio_data[i:i + frame_size]
            windowed = frame * np.hanning(len(frame))
            spectrum = np.abs(np.fft.rfft(windowed))
            total_energy = np.sum(spectrum)
            if total_energy > 0:
                centroid = np.sum(freqs * spectrum) / total_energy
            else:
                centroid = 0.0
            centroids.append(centroid)

        self.spectral_curve = centroids
        return centroids

    def analyze_structure(self, min_segment_duration: float = 8.0) -> List[AudioSegment]:
        """分析音乐结构，划分段落"""
        if self.audio_data is None:
            return []

        self.compute_rms_energy()
        self.compute_spectral_centroid()

        if not self.energy_curve:
            return []

        # 平滑能量曲线
        window = max(1, len(self.energy_curve) // 100)
        smoothed_energy = self._smooth(self.energy_curve, window)
        smoothed_spectral = self._smooth(self.spectral_curve, window) if self.spectral_curve else [0] * len(smoothed_energy)

        # 归一化
        max_e = max(smoothed_energy) if max(smoothed_energy) > 0 else 1.0
        max_s = max(smoothed_spectral) if max(smoothed_spectral) > 0 else 1.0
        norm_energy = [e / max_e for e in smoothed_energy]
        norm_spectral = [s / max_s for s in smoothed_spectral]

        hop_time = 1024.0 / self.sample_rate  # 每帧时间
        total_duration = len(self.audio_data) / self.sample_rate

        # 计算全局统计
        mean_energy = np.mean(norm_energy)
        std_energy = np.std(norm_energy)

        # 使用自适应阈值划分段落
        segments = []
        min_frames = max(1, int(min_segment_duration / hop_time))

        # 检测能量变化边界
        boundaries = [0]
        i = min_frames
        while i < len(norm_energy) - min_frames:
            # 检查前后窗口的能量差异
            look_back = min(min_frames, i)
            look_fwd = min(min_frames, len(norm_energy) - i)
            back_mean = np.mean(norm_energy[max(0, i - look_back):i])
            fwd_mean = np.mean(norm_energy[i:i + look_fwd])

            if abs(fwd_mean - back_mean) > std_energy * 0.5:
                boundaries.append(i)
                i += min_frames
            else:
                i += 1

        boundaries.append(len(norm_energy))

        # 为每个段落分类
        for idx in range(len(boundaries) - 1):
            start_frame = boundaries[idx]
            end_frame = boundaries[idx + 1]
            seg_energy = np.mean(norm_energy[start_frame:end_frame])
            seg_spectral = np.mean(norm_spectral[start_frame:end_frame])

            start_time = start_frame * hop_time
            end_time = end_frame * hop_time

            if end_time - start_time < min_segment_duration * 0.5:
                continue

            seg_type = self._classify_segment(
                seg_energy, seg_spectral, mean_energy, std_energy,
                start_time, total_duration
            )

            segment = AudioSegment(
                segment_type=seg_type,
                start_time=start_time,
                end_time=end_time,
                energy_level=seg_energy,
                spectral_centroid=seg_spectral,
                lighting_suggestion=LIGHTING_SUGGESTIONS[seg_type],
            )
            segments.append(segment)

        # 确保首尾段落正确
        if segments:
            segments[0].segment_type = SegmentType.INTRO
            segments[0].lighting_suggestion = LIGHTING_SUGGESTIONS[SegmentType.INTRO]
            segments[-1].segment_type = SegmentType.OUTRO
            segments[-1].lighting_suggestion = LIGHTING_SUGGESTIONS[SegmentType.OUTRO]

        self.segments = segments
        return segments

    def _classify_segment(self, energy, spectral, mean_e, std_e, start_time, total_dur):
        """根据能量和频谱特征分类段落类型"""
        position_ratio = start_time / total_dur if total_dur > 0 else 0

        # 开头部分 -> Intro
        if position_ratio < 0.1:
            return SegmentType.INTRO
        # 结尾部分 -> Outro
        if position_ratio > 0.9:
            return SegmentType.OUTRO

        # 高能量 + 高频谱 -> Chorus
        if energy > mean_e + std_e * 0.5 and spectral > 0.5:
            return SegmentType.CHORUS
        # 非常高能量 + 高频谱 -> Drop
        if energy > mean_e + std_e and spectral > 0.6:
            return SegmentType.DROP
        # 低能量 -> Verse
        if energy < mean_e - std_e * 0.3:
            return SegmentType.VERSE
        # 中等能量 + 频谱变化 -> Bridge
        if energy > mean_e and spectral > 0.4:
            return SegmentType.BRIDGE

        return SegmentType.VERSE

    def _smooth(self, data: list, window: int) -> list:
        """简单滑动平均平滑"""
        if window <= 1 or len(data) <= window:
            return list(data)
        kernel = np.ones(window) / window
        smoothed = np.convolve(data, kernel, mode='same')
        return smoothed.tolist()

    def export_csv(self, filepath: str):
        """导出结构段落到CSV"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("段落类型,开始时间(秒),结束时间(秒),持续时间(秒),能量水平,频谱质心,灯光建议\n")
            for seg in self.segments:
                f.write(f"{seg.segment_type.value},"
                        f"{seg.start_time:.2f},"
                        f"{seg.end_time:.2f},"
                        f"{seg.duration:.2f},"
                        f"{seg.energy_level:.4f},"
                        f"{seg.spectral_centroid:.1f},"
                        f"\"{seg.lighting_suggestion}\"\n")
