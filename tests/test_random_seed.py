"""Reproducibility of renders that use Vital's random generators (random phases, random LFOs,
noise...). See the random_seed argument of vita.Synth.

Renders are made in subprocesses: the bug being tested depended on what had been created before
in the process (including lazily built static tables), so each check needs a fresh process.
"""
import json
import os
import pickle
import subprocess
import sys

import vita

# Renders a patch that uses random sources (unison random phases, random LFO). Before vita
# 0.0.52, its audio depended on the number of synths created earlier in the process.
_RENDER_SCRIPT = r"""
import hashlib, json, sys
import numpy as np
import vita

seeds = json.loads(sys.argv[1])
pitches = np.array([48, 55, 60, 64])
velocities = np.full(4, 0.8, dtype=np.float32)
starts = 0.4 * np.arange(4, dtype=np.float32)
durations = np.full(4, 0.6, dtype=np.float32)
hashes = []
for seed in seeds:
    synth = vita.Synth() if seed is None else vita.Synth(random_seed=seed)
    synth.set_sample_rate(48000)
    synth.set_bpm(120.0)
    controls = synth.get_controls()
    controls["osc_1_unison_voices"].set(8)
    controls["osc_1_random_phase"].set(1.0)
    controls["filter_1_on"].set(1.0)
    assert synth.connect_modulation("random_1", "filter_1_cutoff")
    controls["modulation_1_amount"].set(0.8)
    audio = synth.render_notes(pitches, velocities, starts, durations, 2.5)
    assert np.abs(audio).max() > 1e-3, "silent render"
    hashes.append(hashlib.md5(np.ascontiguousarray(audio).tobytes()).hexdigest())
    del synth
print(json.dumps(hashes))
"""


def _render_hashes_in_new_process(seeds):
    """Creates one new synth per seed (None: default seed), in order, in a new Python process.
    Returns the md5 hashes of the rendered audio."""
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(p for p in sys.path if p)
    result = subprocess.run(
        [sys.executable, "-c", _RENDER_SCRIPT, json.dumps(seeds)],
        capture_output=True, text=True, env=env, cwd=os.getcwd(), timeout=600,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout.strip().splitlines()[-1])


def test_successive_synths_render_identically():
    # Includes the very first synth of the process (which builds the static tables)
    hashes = _render_hashes_in_new_process([None, None, None])
    assert len(set(hashes)) == 1, hashes
    # Same results in another process
    assert _render_hashes_in_new_process([None, None]) == hashes[:2]


def test_explicit_seed():
    hashes = _render_hashes_in_new_process([0, 1, 1, 0, 2, None])
    h0, h1, h1b, h0b, h2, h_default = hashes
    assert h0 == h0b == h_default  # the default seed is 0
    assert h1 == h1b
    assert len({h0, h1, h2}) == 3  # different seeds give different audio


def test_seed_counter_and_property():
    synth = vita.Synth(random_seed=1234)
    assert synth.random_seed == 1234
    # The counter restarts at random_seed, then one value is taken by each random generator
    assert vita.get_random_seed_counter() > 1234
    assert vita.Synth().random_seed == 0


def test_pickle_keeps_seed():
    synth = vita.Synth(random_seed=42)
    restored = pickle.loads(pickle.dumps(synth))
    assert restored.random_seed == 42

    def settings_without_sample(synth):
        # The sample data isn't bit-exact through a to_json/load_json round trip (unrelated
        # to random seeds, already the case before 0.0.52)
        settings = json.loads(synth.to_json())["settings"]
        del settings["sample"]
        return settings

    assert settings_without_sample(restored) == settings_without_sample(synth)
