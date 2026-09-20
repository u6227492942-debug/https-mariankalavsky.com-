#!/usr/bin/env python3
"""
Regeneruje sekciu Fotky v index.html z priečinkovej štruktúry v assets/images/fotky/.

Ako to funguje:
  - jeden priečinok pod fotky/ = jedna kategória (napr. fotky/ludia/, fotky/krajiny/)
  - reportaz/ je špeciálne (CHOOSER): každý podpriečinok je samostatná akcia
      s vlastnou galériou + URL, napr. fotky/reportaz/house-of-kondor/
  - v OSTATNÝCH kategóriách sú podpriečinky SÉRIE: každý podpriečinok sa
      vyrenderuje ako jeden súvislý blok (fotky série idú za sebou, nemiešajú sa).
      Poradie sérií = podľa názvu priečinka ZOSTUPNE (najnovšie hore), takže
      priečinky pomenuj napr. datumom alebo cislom:  2025-06-more, 2024-11-les ...
      alebo 03-..., 02-..., 01-...  (vyššie = novšie = vyššie na stránke).
      Voľné fotky priamo v kategórii (mimo série) idú ako jeden blok na koniec.
  - technika (štítok digital/analóg v lightboxe) sa berie z množiny DIGITAL nižšie
      (podľa názvu súboru); čo tam nie je = analóg.

Použitie po presune fotiek:  python build_fotky.py
"""
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
FOTKY = os.path.join(ROOT_DIR, 'assets', 'images', 'fotky')
IDX = os.path.join(ROOT_DIR, 'index.html')
IMG_EXT = ('.jpg', '.jpeg', '.png', '.webp')

# SK/EN názvy kategórií a akcií. Neznámy priečinok dostane názov odvodený zo slugu.
LABELS = {
    'ludia': ('Ľudia', 'People'),
    'reportaz': ('Reportáž', 'Reportage'),
    'nocna-obloha': ('Nočná obloha', 'Night Sky'),
    'experimenty': ('Experimenty', 'Experiments'),
    'krajiny': ('Krajiny', 'Landscapes'),
    'zvierata': ('Zvieratá', 'Animals'),
    'ostatne': ('Ostatné', 'Other'),
    'house-of-kondor': ('House of Kondor', 'House of Kondor'),
}
ORDER = ['ludia', 'reportaz', 'nocna-obloha', 'experimenty', 'krajiny', 'zvierata', 'ostatne']

# Kategórie, kde podpriečinky = samostatné galérie (vlastná URL), nie série-bloky.
CHOOSER = {'reportaz'}

# Digitálne fotky (podľa názvu súboru). Čo tu nie je, sa označí ako "analóg".
DIGITAL = set("""
mlaka.jpg huliwow.jpg huliedit.jpg vyklad.jpg foto-syntéza.jpg hviezdy.jpg relax.jpg
derealizácia.jpg prilis vela ruk na objatie.jpg DSC_0086.jpg DSC_0097.jpg DSC_0121.jpg
DSC_0297.jpg DSC_0359.jpg DSC_0450.jpg DSC_0535.jpg DSC_0541.jpg
DSC_0920.jpg DSC_0954.jpg DSC_0957.jpg DSC_1089.jpg DSC_1093.jpg DSC_1097.jpg DSC_1099.jpg
DSC_1123.jpg DSC_1144.jpg DSC_1152.jpg DSC_1159.jpg DSC_1179.jpg DSC_1181.jpg DSC_1182.jpg
DSC_1183.jpg DSC_1207.jpg DSC_1219.jpg DSC_1234.jpg DSC_1256.jpg DSC_1294.jpg DSC_1297.jpg
DSC_1307.jpg DSC_1327.jpg DSC_1330.jpg DSC_1339.jpg DSC_1358.jpg DSC_1372.jpg DSC_1417.jpg
DSC_1422.jpg DSC_1424.jpg DSC_1429.jpg DSC_1433.jpg DSC_1498.jpg
""".split())


def label(slug):
    if slug in LABELS:
        return LABELS[slug]
    p = slug.replace('-', ' ').replace('_', ' ').strip()
    p = p[:1].upper() + p[1:]
    return (p, p)


def js(s):
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"


def relurl(path):
    return os.path.relpath(path, ROOT_DIR).replace('\\', '/')


def images_in(folder):
    return [f for f in sorted(os.listdir(folder))
            if os.path.isfile(os.path.join(folder, f)) and f.lower().endswith(IMG_EXT)]


