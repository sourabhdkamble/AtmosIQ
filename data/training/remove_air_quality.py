import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKUP_SUFFIX = ".before_weather_only"

supervisor_file = ROOT / "backend" / "app" / "agents" / "supervisor.py"
graph_file = ROOT / "backend" / "app" / "agents" / "weather_graph.py"
training_file = ROOT / "data" / "training" / "intent_examples.jsonl"
evaluation_file = ROOT / "data" / "training" / "intent_eval.jsonl"

files = [supervisor_file, graph_file, training_file, evaluation_file]

for path in files:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")

def backup(path):
    backup_path = Path(str(path) + BACKUP_SUFFIX)
    shutil.copy2(path, backup_path)
    print(f"Backup: {backup_path}")

def remove_block(content, pattern, description):
    updated, count = re.subn(pattern, "", content, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError(f"Could not safely locate {description}; no changes applied.")
    return updated

# Prepare and validate the code changes in memory before writing any files.
supervisor = supervisor_file.read_text(encoding="utf-8-sig")
graph = graph_file.read_text(encoding="utf-8-sig")

# Supervisor: reduce the supported route list to four weather categories.
supervisor_new = supervisor.replace(
    '    "air_quality",\n',
    "",
)
if supervisor_new == supervisor:
    raise RuntimeError("Could not find the air_quality route in supervisor.py.")

# Remove the air-quality keyword matching section.
supervisor_new = remove_block(
    supervisor_new,
    r'    # Air quality:.*?return "air_quality"\s*\n',
    "supervisor air-quality keyword block",
)

# Remove the air-quality-specific description from the Gemini prompt.
supervisor_new = remove_block(
    supervisor_new,
    r'- air_quality: AQI, pollution, PM2\.5, or PM10\n',
    "supervisor air-quality prompt line",
)

# Graph: remove the air-quality response function.
graph_new = remove_block(
    graph,
    r'\ndef answer_air_quality_unavailable\(state: WeatherAgentState\) -> dict:.*?(?=\ndef classify_request)',
    "air-quality graph function",
)

# Remove air_quality from choose_route's return type.
graph_new = graph_new.replace(
    '    "answer_air_quality_unavailable",\n',
    "",
)

# Remove the air-quality branch from choose_route.
graph_new = remove_block(
    graph_new,
    r'\n    if intent == "air_quality":\n        return "answer_air_quality_unavailable"\n',
    "air-quality route branch",
)

# Remove the air-quality graph node registration.
graph_new = remove_block(
    graph_new,
    r'\n    graph_builder\.add_node\(\s*"answer_air_quality_unavailable",\s*answer_air_quality_unavailable,\s*\)',
    "air-quality node registration",
)

# Remove the conditional mapping for the deleted node.
graph_new = remove_block(
    graph_new,
    r'\n\s*"answer_air_quality_unavailable": "answer_air_quality_unavailable",',
    "air-quality conditional edge mapping",
)

# Remove the terminal edge for the deleted node.
graph_new = remove_block(
    graph_new,
    r'\n    graph_builder\.add_edge\("answer_air_quality_unavailable", END\)',
    "air-quality terminal edge",
)

# Read and validate both JSONL datasets before changing anything.
def load_jsonl(path):
    records = []
    with path.open("r", encoding="utf-8-sig") as file:
        for number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path.name}, line {number}: {exc}") from exc
            if not isinstance(item, dict) or not isinstance(item.get("route"), str):
                raise ValueError(f"{path.name}, line {number}: missing route.")
            records.append(item)
    return records

training = load_jsonl(training_file)
evaluation = load_jsonl(evaluation_file)

training_new = [x for x in training if x["route"] != "air_quality"]
evaluation_new = [x for x in evaluation if x["route"] != "air_quality"]

allowed_routes = {
    "current_weather",
    "forecast",
    "weather_advice",
    "knowledge",
}

for label, records in (("training", training_new), ("evaluation", evaluation_new)):
    unexpected = sorted({x["route"] for x in records} - allowed_routes)
    if unexpected:
        raise RuntimeError(f"Unexpected routes in {label} data: {unexpected}")

if not evaluation_new:
    raise RuntimeError("Evaluation dataset would be empty.")

# Back up every affected file before writing changes.
for path in files:
    backup(path)

def write_jsonl(path, records):
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8", newline="\n") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
    temp.replace(path)

supervisor_file.write_text(supervisor_new, encoding="utf-8")
graph_file.write_text(graph_new, encoding="utf-8")
write_jsonl(training_file, training_new)
write_jsonl(evaluation_file, evaluation_new)

def counts(records):
    result = {}
    for item in records:
        result[item["route"]] = result.get(item["route"], 0) + 1
    return result

print("\nAtmosIQ weather-only conversion completed.")
print(f"Training records: {len(training)} -> {len(training_new)}")
print(f"Evaluation records: {len(evaluation)} -> {len(evaluation_new)}")
print("Training counts:", counts(training_new))
print("Evaluation counts:", counts(evaluation_new))
print("\nRemaining routes:")
for route in sorted(allowed_routes):
    print(f"  {route}")

print("\nPlease review the changed files before running the evaluation.")
