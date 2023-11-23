from qat.purr.compiler.config import CompilerConfig
from qat.purr.compiler.frontends import QASMFrontend
import pickle
import sys


if len(sys.argv) != 4:
    print("Usage: python3.8 compile.py <circuit.qasm> <circuit.p> <num_shots>")
    sys.exit(1)

qasm_filename = sys.argv[1]
instructions_filename = sys.argv[2]
num_shots = int(sys.argv[3])

frontend = QASMFrontend()

config = CompilerConfig()
config.results_format.binary_count()
config.repeats = num_shots

instruction_builder, parsed_metrics = frontend.parse(qasm_filename, compiler_config=config)

print(f"Writing instructions file to: {instructions_filename}")
with open(instructions_filename, "wb") as f:
    pickle.dump(instruction_builder, f)

print("Done")
