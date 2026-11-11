"""Genera resources/assets/codecore.ico sin dependencias externas.

Dibuja un cuadrado redondeado oscuro con los símbolos «< / >» y escribe un
archivo .ico con varios tamaños (PNG embebido, soportado desde Windows Vista).

Uso:
    python tools/make_icon.py
"""

from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "resources" / "assets" / "codecore.ico"
SIZES = (16, 32, 48, 64, 128, 256)
BASE = 256

BACKGROUND = (16, 24, 40)  # #101828
CHEVRON = (226, 232, 240)  # #E2E8F0
SLASH = (96, 165, 250)  # #60A5FA


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _rounded_box_coverage(x: float, y: float, box: tuple[float, float, float, float], radius: float) -> float:
    left, top, right, bottom = box
    half_x = (right - left) / 2
    half_y = (bottom - top) / 2
    center_x = left + half_x
    center_y = top + half_y
    qx = abs(x - center_x) - (half_x - radius)
    qy = abs(y - center_y) - (half_y - radius)
    outside = math.hypot(max(qx, 0.0), max(qy, 0.0))
    inside = min(max(qx, qy), 0.0)
    distance = outside + inside - radius
    return _clamp(0.5 - distance)


def _segment_distance(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    dx = bx - ax
    dy = by - ay
    length_squared = dx * dx + dy * dy
    if length_squared == 0:
        return math.hypot(px - ax, py - ay)
    t = _clamp(((px - ax) * dx + (py - ay) * dy) / length_squared)
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _blend(pixel: list[float], color: tuple[int, int, int], coverage: float) -> None:
    if coverage <= 0:
        return
    source_alpha = coverage
    destination_alpha = pixel[3] / 255
    out_alpha = source_alpha + destination_alpha * (1 - source_alpha)
    if out_alpha <= 0:
        return
    for channel in range(3):
        source = color[channel] / 255
        destination = pixel[channel] / 255
        pixel[channel] = (source * source_alpha + destination * destination_alpha * (1 - source_alpha)) / out_alpha * 255
    pixel[3] = out_alpha * 255


def _render_base() -> list[list[float]]:
    pixels = [[0.0, 0.0, 0.0, 0.0] for _ in range(BASE * BASE)]
    box = (6.0, 6.0, 250.0, 250.0)
    radius = 52.0
    for y in range(BASE):
        for x in range(BASE):
            coverage = _rounded_box_coverage(x + 0.5, y + 0.5, box, radius)
            if coverage > 0:
                _blend(pixels[y * BASE + x], BACKGROUND, coverage)

    # Símbolos: < / >
    stroke = 17.0
    half = stroke / 2
    segments = [
        ((92.0, 92.0), (62.0, 128.0), CHEVRON),
        ((62.0, 128.0), (92.0, 164.0), CHEVRON),
        ((164.0, 92.0), (194.0, 128.0), CHEVRON),
        ((194.0, 128.0), (164.0, 164.0), CHEVRON),
        ((146.0, 84.0), (110.0, 172.0), SLASH),
    ]
    for start, end, color in segments:
        (ax, ay), (bx, by) = start, end
        left = int(min(ax, bx) - half - 2)
        right = int(max(ax, bx) + half + 2)
        top = int(min(ay, by) - half - 2)
        bottom = int(max(ay, by) + half + 2)
        for y in range(max(0, top), min(BASE, bottom + 1)):
            for x in range(max(0, left), min(BASE, right + 1)):
                distance = _segment_distance(x + 0.5, y + 0.5, ax, ay, bx, by)
                coverage = _clamp(half + 0.5 - distance)
                if coverage > 0:
                    _blend(pixels[y * BASE + x], color, coverage)
    return pixels


def _downscale(pixels: list[list[float]], target: int) -> list[list[float]]:
    if target == BASE:
        return pixels
    factor = BASE // target
    result: list[list[float]] = []
    for y in range(target):
        for x in range(target):
            total = [0.0, 0.0, 0.0, 0.0]
            for dy in range(factor):
                for dx in range(factor):
                    source = pixels[(y * factor + dy) * BASE + (x * factor + dx)]
                    for channel in range(4):
                        total[channel] += source[channel]
            count = factor * factor
            result.append([value / count for value in total])
    return result


def _png(pixels: list[list[float]], size: int) -> bytes:
    raw = bytearray()
    for y in range(size):
        raw.append(0)  # filtro None
        for x in range(size):
            pixel = pixels[y * size + x]
            raw.extend(
                (
                    int(_clamp(pixel[0], 0, 255)),
                    int(_clamp(pixel[1], 0, 255)),
                    int(_clamp(pixel[2], 0, 255)),
                    int(_clamp(pixel[3], 0, 255)),
                )
            )

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    header = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )


def build_icon() -> Path:
    base = _render_base()
    images = [(size, _png(_downscale(base, size), size)) for size in SIZES]

    header = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    entries = bytearray()
    payload = bytearray()
    for size, data in images:
        dimension = 0 if size >= 256 else size
        entries.extend(
            struct.pack("<BBBBHHII", dimension, dimension, 0, 0, 1, 32, len(data), offset)
        )
        payload.extend(data)
        offset += len(data)

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_bytes(header + bytes(entries) + bytes(payload))
    return TARGET


if __name__ == "__main__":
    path = build_icon()
    print(f"Icono generado: {path} ({path.stat().st_size} bytes)")
