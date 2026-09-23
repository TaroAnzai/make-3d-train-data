import importlib.util
import os
import platform
import shutil
import subprocess
import sys

def find_blender(cli_value=None, config_value=None):
    for value in (cli_value, os.environ.get("BLENDER_BIN"), config_value, shutil.which("blender")):
        if value and (shutil.which(value) or os.path.isfile(value)):
            return os.path.abspath(shutil.which(value) or value)
    return None

def blender_version(binary):
    if not binary: return None
    try: return subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=10).stdout.splitlines()[0]
    except (OSError, subprocess.SubprocessError): return None

def report(blender_bin=None, config_bin=None):
    binary=find_blender(blender_bin, config_bin)
    lines=[f"Python: OK ({platform.python_version()})"]
    for title,module in (("Pillow","PIL"),("PyYAML","yaml")): lines.append(f"{title}: {'OK' if importlib.util.find_spec(module) else 'NOT FOUND'}")
    version = blender_version(binary)
    lines.append(f"Blender: {'FOUND (' + version + ')' if version else 'NOT FOUND'}")
    if binary:
        lines.append(f"Blender binary: {binary}")
    if not binary: lines += ["", "Blender-dependent rendering is unavailable.", "Configuration and non-Blender tests can still run."]
    return "\n".join(lines), binary
