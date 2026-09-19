"""Generate a local Codex catalog with overridable Astra commentary cadence."""

import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--source", type=Path, default=Path.home() / ".codex/models_cache.json")
parser.add_argument("--output", type=Path, default=Path(__file__).with_name("models-catalog.local.json"))
args = parser.parse_args()

catalog = {"models": json.loads(args.source.read_text())["models"]}
models = [model for model in catalog["models"] if model["slug"] == "gpt-6-astra"]
if len(models) != 1:
    raise SystemExit("Expected exactly one gpt-6-astra model; catalog left unchanged.")

replacements = {
    "The user appreciates consistent, frequent communication during your turn, and should not be left without a commentary update for more than 60 seconds during ongoing work.":
    "During ongoing work, a commentary update roughly every 60 seconds is recommended by default. This is guidance, not a mandatory timer: follow a different cadence, including silence until a meaningful event, when requested by the user or an applicable skill.",
    "- Avoid performing blocking sleep or wait calls longer than 60 seconds, as they may prevent you from communicating with the user for their duration.":
    "- By default, prefer sleep or wait calls of 60 seconds or less to preserve opportunities for communication. This is a recommendation, not a hard limit: when the user or an applicable skill requests quiet or event-driven waiting, use longer interruptible waits as appropriate, within the tool's supported limits.",
}
paragraph = (
    "During delegated execution or long-running waits, report meaningful events and honor the user's requested cadence. "
    "Do not send periodic unchanged-status updates. Prefer interruptible waits appropriate to the workload; "
    "elapsed time alone does not require commentary."
)
model = models[0]
template = model["model_messages"]["instructions_template"]
for before, after in replacements.items():
    if template.count(before) != 1:
        raise SystemExit("Upstream cadence wording changed; review the patch before regenerating. Output left unchanged.")
    template = template.replace(before, after)
anchor = next(iter(replacements.values()))
template = template.replace(anchor, anchor + "\n\n" + paragraph, 1)
model["model_messages"]["instructions_template"] = template
args.output.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n")
print(f"Wrote {args.output}: patched Astra cadence; retained {len(catalog['models'])} models.")
