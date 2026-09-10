# Evaluation-centered scaling of painter-naming feature clouds

Post-result successor to pngv1-20260910. The added map uses the evaluation-free mean and unchanged original training displacement/scalar. It is cohort adaptation, not unchanged pointwise transfer. No new data or hypothesis tests.

The centered-minus-shift comparison changes scale at an identical weighted mean. Old-scale-minus-centered changes only the origin-induced mean offset at identical centered shape. These add along a specified algebraic path, not a unique causal decomposition. Positive values mean the first map has greater energy.

No corrected conditional-mean residual is estimated for the new map: evaluation-free centering induces dependence across residual repetitions.

| Cohort | Pipeline | View | Service | Painter | Shift | Old scale | Centered scale | Named | Centered−shift | Old−centered | Named−centered |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| original | common_square | all31 | nano_banana_2 | claude_monet | 3.999729 | 3.995194 | 4.175344 | 3.637409 | 0.175616 | -0.180150 | -0.537935 |
| original | common_square | all31 | nano_banana_2 | paul_cezanne | 3.169613 | 3.282640 | 3.425578 | 3.065710 | 0.255965 | -0.142938 | -0.359869 |
| original | common_square | all31 | flux_2_max | claude_monet | 1.886554 | 1.970968 | 2.415230 | 1.657801 | 0.528676 | -0.444262 | -0.757429 |
| original | common_square | all31 | flux_2_max | paul_cezanne | 1.174242 | 1.191911 | 1.407113 | 1.005826 | 0.232871 | -0.215201 | -0.401286 |
| original | common_square | all31 | oauth_gpt_image_2 | claude_monet | 2.785428 | 2.844394 | 3.074578 | 2.681161 | 0.289149 | -0.230184 | -0.393417 |
| original | common_square | all31 | oauth_gpt_image_2 | paul_cezanne | 2.040480 | 2.119966 | 2.202574 | 2.094188 | 0.162094 | -0.082608 | -0.108386 |
| original | jpeg90_512 | all31 | nano_banana_2 | claude_monet | 4.225142 | 4.215200 | 4.396274 | 3.843046 | 0.171132 | -0.181074 | -0.553228 |
| original | jpeg90_512 | all31 | nano_banana_2 | paul_cezanne | 3.426066 | 3.577874 | 3.745129 | 3.307428 | 0.319063 | -0.167255 | -0.437701 |
| original | jpeg90_512 | all31 | flux_2_max | claude_monet | 1.954449 | 2.030419 | 2.469354 | 1.717022 | 0.514905 | -0.438935 | -0.752332 |
| original | jpeg90_512 | all31 | flux_2_max | paul_cezanne | 1.244861 | 1.285884 | 1.502149 | 1.077250 | 0.257288 | -0.216266 | -0.424899 |
| original | jpeg90_512 | all31 | oauth_gpt_image_2 | claude_monet | 2.850679 | 2.929678 | 3.131303 | 2.799826 | 0.280624 | -0.201625 | -0.331477 |
| original | jpeg90_512 | all31 | oauth_gpt_image_2 | paul_cezanne | 2.180307 | 2.281967 | 2.356639 | 2.264025 | 0.176331 | -0.074672 | -0.092613 |
| original | jpeg90_512 | no_lbp8 | nano_banana_2 | claude_monet | 4.291393 | 4.277308 | 4.468928 | 3.911726 | 0.177535 | -0.191619 | -0.557201 |
| original | jpeg90_512 | no_lbp8 | nano_banana_2 | paul_cezanne | 3.417110 | 3.538789 | 3.666044 | 3.324721 | 0.248934 | -0.127256 | -0.341323 |
| original | jpeg90_512 | no_lbp8 | flux_2_max | claude_monet | 1.945440 | 2.013958 | 2.448406 | 1.691575 | 0.502967 | -0.434448 | -0.756831 |
| original | jpeg90_512 | no_lbp8 | flux_2_max | paul_cezanne | 1.228202 | 1.246038 | 1.468400 | 1.039729 | 0.240198 | -0.222362 | -0.428671 |
| original | jpeg90_512 | no_lbp8 | oauth_gpt_image_2 | claude_monet | 2.726541 | 2.779596 | 2.986351 | 2.641255 | 0.259810 | -0.206755 | -0.345096 |
| original | jpeg90_512 | no_lbp8 | oauth_gpt_image_2 | paul_cezanne | 2.106734 | 2.193827 | 2.271117 | 2.168649 | 0.164383 | -0.077289 | -0.102468 |
| original | jpeg90_512 | nontexture19 | nano_banana_2 | claude_monet | 2.881399 | 2.831671 | 2.969238 | 2.575004 | 0.087838 | -0.137566 | -0.394234 |
| original | jpeg90_512 | nontexture19 | nano_banana_2 | paul_cezanne | 2.320881 | 2.321899 | 2.461861 | 2.164042 | 0.140980 | -0.139963 | -0.297819 |
| original | jpeg90_512 | nontexture19 | flux_2_max | claude_monet | 1.876723 | 1.774066 | 2.252333 | 1.461195 | 0.375610 | -0.478267 | -0.791138 |
| original | jpeg90_512 | nontexture19 | flux_2_max | paul_cezanne | 1.145799 | 1.081598 | 1.310358 | 0.914846 | 0.164560 | -0.228760 | -0.395512 |
| original | jpeg90_512 | nontexture19 | oauth_gpt_image_2 | claude_monet | 1.985741 | 1.909386 | 2.129343 | 1.805817 | 0.143601 | -0.219957 | -0.323526 |
| original | jpeg90_512 | nontexture19 | oauth_gpt_image_2 | paul_cezanne | 1.260913 | 1.255108 | 1.305913 | 1.185073 | 0.045000 | -0.050805 | -0.120840 |
| original | primary512 | all31 | nano_banana_2 | claude_monet | 4.127115 | 4.118207 | 4.299233 | 3.759370 | 0.172119 | -0.181027 | -0.539864 |
| original | primary512 | all31 | nano_banana_2 | paul_cezanne | 3.276539 | 3.411656 | 3.552441 | 3.192150 | 0.275902 | -0.140785 | -0.360291 |
| original | primary512 | all31 | flux_2_max | claude_monet | 1.899303 | 1.961784 | 2.407513 | 1.649921 | 0.508211 | -0.445730 | -0.757592 |
| original | primary512 | all31 | flux_2_max | paul_cezanne | 1.219304 | 1.246285 | 1.459901 | 1.054765 | 0.240597 | -0.213616 | -0.405136 |
| original | primary512 | all31 | oauth_gpt_image_2 | claude_monet | 2.793911 | 2.868001 | 3.075464 | 2.738701 | 0.281553 | -0.207464 | -0.336763 |
| original | primary512 | all31 | oauth_gpt_image_2 | paul_cezanne | 2.121558 | 2.215722 | 2.294215 | 2.189301 | 0.172657 | -0.078493 | -0.104914 |
| original | primary512 | no_lbp8 | nano_banana_2 | claude_monet | 4.210895 | 4.193920 | 4.372946 | 3.835636 | 0.162052 | -0.179026 | -0.537310 |
| original | primary512 | no_lbp8 | nano_banana_2 | paul_cezanne | 3.287272 | 3.392518 | 3.519328 | 3.183480 | 0.232056 | -0.126810 | -0.335848 |
| original | primary512 | no_lbp8 | flux_2_max | claude_monet | 1.905799 | 1.955100 | 2.394873 | 1.627412 | 0.489074 | -0.439773 | -0.767461 |
| original | primary512 | no_lbp8 | flux_2_max | paul_cezanne | 1.202038 | 1.214295 | 1.427485 | 1.019695 | 0.225447 | -0.213190 | -0.407790 |
| original | primary512 | no_lbp8 | oauth_gpt_image_2 | claude_monet | 2.696961 | 2.745846 | 2.956594 | 2.610304 | 0.259633 | -0.210748 | -0.346290 |
| original | primary512 | no_lbp8 | oauth_gpt_image_2 | paul_cezanne | 2.063414 | 2.145961 | 2.226447 | 2.113101 | 0.163033 | -0.080486 | -0.113346 |
| original | primary512 | nontexture19 | nano_banana_2 | claude_monet | 2.784890 | 2.738321 | 2.861901 | 2.489904 | 0.077011 | -0.123580 | -0.371997 |
| original | primary512 | nontexture19 | nano_banana_2 | paul_cezanne | 2.149560 | 2.134714 | 2.275857 | 1.985954 | 0.126296 | -0.141143 | -0.289903 |
| original | primary512 | nontexture19 | flux_2_max | claude_monet | 1.839465 | 1.718298 | 2.206210 | 1.396302 | 0.366745 | -0.487912 | -0.809908 |
| original | primary512 | nontexture19 | flux_2_max | paul_cezanne | 1.113985 | 1.051910 | 1.271408 | 0.894838 | 0.157423 | -0.219498 | -0.376570 |
| original | primary512 | nontexture19 | oauth_gpt_image_2 | claude_monet | 1.959259 | 1.882463 | 2.106543 | 1.781864 | 0.147284 | -0.224080 | -0.324679 |
| original | primary512 | nontexture19 | oauth_gpt_image_2 | paul_cezanne | 1.231549 | 1.224358 | 1.276720 | 1.145738 | 0.045171 | -0.052362 | -0.130982 |
| original | resolution256 | all31 | nano_banana_2 | claude_monet | 3.958992 | 3.950904 | 4.132330 | 3.552968 | 0.173339 | -0.181426 | -0.579362 |
| original | resolution256 | all31 | nano_banana_2 | paul_cezanne | 3.815057 | 4.042431 | 4.174937 | 3.749595 | 0.359879 | -0.132506 | -0.425341 |
| original | resolution256 | all31 | flux_2_max | claude_monet | 1.726834 | 1.825564 | 2.155864 | 1.585945 | 0.429030 | -0.330300 | -0.569919 |
| original | resolution256 | all31 | flux_2_max | paul_cezanne | 1.286947 | 1.311054 | 1.526099 | 1.101369 | 0.239152 | -0.215045 | -0.424730 |
| original | resolution256 | all31 | oauth_gpt_image_2 | claude_monet | 2.092374 | 2.202429 | 2.301798 | 2.117273 | 0.209424 | -0.099369 | -0.184525 |
| original | resolution256 | all31 | oauth_gpt_image_2 | paul_cezanne | 1.901914 | 1.990745 | 2.079496 | 1.913722 | 0.177582 | -0.088752 | -0.165775 |
| original | resolution256 | no_lbp8 | nano_banana_2 | claude_monet | 3.972268 | 3.974733 | 4.138846 | 3.600965 | 0.166579 | -0.164113 | -0.537881 |
| original | resolution256 | no_lbp8 | nano_banana_2 | paul_cezanne | 3.717915 | 3.877489 | 3.969399 | 3.670512 | 0.251483 | -0.091910 | -0.298886 |
| original | resolution256 | no_lbp8 | flux_2_max | claude_monet | 1.658957 | 1.762165 | 2.069866 | 1.537991 | 0.410909 | -0.307701 | -0.531875 |
| original | resolution256 | no_lbp8 | flux_2_max | paul_cezanne | 1.280238 | 1.301098 | 1.514676 | 1.090208 | 0.234438 | -0.213578 | -0.424469 |
| original | resolution256 | no_lbp8 | oauth_gpt_image_2 | claude_monet | 1.987314 | 2.082888 | 2.183149 | 1.995775 | 0.195835 | -0.100261 | -0.187373 |
| original | resolution256 | no_lbp8 | oauth_gpt_image_2 | paul_cezanne | 1.876808 | 1.963307 | 2.055076 | 1.882176 | 0.178268 | -0.091770 | -0.172900 |
| original | resolution256 | nontexture19 | nano_banana_2 | claude_monet | 2.675026 | 2.672590 | 2.784211 | 2.428137 | 0.109185 | -0.111621 | -0.356074 |
| original | resolution256 | nontexture19 | nano_banana_2 | paul_cezanne | 2.453720 | 2.525355 | 2.614719 | 2.368832 | 0.160999 | -0.089365 | -0.245888 |
| original | resolution256 | nontexture19 | flux_2_max | claude_monet | 1.520644 | 1.493690 | 1.841399 | 1.261534 | 0.320755 | -0.347709 | -0.579865 |
| original | resolution256 | nontexture19 | flux_2_max | paul_cezanne | 1.145870 | 1.108114 | 1.336376 | 0.907369 | 0.190506 | -0.228263 | -0.429007 |
| original | resolution256 | nontexture19 | oauth_gpt_image_2 | claude_monet | 1.702335 | 1.749669 | 1.834428 | 1.675690 | 0.132093 | -0.084759 | -0.158738 |
| original | resolution256 | nontexture19 | oauth_gpt_image_2 | paul_cezanne | 1.108269 | 1.113978 | 1.171995 | 1.025163 | 0.063727 | -0.058017 | -0.146832 |
| transfer | jpeg90_512 | all31 | flux_2_max | claude_monet | 1.542224 | 1.969393 | 2.127975 | 1.638739 | 0.585751 | -0.158583 | -0.489236 |
| transfer | jpeg90_512 | all31 | flux_2_max | paul_cezanne | 0.776827 | 1.042568 | 1.049510 | 0.827033 | 0.272683 | -0.006942 | -0.222477 |
| transfer | jpeg90_512 | no_lbp8 | flux_2_max | claude_monet | 1.528317 | 1.934261 | 2.096945 | 1.590364 | 0.568629 | -0.162685 | -0.506581 |
| transfer | jpeg90_512 | no_lbp8 | flux_2_max | paul_cezanne | 0.757412 | 1.011978 | 1.017998 | 0.783639 | 0.260586 | -0.006019 | -0.234358 |
| transfer | jpeg90_512 | nontexture19 | flux_2_max | claude_monet | 1.371925 | 1.644467 | 1.794271 | 1.386240 | 0.422346 | -0.149804 | -0.408031 |
| transfer | jpeg90_512 | nontexture19 | flux_2_max | paul_cezanne | 0.709835 | 0.889549 | 0.905944 | 0.718702 | 0.196110 | -0.016395 | -0.187243 |
| transfer | primary512 | all31 | flux_2_max | claude_monet | 1.470401 | 1.900722 | 2.061511 | 1.570522 | 0.591110 | -0.160789 | -0.490989 |
| transfer | primary512 | all31 | flux_2_max | paul_cezanne | 0.736045 | 0.992087 | 0.990369 | 0.820251 | 0.254324 | 0.001718 | -0.170117 |
| transfer | primary512 | no_lbp8 | flux_2_max | claude_monet | 1.467714 | 1.863468 | 2.027096 | 1.530698 | 0.559382 | -0.163628 | -0.496398 |
| transfer | primary512 | no_lbp8 | flux_2_max | paul_cezanne | 0.722766 | 0.964525 | 0.964586 | 0.786020 | 0.241820 | -0.000061 | -0.178566 |
| transfer | primary512 | nontexture19 | flux_2_max | claude_monet | 1.302828 | 1.570525 | 1.721202 | 1.325964 | 0.418375 | -0.150677 | -0.395238 |
| transfer | primary512 | nontexture19 | flux_2_max | paul_cezanne | 0.666172 | 0.838575 | 0.846753 | 0.717755 | 0.180580 | -0.008178 | -0.128997 |
| transfer | resolution256 | all31 | flux_2_max | claude_monet | 1.561522 | 1.862344 | 2.072660 | 1.438415 | 0.511138 | -0.210315 | -0.634244 |
| transfer | resolution256 | all31 | flux_2_max | paul_cezanne | 0.766325 | 1.021057 | 1.014683 | 0.813351 | 0.248358 | 0.006374 | -0.201332 |
| transfer | resolution256 | no_lbp8 | flux_2_max | claude_monet | 1.520912 | 1.799194 | 2.005179 | 1.375313 | 0.484267 | -0.205986 | -0.629866 |
| transfer | resolution256 | no_lbp8 | flux_2_max | paul_cezanne | 0.759513 | 1.008923 | 1.000490 | 0.791679 | 0.240977 | 0.008433 | -0.208811 |
| transfer | resolution256 | nontexture19 | flux_2_max | claude_monet | 1.291304 | 1.499216 | 1.671120 | 1.196142 | 0.379816 | -0.171904 | -0.474978 |
| transfer | resolution256 | nontexture19 | flux_2_max | paul_cezanne | 0.680227 | 0.876810 | 0.882212 | 0.693822 | 0.201985 | -0.005402 | -0.188390 |
