from qmio.circuits import bell, ghz


def test_bell():
    circuit = bell()
    bell_test = """OPENQASM 3.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\nh q[0];\ncx q[0],q[1];\nmeasure q[0] -> c[0];\nmeasure q[1] -> c[1];"""
    assert circuit.strip() == bell_test.strip()


def test_ghz():
    circuit = ghz()
    ghz_test = """OPENQASM 3.0;\ninclude "qelib1.inc";\nqreg q[3];\ncreg meas[3];\nh q[0];\ncx q[0],q[1];\ncx q[0],q[2];\nbarrier q[0],q[1],q[2];\nmeasure q[0] -> meas[0];\nmeasure q[1] -> meas[1];\nmeasure q[2] -> meas[2];"""
    assert circuit.strip() == ghz_test.strip()
