import subprocess


class RunCommandError(Exception):
    pass


def run(cmd):
    p = subprocess.run(cmd, shell=True, capture_output=True)
    if p.returncode != 0:
        raise RunCommandError(p.stderr)
    return p.stdout.decode('utf8'), p.stderr.decode('utf8')
