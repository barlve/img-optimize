#!/usr/bin/env python3
"""img-optimize — kompres & konversi gambar untuk aset web (JPEG/PNG → WebP/AVIF).

Butuh Pillow: pip install pillow
    python3 main.py ./public --webp --kualitas 82 --lebar-maks 1600
    python3 main.py foto.jpg --out hasil/ --png
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow belum terpasang: pip install pillow"); raise SystemExit(2)

EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}


def proses(src: Path, out_dir: Path, format_target: str, kualitas: int, lebar_maks: int) -> tuple[int, int]:
    img = Image.open(src)
    if lebar_maks and img.width > lebar_maks:
        tinggi = int(img.height * lebar_maks / img.width)
        img = img.resize((lebar_maks, tinggi), Image.LANCZOS)
    if img.mode in ("RGBA", "P") and format_target in ("jpeg", "jpg"):
        latar = Image.new("RGB", img.size, (255, 255, 255))
        latar.paste(img.convert("RGBA"), mask=img.convert("RGBA").split()[-1])
        img = latar
    out_dir.mkdir(parents=True, exist_ok=True)
    nama = src.with_suffix("." + ("jpg" if format_target == "jpeg" else format_target)).name
    tujuan = out_dir / nama
    if format_target in ("jpeg", "jpg"):
        img.convert("RGB").save(tujuan, "JPEG", quality=kualitas, optimize=True, progressive=True)
    elif format_target == "webp":
        img.save(tujuan, "WEBP", quality=kualitas, method=6)
    elif format_target == "avif":
        img.save(tujuan, "AVIF", quality=kualitas)
    else:
        img.save(tujuan, "PNG", optimize=True)
    return src.stat().st_size, tujuan.stat().st_size


def main() -> int:
    ap = argparse.ArgumentParser(description="img-optimize")
    ap.add_argument("path")
    ap.add_argument("--out", default=None, help="folder hasil (default: sebelah asli)")
    ap.add_argument("--webp", action="store_true")
    ap.add_argument("--avif", action="store_true")
    ap.add_argument("--png", action="store_true")
    ap.add_argument("--kualitas", type=int, default=82)
    ap.add_argument("--lebar-maks", type=int, default=1600)
    a = ap.parse_args()

    target = "webp" if a.webp else "avif" if a.avif else "png" if a.png else "webp"
    p = Path(a.path)
    files = [p] if p.is_file() else [f for f in p.rglob("*") if f.suffix.lower() in EXT]
    if not files:
        print("Tidak ada gambar."); return 1

    total_awal = total_akhir = 0
    for f in files:
        out_dir = Path(a.out) if a.out else f.parent
        try:
            awal, akhir = proses(f, out_dir, target, a.kualitas, a.lebar_maks)
            total_awal += awal; total_akhir += akhir
            print(f"{f.name:40} {awal/1024:8.1f} KB → {akhir/1024:8.1f} KB ({target})")
        except Exception as e:  # noqa: BLE001
            print(f"⚠️  {f.name}: {type(e).__name__}")

    if total_awal:
        hemat = 100 - (total_akhir * 100 // total_awal)
        print(f"\n{len(files)} gambar · {total_awal/1048576:.2f} MB → {total_akhir/1048576:.2f} MB · hemat {hemat}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
