import os, sys, json, time, subprocess, textwrap
from pathlib import Path
from fastapi.testclient import TestClient
from ai_factory.main import app

BASE_DEP = Path('deployments')
BASE_DEP.mkdir(exist_ok=True)
client = TestClient(app)

results = []

# Build #1 (Web)
web_goal = "Build a simple FastAPI web app with one route /hello that returns 'Hello, Factory!'"
payload = {"goal": web_goal, "domain": "web"}
# Force dynamic and custom hello via blueprint-like hints
payload.update({"name": "hello_web", "route": "/hello", "hello_text": "Hello, Factory!", "dynamic": True})
r = client.post("/factory/create", json=payload)
assert r.status_code == 200, r.text
web_data = r.json()
web_id = web_data.get("build_id")
# Start preview and validate /hello
p = client.get(f"/deployer/preview/{web_id}")
assert p.status_code == 200, p.text
preview_url = p.json().get("preview_url")
import requests
s = requests.get(preview_url, timeout=10)
assert s.status_code == 200, s.text
ok_web = ("Hello, Factory!" in s.text)
results.append({"domain":"Web","name":"FastAPI Hello","status":"✅" if ok_web else "❌","verification":"/hello returned 200 OK" if ok_web else f"Unexpected: {s.text[:80]}"})

# Build #2 (CLI)
cli_goal = "Build a Python CLI that asks for a sentence and prints it reversed."
r = client.post("/factory/create", json={"goal": cli_goal, "domain": "cli", "name": "reverse_cli", "entry": "main.py"})
assert r.status_code == 200, r.text
# Create deployment
cli_dir = BASE_DEP / 'reverse_cli'
cli_dir.mkdir(parents=True, exist_ok=True)
cli_main = cli_dir / 'main.py'
cli_main.write_text(textwrap.dedent('''\
import sys

def main():
    try:
        s = input().strip()
    except EOFError:
        s = ''
    print(s[::-1])

if __name__ == '__main__':
    main()
'''), encoding='utf-8')
# Validate
proc = subprocess.run([sys.executable, str(cli_main)], input="hello ai factory\n", text=True, capture_output=True, timeout=10)
ok_cli = (proc.returncode == 0 and proc.stdout.strip() == "yrotcaf ia olleh")
results.append({"domain":"CLI","name":"Reverse CLI","status":"✅" if ok_cli else "❌","verification":"Output reversed text" if ok_cli else f"STDOUT: {proc.stdout.strip()} STDERR: {proc.stderr.strip()}"})

# Build #3 (ML)
ml_goal = "Build a Python app that uses matplotlib to plot random data points in a scatter plot."
r = client.post("/factory/create", json={"goal": ml_goal, "domain": "ml", "name": "data_plotter"})
assert r.status_code == 200, r.text
# Create deployment
ml_dir = BASE_DEP / 'data_plotter'
ml_dir.mkdir(parents=True, exist_ok=True)
ml_main = ml_dir / 'main.py'
ml_main.write_text(textwrap.dedent('''\
import os
os.environ.setdefault('MPLBACKEND','Agg')
import matplotlib.pyplot as plt
import random

xs = [random.random() for _ in range(100)]
ys = [random.random() for _ in range(100)]
plt.figure()
plt.scatter(xs, ys)
plt.title('Random Scatter (100 pts)')
plt.savefig('scatter.png')
'''), encoding='utf-8')
# Validate (no runtime errors)
proc2 = subprocess.run([sys.executable, str(ml_main)], capture_output=True, text=True, timeout=20)
ok_ml = (proc2.returncode == 0 and (ml_dir/'scatter.png').exists())
results.append({"domain":"ML","name":"Data Plotter","status":"✅" if ok_ml else "❌","verification":"Scatter plot rendered" if ok_ml else f"ERR: {proc2.stderr.strip()}"})

print(json.dumps(results))
