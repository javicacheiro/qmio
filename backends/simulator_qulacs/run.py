from qulacs import QuantumCircuit, QuantumState, QuantumCircuitSimulator, Observable
from qulacs import converter

# Hay que quitar los creg y las medidas porque no está soportado por la autotraducción
qasm_string = """
OPENQASM 2.0;
include "qelib1.inc";

qreg q[2];

h q[0];           
cx q[0],q[1];     
"""
# Convertir el qasm a un circuito en qulacs
qc = converter.convert_QASM_to_qulacs_circuit(qasm_string.splitlines())
print(qc)

# Instanciar el vector de estado
qubits = qc.get_qubit_count()
state = QuantumState(qubits)    # si fuese en la implementación paralela, QuantumState(qubits, 1) y ademas inicializar el entorno mpi

"""
Tendríamos que definir cual es la función báscia
que queremos implementar en en módulo con respecto
a los tipos de simulación disponibles en qulacs.
Podríamos empezar por uno e implementar algún otro a través de
opciones que le pongamos a la opción 

qumio_run(backend=qulacs_sim, qasm_file=<>, sim_type=<>)

Veo bueno este módulo para hacer simulación en los arm multicpu
como paso previo a moverte a qumio porue si quieres hacer simulación
con qulacs y sacarle rendimiento es mejor hacerlo directo.
"""

# Inicializar el vector de estado en el estado 0
state.set_zero_state()
print(state)

# Inicializar el simulador y simular
sim = QuantumCircuitSimulator(qc, state)
sim.simulate()
print(state)

# Instanciar un observable y obtener el valor esperado de ese observable
observable = Observable(1)
observable.add_operator(1.0, "Z 0")

sim.get_expectation_value(observable)
