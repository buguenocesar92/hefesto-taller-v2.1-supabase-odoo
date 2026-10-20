#!/usr/bin/env python3
"""Detecta declaraciones "name:" explícitas en un compose YAML.

Considera violación sólo cuando la declaración está en el archivo fuente,
no cuando docker compose infiere el nombre del directorio. Cada violación
se imprime como: "<scope>:<key>", por ejemplo:
    root
    network:default
    volume:cache
    service:db:tmp
"""
from __future__ import annotations
import re
import sys
from pathlib import Path


def top_level_blocks(text: str, key: str) -> list[str]:
    """Devuelve los bloques de un mapeo top-level `key:`."""
    out: list[str] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(rf"^{re.escape(key)}:\s*(?:#.*)?$", line)
        if m:
            i += 1
            buf: list[str] = []
            block_indent = None
            while i < len(lines):
                cur = lines[i]
                stripped = cur.lstrip()
                if stripped == "" or cur.lstrip().startswith("#"):
                    buf.append(cur)
                    i += 1
                    continue
                indent = len(cur) - len(cur.lstrip())
                if block_indent is None:
                    block_indent = indent
                if indent < block_indent:
                    break
                if indent == block_indent and re.match(r"^[A-Za-z][A-Za-z0-9_-]*:", cur):
                    break
                buf.append(cur)
                i += 1
            out.append("\n".join(buf))
        else:
            i += 1
    return out


def named_entries(block: str, min_inner_indent: int) -> list[tuple[str, str]]:
    """Devuelve pares (clave, cuerpo) de entradas con `name:` declarado."""
    entries: list[tuple[str, str]] = []
    lines = block.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        # caso: "  nombre:" (mapeo) - guardamos clave y consumimos el sub-bloque
        m = re.match(rf"^(\s{{{min_inner_indent},}})(\S+):\s*(?:#.*)?$", line)
        if not m:
            i += 1
            continue
        key = m.group(2)
        entry_indent = len(m.group(1))
        body_lines: list[str] = []
        j = i + 1
        while j < len(lines):
            cur = lines[j]
            if cur.strip() == "" or cur.lstrip().startswith("#"):
                body_lines.append(cur)
                j += 1
                continue
            indent = len(cur) - len(cur.lstrip())
            if indent <= entry_indent:
                break
            body_lines.append(cur)
            j += 1
        body = "\n".join(body_lines)
        if re.search(rf"^\s+name:\s*\S+", body, re.M):
            entries.append((key, body))
        i = j
    return entries


def find_volumes_in_service(body: str) -> list[tuple[str, str]]:
    """Devuelve nombres explícitos en entries de volumes de servicio."""
    out: list[tuple[str, str]] = []
    m = re.search(r"^(\s+)volumes:\s*$", body, re.M)
    if not m:
        return out
    base = len(m.group(1))
    after = body[m.end():]
    # items con sangría base+2: "- key: val" ó "  key: val" en formato mapeo
    lines = after.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        # estilo seq: "  - key: val"
        m2 = re.match(rf"^\s{{{base+1},}}-\s+name:\s*(\S+)", line)
        if m2:
            out.append((m2.group(1), line))
            i += 1
            continue
        # estilo map: "  nombre:" dentro de volumes
        m3 = re.match(rf"^\s{{{base+1},}}(\S+):\s*$", line)
        if m3:
            sub_name = m3.group(1)
            i += 1
            while i < len(lines):
                cur = lines[i]
                if cur.strip() == "" or cur.lstrip().startswith("#"):
                    i += 1
                    continue
                if len(cur) - len(cur.lstrip()) <= base + 1:
                    break
                # dentro de la entrada
                if re.match(rf"^\s{{#{base+3},}}name:\s*\S+", cur):
                    out.append((sub_name, cur))
                    break
                i += 1
            continue
        i += 1
    return out


def main() -> int:
    if len(sys.argv) != 2:
        print("uso: yaml-names.py <compose.yml>", file=sys.stderr)
        return 2
    text = Path(sys.argv[1]).read_text()

    # "name:" a nivel raíz: primera coincidencia antes de cualquier clave top-level
    root_match = re.search(r"^name:\s*\S+", text, re.M)
    if root_match:
        print("root")

    # networks / volumes declarados
    for blk in top_level_blocks(text, "networks"):
        for key, _ in named_entries(blk, 2):
            print(f"network:{key}")
    for blk in top_level_blocks(text, "volumes"):
        for key, _ in named_entries(blk, 2):
            print(f"volume:{key}")

    # volúmenes declarados en servicios
    for blk in top_level_blocks(text, "services"):
        for svc_key, body in named_entries(blk, 2):
            for vol_name, _ in find_volumes_in_service(body):
                print(f"service:{svc_key}:{vol_name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
