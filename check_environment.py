#!/usr/bin/env python3
from dataclasses import dataclass
import importlib.util, os, re, shutil, socket, subprocess, sys

@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str

def run_cmd(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=15, check=False)

def check_java_21():
    java = shutil.which("java")
    if not java:
        return CheckResult("Java 21", False, "java nao encontrado")
    proc = run_cmd([java, "-version"])
    out = (proc.stderr or "") + (proc.stdout or "")
    m = re.search(r'version\s+"?(\d+)(?:\.(\d+))?', out)
    if not m:
        return CheckResult("Java 21", False, "nao parseou versao")
    major = int(m.group(1))
    if major == 1 and m.group(2):
        major = int(m.group(2))
    if major == 21:
        return CheckResult("Java 21", True, out.splitlines()[0].strip())
    return CheckResult("Java 21", False, f"versao {major}, esperado 21")

def check_mapepire():
    for mod in ["mapepire_python", "mapepire"]:
        try:
            if importlib.util.find_spec(mod) is not None:
                return CheckResult("Mapepire", True, f"modulo {mod}")
        except: pass
    return CheckResult("Mapepire", False, "nao encontrado")

def check_ibmi():
    code = shutil.which("code")
    if not code:
        return CheckResult("Extensao IBM i", False, "code nao encontrado")
    proc = run_cmd([code, "--list-extensions"])
    exts = (proc.stdout or "").lower()
    if "ibmi" in exts or "code-for-ibmi" in exts:
        return CheckResult("Extensao IBM i", True, "extensao encontrada")
    return CheckResult("Extensao IBM i", False, "extensao nao encontrada")

def check_as400():
    host = os.getenv("AS400_HOST", "").strip()
    if not host:
        return CheckResult("Conexao AS400", False, "AS400_HOST nao definido")
    port = int(os.getenv("AS400_PORT", "8076"))
    try:
        with socket.create_connection((host, port), timeout=5):
            pass
        return CheckResult("Conexao AS400", True, f"TCP OK {host}:{port}")
    except Exception as e:
        return CheckResult("Conexao AS400", False, f"falha {e}")

def main():
    checks = [check_java_21(), check_mapepire(), check_ibmi(), check_as400()]
    print("="*60)
    print("PRE-FLIGHT - Atlas")
    print("="*60)
    for c in checks:
        print(f"[{'OK  ' if c.ok else 'FAIL'}] {c.name}: {c.detail}")
    fails = [c for c in checks if not c.ok]
    if fails:
        print(f"FALHOU {len(fails)} item(s). Esteira interrompida.")
        return 1
    print("Pre-flight OK. Esteira liberada.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
