"""情绪分析引擎 - 分析音频情绪特征"""

import numpy as np
import wave
from dataclasses import dataclass
from typing import List
from enum import Enum


class MoodZone(Enum):
    CALM = "平静"
    MEDIUM = "中等"
    HIGH_ENERGY = "高能量"


MOOD_COLORS = {
    MoodZone.CALM: (70, 130, 180),        # 钢蓝色 - 平静
    MoodZone.MEDIUM: (255, 165, 0),       # 橙色 - 中等
    MoodZone.HIGH_ENERGY: (220, 20, 60),  # 红色 - 高能量
}

LIGHTING_SUGGESTIONS = {
    MoodZone.CALM: "柔和冷色调（蓝/青/白），低亮度，缓慢渐变，使用柔光效果",
    MoodZone.MEDIUM: "暖色调（橙/黄/粉），中等亮度，适度流动和呼吸效果",
    MoodZone.HIGH_ENERGY: "高饱和色彩（红/紫/白），高亮度，快速变化、频闪、追逐效果",
}


@dataclass
class MoodFrame:
    time: float
    rms_energy: float
    spectral_centroid: float
    zero_crossing_rate: float
    mood_zone: MoodZone


class MoodEngine:
    """情绪分析引擎"""

    def __init__(self):
        self.sample_rate = 44100
        self.audio_data = None
        self.frames: List[MoodFrame] = []
        self.rms_curve: List[float] = []
        self.centroid_curve: List[float] = []
        self.zcr_curve: List[float] = []

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
                    "samples": len(self.audio_data)}

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

        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val

        self.audio_data = audio
        return {
            "duration": len(audio) / self.sample_rate,
            "sample_rate": self.sample_rate,
            "samples": len(audio),
        }

    def analyze(self, frame_size: int = 2048, hop_size: int = 1024) -> List[MoodFrame]:
        """完整分析：RMS能量、频谱质心、过零率"""
        if self.audio_data is None:
            return []

        freqs = np.fft.rfftfreq(frame_size, 1.0 / self.sample_rate)
        rms_list = []
        centroid_list = []
        zcr_list = []

        for i in range(0, len(self.audio_data) - frame_size, hop_size):
            frame = self.audio_data[i:i + frame_size]

            # RMS能量
            rms = np.sqrt(np.mean(frame ** 2))
            rms_list.append(rms)

            # 频谱质心
            windowed = frame * np.hanning(len(frame))
            spectrum = np.abs(np.fft.rfft(windowed))
            total = np.sum(spectrum)
            centroid = np.sum(freqs * spectrum) / total if total > 0 else 0
            centroid_list.append(centroid)

            # 过零率
            signs = np.sign(frame)
            zcr = np.sum(np.abs(np.diff(signs))) / (2 * len(frame))
            zcr_list.append(zcr)

        self.rms_curve = rms_list
        self.centroid_curve = centroid_list
        self.zcr_curve = zcr_list

        # 计算阈值
        max_rms = max(rms_list) if max(rms_list) > 0 else 1.0
        norm_rms = [r / max_rms for r in rms_list]

        mean_rms = np.mean(norm_rms)
        std_rms = np.std(norm_rms)

        hop_time = hop_size / self.sample_rate
        self.frames = []

        for idx in range(len(rms_list)):
            time = idx * hop_time
            norm_e = norm_rms[idx]

            # 分类情绪区间
            if norm_e > mean_rms + std_rms * 0.5:
                zone = MoodZone.HIGH_ENERGY
            elif norm_e < mean_rms - std_rms * 0.3:
                zone = MoodZone.CALM
            else:
                zone = MoodZone.MEDIUM

            self.frames.append(MoodFrame(
                time=time,
                rms_energy=rms_list[idx],
                spectral_centroid=centroid_list[idx],
                zero_crossing_rate=zcr_list[idx],
                mood_zone=zone,
            ))

        return self.frames

    def get_mood_summary(self) -> dict:
        """获取情绪分布统计"""
        if not self.frames:
            return {}

        counts = {z: 0 for z in MoodZone}
        for f in self.frames:
            counts[f.mood_zone] += 1

        total = len(self.frames)
        return {z.value: round(c / total * 100, 1) for z, c in counts.items()}

    def get_mood_segments(self) -> List[dict]:
        """合并连续相同情绪区间为段落"""
        if not self.frames:
            return []

        segments = []
        current_zone = self.frames[0].mood_zone
        start_time = self.frames[0].time
        energies = [self.frames[0].rms_energy]

        for f in self.frames[1:]:
            if f.mood_zone != current_zone:
                segments.append({
                    "zone": current_zone,
                    "start_time": start_time,
                    "end_time": f.time,
                    "avg_energy": np.mean(energies),
                    "suggestion": LIGHTING_SUGGESTIONS[current_zone],
                })
                current_zone = f.mood_zone
                start_time = f.time
                energies = [f.rms_energy]
            else:
                energies.append(f.rms_energy)

        # 最后一段
        segments.append({
            "zone": current_zone,
            "start_time": start_time,
            "end_time": self.frames[-1].time,
            "avg_energy": np.mean(energies),
            "suggestion": LIGHTING_SUGGESTIONS[current_zone],
        })

        return segments

    def export_csv(self, filepath: str):
        """导出情绪时间线到CSV"""
        segments = self.get_mood_segments()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("情绪区间,开始时间(秒),结束时间(秒),持续时间(秒),平均能量,灯光建议\n")
            for seg in segments:
                dur = seg["end_time"] - seg["start_time"]
                f.write(f"{seg['zone'].value},"
                        f"{seg['start_time']:.2f},"
                        f"{seg['end_time']:.2f},"
                        f"{dur:.2f},"
                        f"{seg['avg_energy']:.4f},"
                        f"\"{seg['suggestion']}\"\n")
