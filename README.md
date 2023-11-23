# Qmio

Helper python module and CLI to interact with the different backends available in Qmio.

## Installation
```
export PYTHONPATH=/mnt/Q_SWAP/qmio/lib
export PATH=/mnt/Q_SWAP/qmio/bin/:$PATH
```

## Python Moudule Usage
Basic usage:
```
from qiskit import QuantumCircuit
from qiskit.visualization import plot_histogram
import qmio

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()

results = qmio.run(qc.qasm(), backend='simulator_rtcs')

counts = results['meas']

plot_histogram(counts)
```


## CLI usage
Execution examples:
```
qmio-run circuit.qasm
qmio-run --backend simulator_rtcs circuit.qasm
qmio-run --shots 200 circuit.qasm
qmio-run instructions.p
```
By default the results of the execution are stored in: `results.json`

Compilation examples:
```
qmio-compile -o circuit.p circuit.qasm
qmio-compile --backend simulator_rtcs --shots 200 --output circuit.p circuit.qasm
```

