import sys
sys.path.insert(0, r"D:\Lighting_Designer_Workstation\Common")

results = []

# 1. DMX Calculator
try:
    sys.path.insert(0, r"D:\Lighting_Designer_Workstation\Tools\DMX\DMXCalculator")
    from main import DMXCalculator
    results.append("[1] DMXCalculator: OK")
except Exception as e:
    results.append(f"[1] DMXCalculator: FAIL - {type(e).__name__}: {e}")

# 2. Power Calculator Window
try:
    import importlib
    sys.path.insert(0, r"D:\Lighting_Designer_Workstation\Tools\Engineering\PowerCalculator")
    if 'main' in sys.modules:
        del sys.modules['main']
    from main import PowerCalculatorWindow
    results.append("[2] PowerCalculatorWindow: OK")
except Exception as e:
    results.append(f"[2] PowerCalculatorWindow: FAIL - {type(e).__name__}: {e}")

# 3. BPM Engine
try:
    sys.path.insert(0, r"D:\Lighting_Designer_Workstation\Tools\MusicAnalysis\BPMAnalyzer")
    from bpm_engine import BPMEngine
    engine = BPMEngine()
    results.append("[3] BPMEngine: OK")
except Exception as e:
    results.append(f"[3] BPMEngine: FAIL - {type(e).__name__}: {e}")

# 4. Beat Engine
try:
    sys.path.insert(0, r"D:\Lighting_Designer_Workstation\Tools\MusicAnalysis\BeatDetector")
    from beat_engine import BeatEngine
    engine = BeatEngine()
    results.append("[4] BeatEngine: OK")
except Exception as e:
    results.append(f"[4] BeatEngine: FAIL - {type(e).__name__}: {e}")

# 5. Cue classes
try:
    sys.path.insert(0, r"D:\Lighting_Designer_Workstation\Tools\ShowManagement\CueDesigner")
    from cue_engine import Cue, CueList, EffectGenerator
    results.append("[5] CueEngine classes: OK")
except Exception as e:
    results.append(f"[5] CueEngine: FAIL - {type(e).__name__}: {e}")

# 6. ArtNet Listener
try:
    sys.path.insert(0, r"D:\Lighting_Designer_Workstation\Tools\DMX\ArtNetMonitor")
    from artnet_engine import ArtnetListener, UniverseData
    results.append("[6] ArtNetEngine classes: OK")
except Exception as e:
    results.append(f"[6] ArtNetEngine: FAIL - {type(e).__name__}: {e}")

# 7. sACN Engine
try:
    sys.path.insert(0, r"D:\Lighting_Designer_Workstation\Tools\DMX\sACNMonitor")
    from sacn_engine import SACNEngine
    results.append("[7] SACNEngine: OK")
except Exception as e:
    results.append(f"[7] SACNEngine: FAIL - {type(e).__name__}: {e}")

# 8. RDM Engine
try:
    sys.path.insert(0, r"D:\Lighting_Designer_Workstation\Tools\DMX\RDMTool")
    from rdm_engine import RDMEngine
    engine = RDMEngine()
    results.append("[8] RDMEngine: OK")
except Exception as e:
    results.append(f"[8] RDMEngine: FAIL - {type(e).__name__}: {e}")

# 9. Pixel Mapper classes
try:
    sys.path.insert(0, r"D:\Lighting_Designer_Workstation\Tools\VisualPreview\PixelMapper")
    from pixel_engine import PixelGridModel, PatternGenerator
    results.append("[9] PixelEngine classes: OK")
except Exception as e:
    results.append(f"[9] PixelEngine: FAIL - {type(e).__name__}: {e}")

# 10. Visual Simulator classes
try:
    sys.path.insert(0, r"D:\Lighting_Designer_Workstation\Tools\VisualPreview\VisualSimulator")
    from simulator_engine import StageModel, CoordinateTransform
    results.append("[10] SimulatorEngine classes: OK")
except Exception as e:
    results.append(f"[10] SimulatorEngine: FAIL - {type(e).__name__}: {e}")

for r in results:
    print(r)

fails = sum(1 for r in results if "FAIL" in r)
print(f"\nEngine tests: {len(results)-fails}/{len(results)} passed")