"""
Gera os SVGs animados (efeito maquina de escrever) usados no topo do README.md.

Mascara de revelacao via <clipPath> com <animate> de largura, cursor piscando
via <rect> animado, gradiente de borda e "scanline" em movimento -- tudo em
SMIL puro, sem JavaScript, para funcionar como <img>/<picture> no README do
GitHub.

Uso:
    python generate_profile.py
Gera: profile-dark.svg e profile-light.svg
"""
from dataclasses import dataclass, field

FONT_SIZE = 15
CHAR_W = FONT_SIZE * 0.6          # largura media de um glifo monoespacado
LINE_HEIGHT = 24
START_X = 30
FIRST_LINE_Y = 92
TITLEBAR_H = 40
TOP_PAD = 26
BOTTOM_PAD = 34
RIGHT_PAD = 40

TYPE_SPEED = 0.012                # segundos por caractere
LINE_PAUSE = 0.05                 # pausa entre linhas
START_DELAY = 0.3                 # atraso antes de comecar a digitar

Segment = tuple  # (texto, classe)


@dataclass
class Line:
    segments: list = field(default_factory=list)  # list[Segment]

    @property
    def text(self):
        return "".join(t for t, _ in self.segments)


def kv(label, value, dot_col=30):
    prefix = f". {label}:"
    dots = max(3, dot_col - len(prefix))
    return Line([(". ", "cc"), (label, "key"), (": " + ("." * dots) + " ", "cc"), (value, "value")])


def header(text):
    dashes = "-" + ("—" * 44) + "-"
    return Line([(text, "head"), (" " + dashes, "cc")])


def section(title):
    dashes = "-" + ("—" * (48 - len(title)))
    return Line([(f"- {title}", "accent"), (" " + dashes, "cc")])


def spacer():
    return Line([(". ", "cc")])


LINES = [
    header("micael@dev"),
    kv("Nome", "Micael Parise"),
    kv("Cargo", "Desenvolvedor Full-stack"),
    kv("Foco", "Back-end em PHP / Laravel"),
    spacer(),
    section("Stack"),
    kv("Back-end", "PHP - Laravel - MySQL - SQLite"),
    kv("Front-end", "Blade - Alpine.js - Tailwind - Vue - Nuxt"),
    kv("Infra", "AWS - Docker - GitHub Actions"),
    spacer(),
    section("Contato"),
    kv("LinkedIn", "linkedin.com/in/micaelparise"),
    kv("Instagram", "instagram.com/micaelparise"),
    spacer(),
    Line([(". status: ", "cc"), ("pronto para novos desafios", "accent")]),
]


THEMES = {
    "dark": dict(
        bg1="#0B1120", bg2="#050816",
        titlebar="#0B1120",
        head="#7C3AED", key="#22D3EE", value="#E5E7EB", cc="#475569",
        accent="#10B981", cursor="#22D3EE",
        term_label="#64748B", live_label="#F87171", live_dot="#F87171",
        grad_a="#22D3EE", grad_b="#7C3AED",
        border_a="#7C3AED", border_b="#22D3EE", border_c="#10B981",
        scan_stop="#22D3EE", scan_mid="#A5F3FC",
        scanline_color="#7DD3FC", scanline_op="0.05",
        panel_stroke_op="0.35", text_fill="#dbeafe",
    ),
    "light": dict(
        bg1="#F8FAFC", bg2="#E2E8F0",
        titlebar="#FFFFFF",
        head="#6D28D9", key="#0E7490", value="#1E293B", cc="#94A3B8",
        accent="#047857", cursor="#0E7490",
        term_label="#64748B", live_label="#DC2626", live_dot="#DC2626",
        grad_a="#0E7490", grad_b="#6D28D9",
        border_a="#6D28D9", border_b="#0E7490", border_c="#047857",
        scan_stop="#0E7490", scan_mid="#67E8F9",
        scanline_color="#0F172A", scanline_op="0.035",
        panel_stroke_op="0.25", text_fill="#0f172a",
    ),
}


