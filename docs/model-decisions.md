# Hugging Face model decisions

Verified July 23, 2026 against the current Hub repository metadata, model cards, and pinned repository revisions. A permissive model license does not replace product-specific legal review.

| Repository ID | Pinned revision | Approximate size | License | Runtime and code requirements | Commercial posture | v0.1 decision |
|---|---|---:|---|---|---|---|
| `ZhengPeng7/BiRefNet_lite` | `7838f1c3472f827cd8ce13ab5ccc2ce48077360f` | 44.4M parameters, roughly 178 MB at FP32 before framework overhead | No explicit license metadata found | PyTorch; repository advertises custom code; CPU is possible but slow; lazy cache required | **Ambiguous.** Do not treat as foundational until the publisher clarifies terms | Optional `BiRefNetProvider`; deterministic provider remains default |
| `microsoft/Florence-2-base` | `cb51be2b8d7f48f70a621ad0d56eb570ce820543` | 231.6M parameters, roughly 0.93 GB at FP32 | MIT | Transformers/PyTorch; repository is tagged for custom code; CPU requires materially more latency and memory than fixture mode | Commercial use appears permitted under MIT, subject to ordinary review | Provider boundary documented; implementation deferred so it cannot destabilize rendering |
| `facebook/sam2.1-hiera-small` | `ee5bba1d82bb8749febdf90f45e84b687142ba03` | 46.1M parameters, repository files roughly 369 MB | Apache-2.0 | Transformers-native segmentation path; CPU possible but interactive correction is the intended future use | Commercial use appears permitted under Apache-2.0 | Optional roadmap candidate for component correction |
| `depth-anything/Depth-Anything-V2-Small-hf` | `5426e4f0f36572d16453bbda7a8389317b1bef99` | 24.8M parameters, repository files roughly 99 MB | Apache-2.0 | Transformers depth-estimation pipeline; CPU possible but slower | Commercial use appears permitted under Apache-2.0 | Optional roadmap candidate for shape estimation |
| `microsoft/TRELLIS.2-4B` | `74af0357c905e8a9cb60d9a91811c489d14f6c91` | 4B parameters and multi-gigabyte weights | MIT | Linux, CUDA 12.4-class environment, NVIDIA GPU with at least 24 GB VRAM according to the card | License appears permissive, but the compute footprint conflicts with the free baseline | Rejected for v0.1; experimental fallback issue only |

## Provider policy

`BackgroundRemovalProvider` separates application behavior from any one repository. Implementations are:

- `DeterministicFixtureProvider`: reproducible mask and output for tests
- `NoOpProvider`: preserves the source and records that no isolation occurred
- `BiRefNetProvider`: optional, lazy, revision-pinned adapter with actionable errors

The worker records provider name, fallback status, and warnings. It does not silently substitute one model for another. It never uses a public community Space as a production API, creates a paid Inference Endpoint, commits model weights, or enables arbitrary remote code from a request.