def subdirs(folder):
    return [d for d in sorted(os.listdir(folder)) if os.path.isdir(os.path.join(folder, d))]


def figure(folder, fname):
    tech = 'digital' if fname in DIGITAL else 'analog'
    src = relurl(os.path.join(folder, fname))
    return f'    <figure><img src="{src}" alt="foto" loading="lazy" data-tech="{tech}"></figure>'


def wall(folder, files):
    figs = '\n'.join(figure(folder, f) for f in files)
    return '<div class="wall">\n' + figs + '\n  </div>'


def blocks(cdir):
    """Obsah leaf kategórie ako súvislé bloky:
       najprv série (podpriečinky, ZOSTUPNE = najnovšie hore), potom voľné fotky."""
    out = []
    for series in sorted(subdirs(cdir), reverse=True):
        simgs = images_in(os.path.join(cdir, series))
        if simgs:
            out.append(wall(os.path.join(cdir, series), simgs))
    loose = images_in(cdir)
    if loose:
        out.append(wall(cdir, loose))
    return '\n    '.join(out) if out else '<div class="wall"></div>'


def build():
    cats = subdirs(FOTKY)
    cats = [c for c in ORDER if c in cats] + [c for c in cats if c not in ORDER]

    root_nodes, sections = [], []
    for c in cats:
        cdir = os.path.join(FOTKY, c)
        sk, en = label(c)
        if c in CHOOSER:
            # chooser: podpriečinky sú samostatné akcie (vlastná URL)
            children = []
            for ev in subdirs(cdir):
                evdir = os.path.join(cdir, ev)
                evimgs = images_in(evdir)
                if not evimgs:
                    continue
                esk, een = label(ev)
                lid = 'fotky-' + ev
                children.append(f"{{slug:{js(ev)}, label:{{sk:{js(esk)},en:{js(een)}}}, leaf:{js(lid)}}}")
                sections.append(f'  <!-- Fotky / {sk} / {esk} -->\n  <section class="leaf" id="{lid}">{wall(evdir, evimgs)}</section>\n')
            root_nodes.append(f"{{slug:{js(c)}, label:{{sk:{js(sk)},en:{js(en)}}}, children:[\n      " + ',\n      '.join(children) + "\n    ]}")
        else:
            # leaf: voľné fotky + série-bloky (podpriečinky) v jednej galérii
            lid = 'fotky-' + c
            root_nodes.append(f"{{slug:{js(c)}, label:{{sk:{js(sk)},en:{js(en)}}}, leaf:{js(lid)}}}")
            sections.append(f'  <!-- Fotky / {sk} -->\n  <section class="leaf" id="{lid}">{blocks(cdir)}</section>\n')

    h = open(IDX, encoding='utf-8').read()

    # 1) ROOT Fotky node -> replace from {slug:'fotky', ...} up to {slug:'video',
    rs = h.index("{slug:'fotky',")
    re_ = h.index("{slug:'video',")
    newroot = "{slug:'fotky', label:{sk:'Fotky',en:'Photography'}, children:[\n    " + ',\n    '.join(root_nodes) + "\n  ]},\n  "
    h = h[:rs] + newroot + h[re_:]

    # 2) Fotky sections -> replace from first "<!-- Fotky /" up to "<!-- Video / Klipy -->"
    ss = h.index("  <!-- Fotky /")
    se = h.index("  <!-- Video / Klipy -->")
    h = h[:ss] + '\n'.join(sections) + '\n' + h[se:]

    open(IDX, 'w', encoding='utf-8', newline='').write(h)

    def count(cdir):
        return len(images_in(cdir)) + sum(len(images_in(os.path.join(cdir, e))) for e in subdirs(cdir))

    tot = sum(count(os.path.join(FOTKY, c)) for c in cats)
    print('Rebuilt Fotky:', len(cats), 'categories,', tot, 'photos')
    for c in cats:
        cdir = os.path.join(FOTKY, c)
        loose = len(images_in(cdir))
        subs = subdirs(cdir)
        if subs:
            print(f'  {c}: {count(cdir)}  (voľné {loose}' + ('' if c in CHOOSER else ', série:') + ')')
            for e in sorted(subs, reverse=(c not in CHOOSER)):
                print(f'    {c}/{e}: {len(images_in(os.path.join(cdir, e)))}')
        else:
            print(f'  {c}: {loose}')


if __name__ == '__main__':
    build()
