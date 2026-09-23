"""Render the complete primary-setting painter acceptance counts, without refitting."""
from pathlib import Path
import hashlib
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'reports/painter_selective_attribution_v1/analysis.json'
EXPECTED = 'f725b32b91f38fa8afd85454b3a6f0c8eb7464f5337b18373ce8c8f53e39fa2c'


def main():
    raw = SOURCE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED:
        raise ValueError('frozen selective analysis changed')
    data = json.loads(raw)['settings']['csd/original/primary']['models']
    expected_models = ['gpt-image-1', 'gpt-image-2', 'gpt-image-2.5-flare',
                       'gpt-image-2.5-sunburst', 'google/gemini-3.1-flash-image',
                       'black-forest-labs/flux.2-max']
    if [row['model'] for row in data] != expected_models:
        raise ValueError('complete six-configuration order required')
    counts = np.array([[p['accepted_count'] for p in row['reference_gate']['per_painter']]
                       for row in data])
    if counts.shape != (6, 4) or np.any((counts < 0) | (counts > 28)):
        raise ValueError('invalid complete painter counts')
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8,
                         'pdf.fonttype': 42, 'ps.fonttype': 42})
    fig, ax = plt.subplots(figsize=(3.25, 2.32))
    fig.subplots_adjust(left=.34, right=.97, top=.88, bottom=.12)
    ax.imshow(counts, cmap='Blues', vmin=0, vmax=28, aspect='auto')
    ax.set_xticks(range(4), ['Monet', 'Sisley', 'Pissarro', 'Cézanne'], fontsize=7)
    ax.xaxis.tick_top()
    ax.set_yticks(range(6), ['GPT Image 1', 'GPT Image 2', 'Flare', 'Sunburst',
                            'Nano Banana 2', 'FLUX.2 Max'])
    ax.tick_params(axis='both', length=0)
    ax.set_xticks(np.arange(-.5, 4, 1), minor=True)
    ax.set_yticks(np.arange(-.5, 6, 1), minor=True)
    ax.grid(which='minor', color='white', linewidth=1.5)
    ax.tick_params(which='minor', length=0)
    for (r, c), n in np.ndenumerate(counts):
        ax.text(c, r, str(n), ha='center', va='center',
                color='white' if n >= 16 else '#111111', fontsize=9)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlabel('Accepted images / 28 per painter', fontsize=8, labelpad=6)
    target = ROOT / 'paper/figures/icml_selective_coverage.pdf'
    fig.savefig(target, metadata={'Creator': 'Matplotlib; frozen primary gate counts',
                                 'CreationDate': None, 'ModDate': None})
    plt.close(fig)
    print('Rendered all 24 primary painter acceptance counts from bound results.')


if __name__ == '__main__':
    main()
