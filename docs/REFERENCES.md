# References

This is the methodological reading list used by the implementation and failure investigation. Links point to publisher, DOI, PubMed, public full text, official product documentation, or exact source revisions where available.

## Positioning and novelty

LatentArtBench does not claim to be the first artist-style benchmark, the first distributional evaluation of art generation, or the first study of artistic mode collapse. Prior work already covers broad art classes, style-transfer metrics, artist prototypes, set-level artist signatures, prompted-artist recognition, AI-versus-human statistics, and artist-level diversity.

The proposed contribution is a measurement-qualified combination of:

1. source-method functional replication;
2. reproduction uncertainty and acquisition-domain controls;
3. held-out and leave-source-out real-group validity;
4. frozen real-only transformations;
5. content-matched prompt distributions;
6. separate fidelity, specificity, coverage, contraction, and coherence outcomes;
7. evaluator-family dependence and narrowly scoped human qualification.

No component is claimed as unprecedented. The contribution succeeds only if the combined protocol changes which generator differences can be interpreted scientifically.

## Core quantitative-art lineage

1. Kim, D., Son, S.-W., & Jeong, H. (2014). Large-Scale Quantitative Analysis of Painting Arts. *Scientific Reports, 4*, 7370. [https://doi.org/10.1038/srep07370](https://doi.org/10.1038/srep07370)

2. Lee, B., Kim, D., Sun, S., Jeong, H., & Park, J. (2018). Heterogeneity in chromatic distance in images and characterization of massive painting data set. *PLOS ONE, 13*(9), e0204430. [DOI](https://doi.org/10.1371/journal.pone.0204430); [PLOS full article and figures](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0204430)

3. Seo, M. K., Shin, I.-S., Han, S. K., Lee, B., & Jeong, H. (2018). Information-Theoretic Analysis of Color Interaction in Artistic Paintings. *New Physics: Sae Mulli, 68*(6), 693–699. [https://doi.org/10.3938/NPSM.68.693](https://doi.org/10.3938/NPSM.68.693)

4. Sigaki, H. Y. D., Perc, M., & Ribeiro, H. V. (2018). History of art paintings through the lens of entropy and complexity. *Proceedings of the National Academy of Sciences, 115*(37), E8585–E8594. [https://doi.org/10.1073/pnas.1800083115](https://doi.org/10.1073/pnas.1800083115)

5. Lee, B., Seo, M. K., Kim, D., Shin, I.-S., Schich, M., Jeong, H., & Han, S. K. (2020). Dissecting landscape art history with information theory. *Proceedings of the National Academy of Sciences, 117*(43), 26580–26590. [https://doi.org/10.1073/pnas.2011927117](https://doi.org/10.1073/pnas.2011927117)

6. Kim, S., Lee, B., & Lee, W. (2025). Investigating the diversity and stylization of contemporary user generated visual arts in the complexity entropy plane. *Scientific Reports, 15*, 22075. [https://doi.org/10.1038/s41598-025-04448-9](https://doi.org/10.1038/s41598-025-04448-9)

7. Tarozo, M. M., Pessa, A. A. B., Zunino, L., Rosso, O. A., Perc, M., & Ribeiro, H. V. (2025). Two-by-two ordinal patterns in art paintings. *PNAS Nexus, 4*(3), pgaf092. [https://doi.org/10.1093/pnasnexus/pgaf092](https://doi.org/10.1093/pnasnexus/pgaf092)

8. Kim, J., Lee, B., You, T., & Yun, J. (2026). Context-aware multimodal AI navigates hidden pathways in five centuries of art evolution. *Proceedings of the National Academy of Sciences, 123*(30), e2517969123. [DOI/version of record](https://doi.org/10.1073/pnas.2517969123); [PubMed record](https://pubmed.ncbi.nlm.nih.gov/42497200/); [public full text and supplement at PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC13416963/)

For implementation scope, Lee et al.'s source behavior is the collapse of the complete mean-rescaled adjacent-pixel distance distribution across the Figure 1 resolutions, not merely evaluation of scalar seamlessness `S`. Its data section also documents exclusions for partial captures, non-rectangular frames, serious damage, and photographs. Kim et al.'s methods specify the SD2 512-base checkpoint, forced 512x512 inputs, an aspect-ratio exclusion at 2, a low-resolution exclusion, and a 16,384-dimensional autoencoder vector. Project-specific K-S margins, deterministic seed repair, PCA limits, and reproduction margins are adaptations rather than claims about either paper.

## Direct AI and human-art comparison

9. Papia, E.-M., Kondi, A., & Constantoudis, V. (2023). Entropy and complexity analysis of AI-generated and human-made paintings. *Chaos, Solitons & Fractals, 170*, 113385. [https://doi.org/10.1016/j.chaos.2023.113385](https://doi.org/10.1016/j.chaos.2023.113385)

## Generative-art benchmarks and style evaluation

10. Liao, P., Li, X., Liu, X., & Keutzer, K. (2022). The ArtBench Dataset: Benchmarking Generative Models with Artworks. [https://arxiv.org/abs/2206.11404](https://arxiv.org/abs/2206.11404)

11. Wright, M., & Ommer, B. (2022). ArtFID: Quantitative Evaluation of Neural Style Transfer. [https://arxiv.org/abs/2207.12280](https://arxiv.org/abs/2207.12280)

12. Somepalli, G., Gupta, A., Gupta, K., Palta, S., Goldblum, M., Geiping, J., Shrivastava, A., & Goldstein, T. (2024). Measuring Style Similarity in Diffusion Models. [https://arxiv.org/abs/2404.01292](https://arxiv.org/abs/2404.01292)

13. Moayeri, M., Basu, S., Balasubramanian, S., Kattakinda, P., Chengini, A., Brauneis, R., & Feizi, S. (2024). Rethinking Artistic Copyright Infringements in the Era of Text-to-Image Generative Models. [https://arxiv.org/abs/2404.08030](https://arxiv.org/abs/2404.08030)

14. Asperti, A., George, F., Marras, T., Stricescu, R. C., & Zanotti, F. (2025). A Critical Assessment of Modern Generative Models’ Ability to Replicate Artistic Styles. [https://arxiv.org/abs/2502.15856](https://arxiv.org/abs/2502.15856)

15. Su, G., Wang, S.-Y., Hertzmann, A., Shechtman, E., Zhu, J.-Y., & Zhang, R. (2025). Identifying Prompted Artist Names from Generated Images. [https://arxiv.org/abs/2507.18633](https://arxiv.org/abs/2507.18633)

16. Frochte, J. (2026). When Style Similarity Scores Fail: Diagnosing Raw CSD Cosine in Artist-Style Evaluation. [https://arxiv.org/abs/2605.09030](https://arxiv.org/abs/2605.09030)

17. Lee, J., Kim, Y., Ali, G., Kim, S., & Hwang, J.-I. (2026). Through Van Gogh’s Eyes: Global Style Transfer with Diffusion Model. [https://arxiv.org/abs/2608.11546](https://arxiv.org/abs/2608.11546)

18. Asperti, A. (2026). On the Separation of Human and AI-Generated Images in CLIP Embedding Space. [https://arxiv.org/abs/2608.25609](https://arxiv.org/abs/2608.25609)

## General distributional evaluation

19. Naeem, M. F., Oh, S. J., Uh, Y., Choi, Y., & Yoo, J. (2020). Reliable Fidelity and Diversity Metrics for Generative Models. *Proceedings of Machine Learning Research, 119*, 7176–7185. [https://proceedings.mlr.press/v119/naeem20a.html](https://proceedings.mlr.press/v119/naeem20a.html)

## Thesis

20. Lee, B. (2021). *Art and Complexity in the Era of Big Data* [Doctoral dissertation, Korea Advanced Institute of Science and Technology]. [KAIST Library record](https://library.kaist.ac.kr/search/detail/view.do?bibCtrlNo=956521)

## Related project code

21. Kim, J., Lee, B., You, T., & Yun, J. *Art History: source code for contextual and formal vector analysis*. Frozen source revision [`7da12358cf34dad2184f357a048c2cf114b3c4e0`](https://github.com/aljinny/art-history/tree/7da12358cf34dad2184f357a048c2cf114b3c4e0); [`make_resize_img.py`](https://github.com/aljinny/art-history/blob/7da12358cf34dad2184f357a048c2cf114b3c4e0/001_Scripts/make_resize_img.py); [`make_a-vector.py`](https://github.com/aljinny/art-history/blob/7da12358cf34dad2184f357a048c2cf114b3c4e0/001_Scripts/make_a-vector.py). The audited nested source-code checkout was clean at this exact revision. It lives under the outer repository's ignored `artifacts/` tree, so that clean status does not mean the checkout, raw paintings, model files, or extracted vectors are committed by this project. No explicit reuse license was identified, so the project treats the source as method evidence and maintains a clean-room implementation.

## Pinned learned-formal model artifacts

22. Stable Diffusion 2 base public mirror, frozen revision [`64bf7b4f10eee35494b38d55c06c0c78cf8b44d0`](https://huggingface.co/Manojb/stable-diffusion-2-base/tree/64bf7b4f10eee35494b38d55c06c0c78cf8b44d0). Full [`512-base-ema.ckpt`](https://huggingface.co/Manojb/stable-diffusion-2-base/blob/64bf7b4f10eee35494b38d55c06c0c78cf8b44d0/512-base-ema.ckpt), SHA-256 `d635794c1fedfdfa261e065370bea59c651fc9bfa65dc6d67ad29e11869a1824`, 5,214,864,007 bytes.

23. Stable Diffusion 2 base VAE [`config.json`](https://huggingface.co/Manojb/stable-diffusion-2-base/blob/64bf7b4f10eee35494b38d55c06c0c78cf8b44d0/vae/config.json), SHA-256 `6b194a1bad5f6ab0431cc254088949b814f75d0c3230483ad8fc6be2cc1495a0`, 716 bytes.

24. Stable Diffusion 2 base VAE [`diffusion_pytorch_model.safetensors`](https://huggingface.co/Manojb/stable-diffusion-2-base/blob/64bf7b4f10eee35494b38d55c06c0c78cf8b44d0/vae/diffusion_pytorch_model.safetensors), SHA-256 `a1d993488569e928462932c8c38a0760b874d166399b14414135bd9c42df5815`, 334,643,276 bytes.

The public mirror is a pinned provenance location. The bitwise mapping check verifies that its 248 VAE tensors equal the corresponding first-stage tensors in the recovered checkpoint; neither the mirror nor that check proves this was the exact file used by Kim et al.

## GPT Image API and transport references

25. OpenAI. *GPT-Image-1 model*. Official OpenAI documentation for the model and `v1/images/generations` endpoint. [https://developers.openai.com/api/docs/models/gpt-image-1](https://developers.openai.com/api/docs/models/gpt-image-1)

26. OpenAI. *GPT-Image-2 model*. Official OpenAI documentation for the model and `v1/images/generations` endpoint. [https://developers.openai.com/api/docs/models/gpt-image-2](https://developers.openai.com/api/docs/models/gpt-image-2)

27. OpenAI. *Image generation*. Official OpenAI guide to image generation. [https://developers.openai.com/api/docs/guides/image-generation](https://developers.openai.com/api/docs/guides/image-generation)

28. `isingmodel/codex-oauth`. User-maintained OpenAI-compatible OAuth proxy used locally for the API integration test. [Repository](https://github.com/isingmodel/codex-oauth); test-time Git HEAD [`7dbbdea0e94a5e542b0af34dcb11c5957b158bed`](https://github.com/isingmodel/codex-oauth/tree/7dbbdea0e94a5e542b0af34dcb11c5957b158bed). The image-support implementation had uncommitted changes, so the commit is only a repository anchor; retained content hashes and request/output evidence, not this commit alone, describe the tested transport.

## Reference policy

This list will be expanded during the systematic literature review. Bibliographic metadata should be checked against the version of record before manuscript submission. Method implementations must cite the exact paper, supplement, code repository and commit, model revision, and artifact hashes used. Public mirrors are provenance locations, not a claim that their maintainers authored the underlying model. Official OpenAI API documentation supports the compatible request shape and named endpoints; it does not document or validate the separate local proxy-to-ChatGPT-Codex route used in this run.
