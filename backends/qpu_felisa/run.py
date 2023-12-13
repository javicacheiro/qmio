from qat.purr.compiler.config import CompilerConfig
from qat.purr.compiler.frontends import QASMFrontend
import pickle
import sys
import json
from pathlib import Path
from lx7.zmq_wrapper import ZMQClient


if len(sys.argv) != 5:
    print("Usage: python3.8 run.py <compiled_circuit.x> <results.json> <execution_metrics.json> <num_shots>")
    sys.exit(1)

circuit_filename = sys.argv[1]
results_filename = sys.argv[2]
execution_metrics_filename = sys.argv[3]
num_shots = int(sys.argv[4])

if Path(circuit_filename).is_file():
    print(f"Reading circuit file: {circuit_filename}")
    circuit = Path(circuit_filename).read_text()

config = CompilerConfig()
config.results_format.binary_count()
config.repeats = num_shots

zmq_client = ZMQClient()
output = zmq_client.execute_task(circuit, config.to_json())

with open(results_filename, "w") as f:
    json.dump(output["results"], f)

with open(execution_metrics_filename, "w") as f:
    json.dump(output["execution_metrics"], f)

print(output["results"])
