"""Hashes und kanonisches JSON (wie lf1, bewusst eigene Kopie: lf1 bleibt unveraendert)."""
import hashlib
import json
import os


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def canon_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def json_hash(obj):
    return sha256_bytes(canon_json(obj).encode("utf-8"))


def code_hash(pkg_dir=None):
    """SHA-256 ueber alle .py-Dateien des Pakets (Name + LF-normalisierter Inhalt), wie lf1."""
    if pkg_dir is None:
        pkg_dir = os.path.dirname(os.path.abspath(__file__))
    h = hashlib.sha256()
    for name in sorted(os.listdir(pkg_dir)):
        if name.endswith(".py"):
            with open(os.path.join(pkg_dir, name), "rb") as f:
                body = f.read().replace(b"\r\n", b"\n")
            h.update(name.encode("utf-8") + b"\0" + body + b"\0")
    return h.hexdigest()


def write_once(path, text):
    """Schreibt `text` genau einmal und atomar: Ergebnis erscheint ganz oder gar nicht; existiert path bereits, wird nichts geaendert (False)."""
    tmp = "%s.tmp.%d" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    try:
        try:
            os.link(tmp, path)                      # schlaegt atomar fehl, wenn path existiert
        except FileExistsError:
            return False
        except OSError:                             # Dateisystem ohne Hardlinks: Pruefung + atomarer Austausch
            if os.path.exists(path):
                return False
            os.replace(tmp, path)
            return True
        return True
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
