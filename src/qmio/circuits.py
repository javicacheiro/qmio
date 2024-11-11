"""
Qmio QASM circuit generators examples

"""


def bell(qc: int = 0, qt: int = 1) -> str:
    """
    Creates a bell pair between qc and qt

    Parameters:
    -----------
    qc: int, default = 0
        Qubit control to participate in bell pair

    qt: int, default = 1
        Qubit target to participate in bell pair

    Returns:
    --------
    bell: str
        QASM 3.0 string with the circuit

    """
    bell = f"""OPENQASM 3.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[{qc}];
cx q[{qc}],q[{qt}];
measure q[{qc}] -> c[0];
measure q[{qt}] -> c[1];"""
    return bell


def ghz(qc: int = 0, qt1: int = 1, qt2: int = 2)-> str:
    """
    Creates a ghz trio among qc and qt1 and qt2

    Parameters:
    -----------
    qc: int, default = 0
        Qubit control to participate in ghz trio

    qt1: int, default = 1
        Qubit target 1 to participate in ghz trio

    qt2: int, default = 2
        Qubit target 2 to participate in ghz trio

    Returns:
    --------
    ghz: str
        QASM 3.0 string with the circuit

    """
    ghz = f"""OPENQASM 3.0;
include "qelib1.inc";
qreg q[3];
creg meas[3];
h q[{qc}];
cx q[{qc}],q[{qt1}];
cx q[{qc}],q[{qt2}];
barrier q[{qc}],q[{qt1}],q[{qt2}];
measure q[{qc}] -> meas[0];
measure q[{qt1}] -> meas[1];
measure q[{qt2}] -> meas[2];"""
    return ghz
