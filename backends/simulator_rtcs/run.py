from qat.purr.compiler.config import CompilerConfig
from qat.purr.compiler.frontends import QASMFrontend
import pickle
import sys
import json
import time

if len(sys.argv) != 5:
    print("Usage: python3.8 run.py <compiled_circuit.x> <results.json> <execution_metrics.json> <num_shots>")
    sys.exit(1)

circuit_filename = sys.argv[1]
results_filename = sys.argv[2]
execution_metrics_filename = sys.argv[3]
num_shots = int(sys.argv[4])

# Read pre-compiled circuit
with open(circuit_filename, "rb") as f:
    print(f"Reading pre-compiled circuit file: {circuit_filename}")
    instruction_builder = pickle.load(f)

frontend = QASMFrontend()

config = CompilerConfig()
config.results_format.binary_count()
config.repeats = num_shots

# Time measure
start = time.time()
end = time.time()
results, execution_metrics = frontend.execute(instruction_builder, compiler_config=config)
elapsed = {"elapsed_time": end - time}

with open(results_filename, "w") as f:
    json.dump(results, f)

with open(execution_metrics_filename, "w") as f:
    json.dump(execution_metrics.as_dict(), f)

print(results)
