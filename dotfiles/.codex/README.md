# Astra commentary cadence

`config.toml` sets `developer_instructions` to exempt passive waits from Astra's
60-second commentary cadence and 60-second wait guidance, following a
workaround suggested by OpenAI support. The upstream model catalog stays
unmodified, so new models and prompt updates arrive without regeneration.

Restart Codex to load the instructions. Existing conversations may retain their
previous instructions; verify in a fresh conversation. The Codex desktop app can
supply its own instructions, so the workaround may not apply there.

## Fallback: patched model catalog

If the instructions stop being honored, `patch-model-catalog.py` generates a
catalog that rewrites Astra's two 60-second recommendations directly:

```sh
mise exec -- python dotfiles/.codex/patch-model-catalog.py
```

The script copies the models from `~/.codex/models_cache.json`, changes only
Astra's cadence wording, and writes `models-catalog.local.json` next to itself
(ignored by Git). Point `model_catalog_json` at that file's absolute path and
restart Codex. The script stops without changing its output if Astra's
original cadence wording has changed. `--source` accepts an upstream cache or
catalog JSON file containing a `models` array.

The catalog is a static snapshot: it hides models and prompt changes published
after it was generated. To refresh it, remove `model_catalog_json`, restart
Codex so its model cache updates, rerun the script, then restore the setting.

See the [Codex configuration reference](https://developers.openai.com/codex/config-reference)
for `developer_instructions` and `model_catalog_json`.
