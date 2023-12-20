# Qmio

Helper python module and CLI to interact with the different backends available in Qmio.

## Installation
```
export PYTHONPATH=/mnt/Q_SWAP/qmio/lib
export PATH=/mnt/Q_SWAP/qmio/bin/:$PATH
```

## Python Module Usage
Basic usage:
```
from qiskit import QuantumCircuit
from qiskit.visualization import plot_histogram
import qmio
from qmio.utils import RunCommandError


qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()

try:
    results, metrics = qmio.run(qc.qasm(), backend='qpu_felisa', direct=True, shots=1000)
    counts = results['meas']
    plot_histogram(counts)
except RunCommandError:
    print("The slurm job has failed")
```


## CLI usage
Execution examples:
```
qmio-run circuit.qasm
qmio-run instructions.p
qmio-run --direct --backend qpu_felisa --shots 200 circuit.qasm
qmio-run --backend simulator_rtcs circuit.qasm
```
By default the results of the execution are stored in: `results.json`

Compilation examples:
```
qmio-compile -o circuit.p circuit.qasm
qmio-compile --backend simulator_rtcs --shots 200 --output circuit.p circuit.qasm
```

