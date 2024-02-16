# Qmio

Helper python module and CLI to interact with the different backends available in Qmio.

## Installation
```
export PYTHONPATH=/mnt/Q_SWAP/qmio/lib
export PATH=/mnt/Q_SWAP/qmio/bin/:$PATH
```

## Python Module Usage
Basic usage:
```python
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
except RunCommandError as e:
    print(e)
```


## CLI usage
### Help
You can see all available options running:
```
qmio-run --help
```
Below you can see examples of how to execute and compile code.

### Execution examples
- Run a QASM circuit in the Felisa QPU
```
qmio-run --direct --backend qpu_felisa --shots 200 circuit.qasm
```
- Run in the simulator
```
qmio-run --backend simulator_rtcs circuit.qasm
```
- Run in the default backend
```
qmio-run circuit.qasm
```
- Run a compiled instructions file in the default backend
```
qmio-run instructions.p
```

By default the results of the execution are stored in `results.json` and the execution metrics in `execution_metrics.json` in the directory where you submitted the job.

### Compilation examples
```
qmio-compile -o circuit.p circuit.qasm
qmio-compile --backend simulator_rtcs --shots 200 --output circuit.p circuit.qasm
```
Currently compilation is not possible for Felisa QPU backend.
