"simple wrapper around git shell"
import subprocess

def clean() -> bool:
    "return True if uncommitted changes"
    # todo: make it possible to do 'subdirectory clean' for multi-build projects
    ret = subprocess.run('git status -s --untracked-files=no', shell=True, capture_output=True)
    return not any(bool(line.strip()) for line in ret.stdout.splitlines())

def sha() -> str:
    "return current sha"
    ret = subprocess.run('git rev-parse HEAD', shell=True, capture_output=True)
    return ret.stdout.strip().decode()
