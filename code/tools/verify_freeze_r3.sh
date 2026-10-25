#!/bin/bash
# verify_freeze_r3.sh - unabhaengige Nachrechnung des Freeze-Hashs ohne Python: sha256sum, openssl und node muessen identisch sein.
# Aufruf im Repo-Wurzelordner: bash code/tools/verify_freeze_r3.sh   (liest register/FREEZE_MANIFEST_R3.txt)
set -e
M=register/FREEZE_MANIFEST_R3.txt
ok=1
# 1) Hash des Manifests mit drei Werkzeugen
a=$(sha256sum "$M" | cut -d' ' -f1)
b=$(openssl dgst -sha256 "$M" | awk '{print $NF}')
c=$(node -e 'const c=require("crypto"),f=require("fs");console.log(c.createHash("sha256").update(f.readFileSync(process.argv[1])).digest("hex"))' "$M")
echo "FREEZE_HASH sha256sum=$a"; echo "FREEZE_HASH openssl  =$b"; echo "FREEZE_HASH node     =$c"
[ "$a" = "$b" ] && [ "$b" = "$c" ] || { echo "FEHLER: Manifest-Hash uneinheitlich"; ok=0; }
# 2) jede aufgelistete Datei: Hash neu (Texte LF-normalisiert) gegen Manifestzeile
while read -r grp path h; do
  case "$grp" in spec|code|data) ;; *) continue;; esac
  if [[ "$path" == *.md || "$path" == *.txt ]]; then x=$(sed 's/\r$//' "$path" | sha256sum | cut -d' ' -f1); else x=$(sha256sum "$path" | cut -d' ' -f1); fi
  if [ "$x" = "$h" ]; then echo "ok   $path"; else echo "FEHLER $path ist $x, Manifest sagt $h"; ok=0; fi
done < "$M"
[ $ok = 1 ] && echo "ALLES IDENTISCH" || { echo "ABWEICHUNG"; exit 1; }
