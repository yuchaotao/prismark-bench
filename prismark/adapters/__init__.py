"""Registry of tool adapters. Optional dependencies are imported lazily."""

from __future__ import annotations

from prismark.adapters.base import Adapter

# Short names for Hugging Face models: alias -> (kind, model id)
HF_MODELS = {
    "privacy-filter": ("token", "openai/privacy-filter"),
    "piiranha": ("token", "iiiorg/piiranha-v1-detect-personal-information"),
    "gliner-nvidia": ("gliner", "nvidia/gliner-pii"),
    "gliner-urchade": ("gliner", "urchade/gliner_multi_pii-v1"),
}


def load(name: str) -> Adapter:
    if name == "regex":
        from prismark.adapters.regex_baseline import RegexBaseline

        return RegexBaseline()
    if name == "presidio":
        from prismark.adapters.presidio import PresidioAdapter

        return PresidioAdapter()
    if name in HF_MODELS:
        kind, model = HF_MODELS[name]
        if kind == "token":
            from prismark.adapters.hf_token import HFTokenClassifier

            return HFTokenClassifier(model, name=name)
        from prismark.adapters.gliner_adapter import GLiNERAdapter

        return GLiNERAdapter(model, name=name)
    if name.startswith("gliner:"):
        from prismark.adapters.gliner_adapter import GLiNERAdapter

        return GLiNERAdapter(name.partition(":")[2])
    if name.startswith("hf:"):
        from prismark.adapters.hf_token import HFTokenClassifier

        return HFTokenClassifier(name.partition(":")[2])
    if name.startswith("ollama:"):
        from prismark.adapters.ollama import OllamaAdapter

        return OllamaAdapter(name.partition(":")[2])
    if name == "claude" or name.startswith("claude:"):
        from prismark.adapters.llm import ClaudeAdapter

        _, _, model = name.partition(":")
        return ClaudeAdapter(model=model) if model else ClaudeAdapter()
    raise ValueError(f"unknown tool {name!r}; available: {', '.join(AVAILABLE)}")


AVAILABLE = ["regex", "presidio", *HF_MODELS, "hf:<model id>", "gliner:<model id>", "ollama:<model>", "claude[:<model>]"]