def build_typing(lines):
    """Calcula tempos e larguras de digitacao para cada linha."""
    t = START_DELAY
    out = []
    for i, line in enumerate(lines):
        n_chars = len(line.text)
        dur = max(0.08, n_chars * TYPE_SPEED)
        width_px = max(10.0, n_chars * CHAR_W)
        y = FIRST_LINE_Y + i * LINE_HEIGHT
        out.append(dict(line=line, begin=round(t, 3), dur=round(dur, 3), width=round(width_px, 1), y=y))
        t += dur + LINE_PAUSE
    return out, t


def render_svg(theme_name):
    theme = THEMES[theme_name]
    typed, end_t = build_typing(LINES)

    max_chars = max(len(l.text) for l in LINES)
    width = int(START_X + max_chars * CHAR_W + RIGHT_PAD)
    height = int(TITLEBAR_H + TOP_PAD + len(LINES) * LINE_HEIGHT + BOTTOM_PAD)

    clip_defs = []
    text_groups = []
    for i, t in enumerate(typed):
        clip_defs.append(
            f'<clipPath id="lc{i}"><rect x="{START_X - 4}" y="{t["y"] - FONT_SIZE - 2}" '
            f'width="0" height="{LINE_HEIGHT}">'
            f'<animate attributeName="width" from="0" to="{t["width"] + 8}" dur="{t["dur"]}s" '
            f'begin="{t["begin"]}s" fill="freeze" calcMode="linear"/></rect></clipPath>'
        )

        tspans = []
        for seg_text, seg_class in t["line"].segments:
            esc = (seg_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
            tspans.append(f'<tspan class="{seg_class}">{esc}</tspan>')
        # primeiro tspan carrega x/y explicitos, os demais fluem na sequencia
        first_seg, first_class = t["line"].segments[0]
        first_esc = first_seg.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        tspans[0] = f'<tspan x="{START_X}" y="{t["y"]}" class="{first_class}">{first_esc}</tspan>'

        text_groups.append(
            f'<g clip-path="url(#lc{i})"><text x="{START_X}" y="0" fill="{theme["text_fill"]}">'
            f'{"".join(tspans)}</text></g>'
        )

    # cursor: pula para o inicio de cada linha e "anda" ate o fim dela enquanto digita
    cursor_anims = []
    for t in typed:
        cy = t["y"] - FONT_SIZE
        cursor_anims.append(f'<set attributeName="y" to="{cy}" begin="{t["begin"]}s"/>')
        cursor_anims.append(f'<set attributeName="x" to="{START_X}" begin="{t["begin"]}s"/>')
        cursor_anims.append(
            f'<animate attributeName="x" from="{START_X}" to="{START_X + t["width"]}" '
            f'dur="{t["dur"]}s" begin="{t["begin"]}s" fill="freeze" calcMode="linear"/>'
        )
    cursor_anims.append(
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
        f'dur="0.9s" begin="{START_DELAY}s" repeatCount="indefinite"/>'
    )

    scan_dur = round(max(end_t + 1.5, 4.0), 2)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<defs>
  <linearGradient id="asciiGrad" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="{theme['grad_a']}">
      <animate attributeName="stop-color" values="{theme['grad_a']};{theme['grad_b']};{theme['grad_a']}" dur="9s" repeatCount="indefinite"/>
    </stop>
    <stop offset="100%" stop-color="{theme['grad_b']}"/>
  </linearGradient>
  <linearGradient id="borderGrad" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="{theme['border_a']}"/>
    <stop offset="50%" stop-color="{theme['border_b']}"/>
    <stop offset="100%" stop-color="{theme['border_c']}"/>
  </linearGradient>
  <radialGradient id="bgGlow" cx="30%" cy="15%" r="85%">
    <stop offset="0%" stop-color="{theme['bg1']}"/>
    <stop offset="100%" stop-color="{theme['bg2']}"/>
  </radialGradient>
  <linearGradient id="scanGrad" x1="0%" y1="0%" x2="0%" y2="100%">
    <stop offset="0%" stop-color="{theme['scan_stop']}" stop-opacity="0"/>
    <stop offset="45%" stop-color="{theme['scan_stop']}" stop-opacity="0.05"/>
    <stop offset="50%" stop-color="{theme['scan_mid']}" stop-opacity="0.55"/>
    <stop offset="55%" stop-color="{theme['scan_stop']}" stop-opacity="0.05"/>
    <stop offset="100%" stop-color="{theme['grad_b']}" stop-opacity="0"/>
  </linearGradient>
  <pattern id="scanlines" width="4" height="4" patternUnits="userSpaceOnUse">
    <rect width="4" height="1" fill="{theme['scanline_color']}" opacity="{theme['scanline_op']}"/>
  </pattern>
  {"".join(clip_defs)}
  <style>
    .key    {{ font-family: 'Courier New', Consolas, monospace; font-size: {FONT_SIZE}px; fill: {theme['key']}; font-weight: bold; }}
    .value  {{ font-family: 'Courier New', Consolas, monospace; font-size: {FONT_SIZE}px; fill: {theme['value']}; }}
    .cc     {{ font-family: 'Courier New', Consolas, monospace; font-size: {FONT_SIZE}px; fill: {theme['cc']}; }}
    .head   {{ font-family: 'Courier New', Consolas, monospace; font-size: 17px; fill: {theme['head']}; font-weight: bold; }}
    .accent {{ font-family: 'Courier New', Consolas, monospace; font-size: {FONT_SIZE}px; fill: {theme['accent']}; font-weight: bold; }}
    text, tspan {{ white-space: pre; }}
    .term-label {{ font-family: 'Courier New', Consolas, monospace; font-size: 12px; fill: {theme['term_label']}; letter-spacing: 0.5px; }}
    .live-label {{ font-family: 'Courier New', Consolas, monospace; font-size: 10px; fill: {theme['live_label']}; letter-spacing: 1px; }}
    .cursor-blink {{ fill: {theme['cursor']}; }}
  </style>
</defs>

<rect width="{width}" height="{height}" rx="18" fill="url(#bgGlow)"/>
<rect width="{width}" height="{height}" rx="18" fill="url(#scanlines)"/>

<g id="titlebar">
  <rect x="3" y="3" width="{width - 6}" height="34" rx="16" fill="{theme['titlebar']}" fill-opacity="0.85"/>
  <circle cx="24" cy="20" r="5" fill="#EF4444"><animate attributeName="opacity" values="1;0.55;1" dur="4s" repeatCount="indefinite"/></circle>
  <circle cx="42" cy="20" r="5" fill="#F59E0B"><animate attributeName="opacity" values="1;0.55;1" dur="4s" begin="0.3s" repeatCount="indefinite"/></circle>
  <circle cx="60" cy="20" r="5" fill="#10B981"><animate attributeName="opacity" values="1;0.55;1" dur="4s" begin="0.6s" repeatCount="indefinite"/></circle>
  <text x="{width / 2}" y="25" text-anchor="middle" class="term-label">micael@dev ~ % ./perfil.sh --live</text>
  <circle cx="{width - 58}" cy="20" r="4" fill="{theme['live_dot']}">
    <animate attributeName="opacity" values="1;0.15;1" dur="1.1s" repeatCount="indefinite"/>
  </circle>
  <text x="{width - 48}" y="24" class="live-label">LIVE</text>
</g>

<g>
  {"".join(text_groups)}
  <rect x="{START_X}" y="{FIRST_LINE_Y - FONT_SIZE}" width="{CHAR_W - 2}" height="{FONT_SIZE + 4}" class="cursor-blink" opacity="0">
    {"".join(cursor_anims)}
  </rect>
</g>

<rect x="0" y="-70" width="{width}" height="70" fill="url(#scanGrad)" opacity="0.7" style="mix-blend-mode:screen">
  <animateTransform attributeName="transform" type="translate" from="0 -70" to="0 {height + 70}" dur="{scan_dur}s" repeatCount="indefinite"/>
</rect>

<rect x="3" y="3" width="{width - 6}" height="{height - 6}" rx="16" fill="none" stroke="url(#borderGrad)" stroke-width="2" opacity="0.8">
  <animate attributeName="opacity" values="0.5;0.95;0.5" dur="3.2s" repeatCount="indefinite"/>
</rect>
</svg>
'''
    return svg


if __name__ == "__main__":
    for theme_name in THEMES:
        svg = render_svg(theme_name)
        out_path = f"profile-{theme_name}.svg"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"Gerado {out_path}")
