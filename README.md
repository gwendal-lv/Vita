# Vita

Vita is a Python module for interacting with the [Vital Synthesizer](https://github.com/mtytel/vital). **It is not an official product related to Vital**. Vita uses [Effort-based versioning](https://jacobtomlinson.dev/effver/).

## Installation

Vita is supported on Linux, macOS, and Windows. Install with `pip`:

```bash
pip install vita
```

## Example

```python
from scipy.io import wavfile
import vita

sample_rate = 44100
bpm = 120.0
note_dur = 1.0
render_dur = 3.0
pitch = 36  # integer
velocity = 0.7  # [0.0 to 1.0]

synth = vita.Synth()
# The initial preset is loaded by default.

synth.set_sample_rate(sample_rate)
synth.set_bpm(bpm)

# Let's make a custom modulation using
# the available modulation sources and destinations.
# These lists are constant.
print("potential sources:", vita.get_modulation_sources())
print("potential destinations:", vita.get_modulation_destinations())

# "lfo_1" is a potential source,
# and "filter_1_cutoff" is a potential destination.
assert synth.connect_modulation("lfo_1", "filter_1_cutoff")

controls = synth.get_controls()
controls["modulation_1_amount"].set(1.0)
controls["filter_1_on"].set(1.0)
val = controls["filter_1_on"].value()
controls["lfo_1_tempo"].set(vita.constants.SyncedFrequency.k1_16)

# Use normalized parameter control (0-1 range, VST-style)
controls["filter_1_cutoff"].set_normalized(0.5)  # Set knob to 50%
print(controls["filter_1_cutoff"].get_normalized())  # Get normalized value

# Get parameter details and display text
info = synth.get_control_details("delay_style")
print(f"Options: {info.options}")  # ["Mono", "Stereo", "Ping Pong", "Mid Ping Pong"]
print(f"Current: {synth.get_control_text('delay_style')}")  # e.g., "Stereo"

# Render audio to numpy array shaped (2, NUM_SAMPLES)
audio = synth.render(pitch, velocity, note_dur, render_dur)

wavfile.write("generated_preset.wav", sample_rate, audio.T)

# Dump current state to JSON text
preset_path = "generated_preset.vital"

json_text = synth.to_json()

with open(preset_path, "w") as f:    
    f.write(json_text)

# Load JSON text
with open(preset_path, "r") as f:
    json_text = f.read()

assert synth.load_json(json_text)

# Or load directly from file
assert synth.load_preset(preset_path)

# Load the initial preset, which also clears modulations
synth.load_init_preset()
# Or just clear modulations.
synth.clear_modulations()
```

### Reproducible renders (`random_seed`)

Vital's random sources (oscillator and unison random phases, random LFOs, random triggers, noise...) are seeded from the `random_seed` of each synth:

```python
synth = vita.Synth()                # random_seed=0 by default
synth = vita.Synth(random_seed=3)   # another random variation of the same preset
print(synth.random_seed)
```

Two synths created with the same `random_seed`, with the same calls made on them (preset, notes, settings), render the same audio, whatever was created before in the process. Different seeds give different audio for presets that use random sources; fully deterministic presets render the same with every seed.

Limitations: the seeds come from a process-wide counter, reset when a synth is constructed. Build and use synths one at a time per process (not concurrently in several threads), and avoid interleaving calls on several synths alive at the same time: voices are created lazily during a render and take the next values of the counter. `vita.get_random_seed_counter()` returns the current counter value (for debugging).

**Behavior change in 0.0.52:** before, the seeds depended on how many synths had been created earlier in the process, so the 1st, 2nd, 3rd... `vita.Synth()` of a process rendered presets with random sources differently. Renders of such presets therefore differ from earlier versions, except that `random_seed=1` gives the same audio as the first `vita.Synth()` of a process in 0.0.51 (observed on the presets we tested). Deterministic presets render exactly as before.

Documentation is not yet automated. Please browse [bindings.cpp](https://github.com/DBraun/Vita/blob/main/src/headless/bindings.cpp) to get a sense of how the code works.

### Issues

If you find any issues with the code, report them at https://github.com/DBraun/Vita.

### Code Licensing
If you are making a proprietary or closed source app and would like to use Vital's source code, contact licensing@vital.audio for non GPLv3 licensing options.

### What can you do with the source
The source code is licensed under the GPLv3. If you download the source or create builds you must comply with that license.

### Things you can't do with this source
 - Do not create an app and distribute it on the iOS app store. The app store is not comptabile with GPLv3 and you'll only get an exception for this if you're paying for a GPLv3 exception for Vital's source (see Code Licensing above).
 - Do not use the name "Vital", "Vital Audio", "Tytel" or "Matt Tytel" for marketing or to name any distribution of binaries built with this source. This source code does not give you rights to infringe on trademarks.
 - Do not connect to any web service at https://vital.audio, https://account.vital.audio or https://store.vital.audio from your own builds. This is against the terms of using those sites.
 - Do not distribute the presets that come with the free version of Vital. They're under a separate license that does not allow redistribution.
