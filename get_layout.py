import subprocess

variant = ""

out = subprocess.check_output(["localectl", "status"], text=True)
for line in out.splitlines():
    line = line.strip()
    if line.startswith("X11 Layout:"):
        variant += line.split(":")[1].strip()
        variant += "-"
        
    if line.startswith("X11 Variant"):
        variant += line.split(":")[1].strip()
    
print(variant)
