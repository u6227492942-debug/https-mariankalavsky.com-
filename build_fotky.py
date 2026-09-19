#!/usr/bin/env python3
"""
Regeneruje sekciu Fotky v index.html z priečinkovej štruktúry v assets/images/fotky/.

Ako to funguje:
  - jeden priečinok pod fotky/ = jedna kategória (napr. fotky/portrety/, fotky/krajiny/)
  - reportaz/ je špeciálne: každý podpriečinok je pomenovaná akcia (vlastná galéria + URL)
      napr. fotky/reportaz/house-of-kondor/
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


def build():
    cats = subdirs(FOTKY)
    cats = [c for c in ORDER if c in cats] + [c for c in cats if c not in ORDER]

    root_nodes, sections = [], []
    for c in cats:
        cdir = os.path.join(FOTKY, c)
        sk, en = label(c)
        imgs = images_in(cdir)
        events = subdirs(cdir)
        if events and not imgs:
            # chooser: podpriečinky sú akcie
            children = []
            for ev in events:
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
            lid = 'fotky-' + c
            root_nodes.append(f"{{slug:{js(c)}, label:{{sk:{js(sk)},en:{js(en)}}}, leaf:{js(lid)}}}")
            sections.append(f'  <!-- Fotky / {sk} -->\n  <section class="leaf" id="{lid}">{wall(cdir, imgs)}</section>\n')

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
    tot = sum(len(images_in(os.path.join(FOTKY, c))) or sum(len(images_in(os.path.join(FOTKY, c, e))) for e in subdirs(os.path.join(FOTKY, c))) for c in cats)
    print('Rebuilt Fotky:', len(cats), 'categories,', tot, 'photos')
    for c in cats:
        cdir = os.path.join(FOTKY, c)
        n = len(images_in(cdir))
        if n:
            print(f'  {c}: {n}')
        else:
            for e in subdirs(cdir):
                print(f'  {c}/{e}: {len(images_in(os.path.join(cdir, e)))}')


if __name__ == '__main__':
    build()
