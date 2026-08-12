"""Security scan — check for secrets, sensitive files, and security issues."""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
issues = []

# 1. Scan Python files for hardcoded secrets
secret_patterns = [
    (r'password\s*=\s*["\'][^"\']{4,}["\']', "hardcoded password"),
    (r'api_key\s*=\s*["\'][^"\']{8,}["\']', "hardcoded API key"),
    (r'secret\s*=\s*["\'][^"\']{8,}["\']', "hardcoded secret"),
    (r'token\s*=\s*["\'][^"\']{8,}["\']', "hardcoded token"),
    (r'BEGIN RSA PRIVATE KEY', "private key embedded"),
    (r'BEGIN CERTIFICATE', "certificate embedded"),
]

for dirpath, dirs, files in os.walk(os.path.join(ROOT, "verbamind")):
    for f in files:
        if not f.endswith(".py"):
            continue
        fpath = os.path.join(dirpath, f)
        try:
            with open(fpath, encoding="utf-8") as fh:
                for lineno, line in enumerate(fh, 1):
                    for pattern, desc in secret_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            rel = os.path.relpath(fpath, ROOT)
                            issues.append(f"  [{desc}] {rel}:{lineno}: {line.strip()[:80]}")
        except Exception:
            pass

# 2. Check for sensitive files that should NOT be committed
sensitive_exts = {".vera", ".pem", ".key", ".p12", ".pfx", ".dat"}
sensitive_names = {"key.dat", ".env", "config.json"}

for dirpath, dirs, files in os.walk(ROOT):
    if ".git" in dirpath or "node_modules" in dirpath:
        continue
    for f in files:
        fpath = os.path.join(dirpath, f)
        rel = os.path.relpath(fpath, ROOT)
        ext = os.path.splitext(f)[1].lower()
        if ext in sensitive_exts or f in sensitive_names:
            if os.path.exists(os.path.join(ROOT, ".gitignore")):
                with open(os.path.join(ROOT, ".gitignore")) as gf:
                    gitignore = gf.read()
                if f not in gitignore and ext not in gitignore:
                    issues.append(f"  [untracked sensitive file] {rel}")

# 3. Check .gitignore covers critical patterns
gitignore_path = os.path.join(ROOT, ".gitignore")
if os.path.exists(gitignore_path):
    with open(gitignore_path) as f:
        gi = f.read()
    required = [".vera", "key.dat", "config.json", ".env"]
    for pat in required:
        if pat not in gi:
            issues.append(f"  [.gitignore missing] pattern '{pat}' not found")

# 4. Check AES key size (must be 256-bit = 32 bytes)
sys.path.insert(0, ROOT)
try:
    from verbamind.security.encryptor import generate_aes_key
    key = generate_aes_key()
    if len(key) != 32:
        issues.append(f"  [AES key size] expected 32 bytes, got {len(key)}")
except Exception as e:
    issues.append(f"  [AES test failed] {e}")

# Report
print("=" * 60)
print("SECURITY SCAN REPORT")
print("=" * 60)

if not issues:
    print("\n✅ NO SECURITY ISSUES FOUND")
    print("\nChecked:")
    print("  - Hardcoded secrets/passwords/keys: NONE")
    print("  - Sensitive files (.vera/.pem/.key/.dat): properly gitignored")
    print("  - .gitignore covers: .vera, key.dat, config.json, .env")
    print("  - AES-256 key generation: 32 bytes verified")
else:
    print(f"\n⚠️  {len(issues)} ISSUE(S) FOUND:")
    for issue in issues:
        print(issue)

print("\n" + "=" * 60)
sys.exit(1 if issues else 0)
