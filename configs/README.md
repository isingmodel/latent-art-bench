# Study configurations

These files record the inputs used by completed study stages. They are not
editable templates for repeating or extending a terminal collection.

| Directory | Contents |
|---|---|
| `painter_distribution_study_v1/` | Earlier controlled naming study: brief inventory, generation design, technical pilots and diagnostic selection |
| `painter_responsiveness_v1/` | FLUX.2 Max mechanism diagnostic: painter clauses against a requested color change (192-image cap) |
| `painter_responsiveness_v2/` | GPT Image 2 computational palette intervention; later clause and replication studies bind this file |
| `painter_prompt_study_v1/` | Earlier 1,920-slot prompt experiment |
| `painter_prompt_supplement_v1/` | Post-registration missingness analysis of the prompt experiment |
| `painter_feature_generation_v2/` | Historical SD-Turbo and OAuth generation settings |
| `painter_feature_generation_v1/` | Historical metadata-discovery and collection census contracts |

The six-model study behind the current manuscripts has no directory here: its
scenes, models and budget are fixed in
[painter_specificity_v1/study.py](../src/latent_art_bench/painter_specificity_v1/study.py),
narrowed to 14 scenes by [painter_specificity_v2](../src/latent_art_bench/painter_specificity_v2/study.py)
and described in its [protocol](../studies/painter_specificity_v2/PROTOCOL.md).
The distribution revision and the ICML-era analyses likewise use frozen plans
and retained numeric inputs rather than a collection configuration. See the
[analysis catalog](../docs/ANALYSES.md) for each study's computation, plotting
and replay command.

Every executed configuration must remain at its original path and byte content.
Corrections or additional data require a new scope and configuration, with the
relevant authorization before network or generation work. No collector is active;
[current status](../docs/STATUS.md) is the operational authority.
