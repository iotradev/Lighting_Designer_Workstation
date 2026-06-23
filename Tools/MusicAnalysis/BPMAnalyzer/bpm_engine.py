# -*- coding: utf-8 -*-
"""
BPM检测引擎 v2 - 基于自相关的鲁棒BPM检测
支持: WAV / MP3 / FLAC / OGG / AAC (via miniaudio)
"""
import wave
import numpy as np
from pathlib import Path


class BPMEngine:
    """BPM检测引擎 v2 - 自相关算法"""

    def __init__(self):
        self.sample_rate = 0
        self.samples = None
        self.duration = 0.0
        self.energy_curve = None
        self.onset_times = []
        self.bpm_history = []
        self.current_bpm = 0.0
        self.min_bpm = 60
        self.max_bpm = 200

    def load_audio(self, file_path: str) -> dict:
        """加载音频文件 (WAV/MP3/FLAC/OGG/AAC)"""
        path = Path(file_path)
        ext = path.suffix.lower()
        if ext == '.wav':
            return self._load_wav(file_path)
        elif ext in ('.mp3', '.flac', '.ogg', '.aac', '.m4a', '.wma'):
            return self._load_with_miniaudio(file_path)
        else:
            return {'success': False, 'message': f'不支持的格式: {ext}'}

    def _load_with_miniaudio(self, file_path: str) -> dict:
        """内存解码非WAV格式 (兼容中文路径)"""
        try:
            import miniaudio
        except ImportError:
            return {'success': False, 'message': '缺少miniaudio库'}
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            decoded = miniaudio.decode(data, output_format=miniaudio.SampleFormat.SIGNED16)
            self.sample_rate = decoded.sample_rate
            n_ch = decoded.nchannels
            raw = np.array(decoded.samples, dtype=np.float64) / 32768.0
            if n_ch > 1:
                raw = raw.reshape(-1, n_ch).mean(axis=1)
            self.samples = raw.astype(np.float32)
            self.duration = len(self.samples) / self.sample_rate
            return {'success': True, 'message': '加载成功', 'sample_rate': self.sample_rate,
                    'duration': self.duration, 'channels': n_ch,
                    'samples_count': len(self.samples)}
        except Exception as e:
            return {'success': False, 'message': f'加载失败: {e}'}

    def _load_wav(self, file_path: str) -> dict:
        try:
            with wave.open(file_path, 'rb') as wf:
                self.sample_rate = wf.getframerate()
                n_ch = wf.getnchannels()
                sw = wf.getsampwidth()
                n_frames = wf.getnframes()
                raw = wf.readframes(n_frames)
            if sw == 1:
                s = np.frombuffer(raw, dtype=np.uint8).astype(np.float64) / 128.0 - 1.0
            elif sw == 2:
                s = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
            elif sw == 4:
                s = np.frombuffer(raw, dtype=np.int32).astype(np.float64) / 2147483648.0
            else:
                return {'success': False, 'message': f'不支持{sw*8}bit'}
            if n_ch > 1:
                s = s.reshape(-1, n_ch).mean(axis=1)
            self.samples = s.astype(np.float32)
            self.duration = len(self.samples) / self.sample_rate
            return {'success': True, 'message': '加载成功', 'sample_rate': self.sample_rate,
                    'duration': self.duration, 'channels': n_ch,
                    'samples_count': len(self.samples)}
        except Exception as e:
            return {'success': False, 'message': f'WAV加载失败: {e}'}

    def detect_bpm(self, start_time=0.0, end_time=0.0) -> dict:
        """
        检测BPM - 多频段频谱通量 + 自相关 (v3)
        改进: 低频聚焦、通量平滑、多分辨率、八度校正
        """
        if self.samples is None:
            return {'bpm': 0, 'message': '未加载音频'}

        sr = self.sample_rate
        s0 = int(start_time * sr)
        s1 = int(end_time * sr) if end_time > 0 else len(self.samples)
        s0 = max(0, min(s0, len(self.samples)))
        s1 = max(s0, min(s1, len(self.samples)))
        seg = self.samples[s0:s1]

        if len(seg) < sr:
            return {'bpm': 0, 'message': '音频太短'}

        # ── 1. 多频段频谱通量 ──
        hop = 512
        frame = 2048
        n_frames = (len(seg) - frame) // hop + 1
        if n_frames < 10:
            return {'bpm': 0, 'message': '音频太短'}

        window = np.hanning(frame)
        flux_full = np.zeros(n_frames)
        flux_low = np.zeros(n_frames)   # 低频带 (鼓/贝斯)
        flux_mid = np.zeros(n_frames)   # 中频带 (人声/旋律)
        prev_full = None
        prev_low = None
        prev_mid = None

        bin_hz = sr / frame
        low_cut = int(60 / bin_hz)     # 60Hz
        low_end = int(300 / bin_hz)    # 300Hz
        mid_end = int(4000 / bin_hz)   # 4kHz

        for i in range(n_frames):
            chunk = seg[i*hop : i*hop+frame] * window
            mag = np.abs(np.fft.rfft(chunk))
            if prev_full is not None:
                diff_full = mag - prev_full
                flux_full[i] = np.sum(np.maximum(diff_full, 0))
                # 低频带: 聚焦鼓和贝斯
                diff_low = mag[low_cut:low_end] - prev_full[low_cut:low_end]
                flux_low[i] = np.sum(np.maximum(diff_low, 0))
                # 中频带
                diff_mid = mag[low_end:mid_end] - prev_full[low_end:mid_end]
                flux_mid[i] = np.sum(np.maximum(diff_mid, 0))
            prev_full = mag

        # 归一化
        for flux in (flux_full, flux_low, flux_mid):
            mx = flux.max()
            if mx > 0:
                flux /= mx

        # 加权合成: 低频权重最高 (鼓点检测)
        flux = 0.6 * flux_low + 0.3 * flux_mid + 0.1 * flux_full

        # 平滑通量 (3点移动平均减少噪声)
        if len(flux) > 2:
            flux = np.convolve(flux, [0.25, 0.5, 0.25], mode='same')

        # ── 2. 自适应阈值峰值检测 ──
        win_len = max(5, int(sr / hop * 0.4))
        onsets = []
        for i in range(1, len(flux) - 1):
            lo = max(0, i - win_len)
            hi = min(len(flux), i + win_len + 1)
            local_med = np.median(flux[lo:hi])
            threshold = local_med * 1.1 + 0.01  # 降低阈值减少漏检

            if flux[i] > flux[i-1] and flux[i] >= flux[i+1] and flux[i] > threshold:
                t = (i * hop + s0) / sr
                if not onsets or (t - onsets[-1]) >= 0.12:
                    onsets.append(t)

        self.onset_times = onsets

        # ── 3. 多分辨率自相关 ──
        bpm_candidates = []
        for frame_size in [2048, 4096]:
            n_f = (len(seg) - frame_size) // hop + 1
            if n_f < 10:
                continue
            win = np.hanning(frame_size)
            f = np.zeros(n_f)
            prev = None
            for i in range(n_f):
                c = seg[i*hop : i*hop+frame_size] * win
                m = np.abs(np.fft.rfft(c))
                if prev is not None:
                    d = m - prev
                    f[i] = np.sum(np.maximum(d, 0))
                prev = m
            mx = f.max()
            if mx > 0:
                f /= mx
            bpm_c = self._autocorrelation_bpm(f, sr, hop)
            if bpm_c > 0:
                bpm_candidates.append(bpm_c)

        # 取中位数作为最终结果
        if bpm_candidates:
            bpm = round(float(np.median(bpm_candidates)), 1)
        else:
            bpm = 0.0

        # ── 4. 八度校正 ──
        bpm = self._correct_octave_error(bpm, flux, sr, hop)
        self.current_bpm = bpm

        self.energy_curve = flux
        time_axis = np.arange(len(flux)) * hop / sr + start_time
        conf = self._estimate_confidence(onsets)

        return {
            'bpm': bpm,
            'energy_curve': flux,
            'energy_time_axis': time_axis,
            'onset_times': onsets,
            'confidence': conf,
            'duration': len(seg) / sr
        }

    def _autocorrelation_bpm(self, flux, sr, hop):
        """
        用自相关从频谱通量中提取主节奏周期
        """
        sf = np.maximum(flux - np.mean(flux), 0)
        n = len(sf)
        fft_size = 1
        while fft_size < 2 * n:
            fft_size *= 2

        fft_sf = np.fft.rfft(sf, n=fft_size)
        acf = np.fft.irfft(fft_sf * np.conj(fft_sf))[:n]
        if acf[0] > 0:
            acf /= acf[0]

        min_lag = int(60.0 / self.max_bpm * sr / hop)
        max_lag = int(60.0 / self.min_bpm * sr / hop)
        min_lag = max(2, min_lag)
        max_lag = min(n - 1, max_lag)

        if max_lag <= min_lag:
            return 0.0

        search = acf[min_lag:max_lag]
        if len(search) < 2:
            return 0.0

        peak_idx = np.argmax(search) + min_lag
        peak_val = acf[peak_idx]

        if peak_val < 0.05:
            return 0.0

        if 1 <= peak_idx < len(acf) - 1:
            alpha = acf[peak_idx - 1]
            beta = acf[peak_idx]
            gamma = acf[peak_idx + 1]
            denom = alpha - 2 * beta + gamma
            if abs(denom) > 1e-10:
                shift = 0.5 * (alpha - gamma) / denom
            else:
                shift = 0
            refined_lag = peak_idx + shift
        else:
            refined_lag = peak_idx

        period_sec = refined_lag * hop / sr
        bpm = 60.0 / period_sec if period_sec > 0 else 0

        while bpm > self.max_bpm:
            bpm /= 2
        while bpm < self.min_bpm:
            bpm *= 2

        return round(bpm, 1)

    def _correct_octave_error(self, bpm, flux, sr, hop):
        """
        八度校正: 比较原BPM、半速、双速的自相关峰值强度
        选择置信度最高的那个
        """
        if bpm <= 0:
            return bpm

        sf = np.maximum(flux - np.mean(flux), 0)
        n = len(sf)
        fft_size = 1
        while fft_size < 2 * n:
            fft_size *= 2
        fft_sf = np.fft.rfft(sf, n=fft_size)
        acf = np.fft.irfft(fft_sf * np.conj(fft_sf))[:n]
        if acf[0] > 0:
            acf /= acf[0]

        def acf_strength(b):
            lag = int(60.0 / b * sr / hop)
            if 2 <= lag < len(acf):
                return acf[lag]
            return 0.0

        candidates = [bpm]
        half = bpm / 2
        double = bpm * 2
        if self.min_bpm <= half <= self.max_bpm:
            candidates.append(half)
        if self.min_bpm <= double <= self.max_bpm:
            candidates.append(double)

        best = max(candidates, key=acf_strength)
        return round(best, 1)

    def _estimate_confidence(self, onset_times):
        """估计置信度: 基于自相关峰值强度 + 起始点间隔一致性"""
        if self.current_bpm <= 0:
            return 0.0

        conf = 0.0

        # 1) 起始点间隔一致性 (40%权重)
        if len(onset_times) >= 4:
            intervals = np.diff(onset_times)
            expected = 60.0 / self.current_bpm
            # 计算有多少间隔接近期望值(±20%)
            close = np.sum(np.abs(intervals - expected) < expected * 0.2)
            ratio = close / len(intervals)
            conf += 0.4 * ratio
        elif len(onset_times) >= 2:
            conf += 0.1

        # 2) 自相关峰值强度 (60%权重)
        if hasattr(self, 'energy_curve') and self.energy_curve is not None:
            sf = np.maximum(self.energy_curve - np.mean(self.energy_curve), 0)
            n = len(sf)
            fft_size = 1
            while fft_size < 2 * n:
                fft_size *= 2
            fft_sf = np.fft.rfft(sf, n=fft_size)
            acf = np.fft.irfft(fft_sf * np.conj(fft_sf))[:n]
            if acf[0] > 0:
                acf /= acf[0]
            lag = int(60.0 / self.current_bpm * self.sample_rate / 512)
            if 2 <= lag < len(acf):
                peak_strength = acf[lag]
                conf += 0.6 * min(1.0, peak_strength * 2)

        return round(min(1.0, conf), 2)

    def get_waveform_data(self, max_points=4000):
        """降采样波形用于绘图"""
        if self.samples is None:
            return []
        n = len(self.samples)
        if n <= max_points:
            return self.samples.tolist()
        step = n / max_points
        return [float(self.samples[int(i * step)]) for i in range(max_points)]

    def compute_bpm_curve(self, window_sec=5.0, hop_sec=1.0):
        """滑动窗口BPM曲线"""
        if self.samples is None:
            return {'bpm_curve': [], 'time_axis': []}

        sr = self.sample_rate
        win_samples = int(window_sec * sr)
        hop_samples = int(hop_sec * sr)
        bpms = []
        times = []

        for start in range(0, len(self.samples) - win_samples, hop_samples):
            t = start / sr
            r = self.detect_bpm(t, t + window_sec)
            if r['bpm'] > 0:
                bpms.append(r['bpm'])
                times.append(t + window_sec / 2)

        self.bpm_history = bpms
        return {'bpm_curve': bpms, 'time_axis': times}

    def get_statistics(self) -> dict:
        """从BPM历史中计算统计数据"""
        if not self.bpm_history:
            return {'avg': 0, 'min': 0, 'max': 0, 'std': 0, 'count': 0}
        arr = np.array(self.bpm_history)
        return {
            'avg': round(float(arr.mean()), 1),
            'min': round(float(arr.min()), 1),
            'max': round(float(arr.max()), 1),
            'std': round(float(arr.std()), 1),
            'count': len(arr)
        }

    def export_csv(self, path):
        import csv
        from pathlib import Path as P
        P(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["time_sec", "bpm"])
            for i, bpm in enumerate(self.bpm_history):
                writer.writerow([f"{i:.1f}", bpm])
