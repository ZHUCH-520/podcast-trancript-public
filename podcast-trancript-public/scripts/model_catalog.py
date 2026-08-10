from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelSource:
    repo_id: str
    revision: str
    download_bytes: int
    required_files: tuple[str, ...]


@dataclass(frozen=True)
class Profile:
    name: str
    mlx: ModelSource
    faster: ModelSource


MODEL_PROFILES = {
    "small": Profile(
        name="small",
        mlx=ModelSource(
            "mlx-community/whisper-small-mlx",
            "45f3915923c7a79a5a5b5a7d909d39aeb0e5630e",
            481_307_592,
            ("config.json", "weights.npz"),
        ),
        faster=ModelSource(
            "Systran/faster-whisper-small",
            "536b0662742c02347bc0e980a01041f333bce120",
            483_546_902,
            ("config.json", "model.bin", "tokenizer.json", "vocabulary.txt"),
        ),
    ),
    "turbo": Profile(
        name="turbo",
        mlx=ModelSource(
            "mlx-community/whisper-large-v3-turbo",
            "a4aaeec0636e6fef84abdcbe3544cb2bf7e9f6fb",
            3_228_066_988,
            ("config.json", "weights.safetensors"),
        ),
        faster=ModelSource(
            "mobiuslabsgmbh/faster-whisper-large-v3-turbo",
            "0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf",
            1_617_884_929,
            ("config.json", "model.bin", "tokenizer.json", "vocabulary.json"),
        ),
    ),
    "large-v3": Profile(
        name="large-v3",
        mlx=ModelSource(
            "mlx-community/whisper-large-v3-mlx",
            "49e6aa286ad60c14352c404340ded53710378a11",
            3_247_898_936,
            ("config.json", "weights.npz"),
        ),
        faster=ModelSource(
            "Systran/faster-whisper-large-v3",
            "edaa852ec7e145841d8ffdb056a99866b5f0a478",
            3_145_762_253,
            ("config.json", "model.bin", "tokenizer.json", "vocabulary.json"),
        ),
    ),
}


def source_for(profile: str, backend: str) -> ModelSource:
    try:
        selected = MODEL_PROFILES[profile]
    except KeyError as exc:
        raise ValueError(f"unsupported model profile: {profile}") from exc
    if backend == "mlx":
        return selected.mlx
    if backend == "faster":
        return selected.faster
    raise ValueError(f"unsupported backend: {backend}")


def package_requirements(backend: str) -> list[str]:
    common = ["huggingface-hub==1.27.0"]
    if backend == "mlx":
        return common + ["mlx-whisper==0.4.3"]
    if backend == "faster":
        return common + ["faster-whisper==1.2.1"]
    raise ValueError(f"unsupported backend: {backend}")
