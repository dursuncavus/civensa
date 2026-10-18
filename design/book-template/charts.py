"""Editable sample charts (SVG with live text + PDF with embedded TrueType) in Fira Sans."""
import os, glob
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter
import data as D

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'grafikler')
os.makedirs(OUT, exist_ok=True)
for f in glob.glob(os.path.join(HERE, '..', 'gf', 'ofl', 'firasans*', '*.ttf')):
    font_manager.fontManager.addfont(f)

plt.rcParams.update({
    'font.family': 'Fira Sans Condensed', 'font.size': 7.5, 'svg.fonttype': 'none', 'pdf.fonttype': 42,
    'axes.edgecolor': '#9a9a96', 'axes.linewidth': 0.5, 'axes.labelcolor': '#3b3b39', 'text.color': '#262624',
    'xtick.color': '#52514e', 'ytick.color': '#52514e', 'xtick.major.width': 0.5, 'ytick.major.width': 0.5,
    'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 150,
})
S = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300']   # = swatches Grafik 1–6
MUTED, GRID = '#52514e', '#e4e3df'
MM = 1 / 25.4
WIDTH = 165 * MM


def tr(v, dec=0):
    s = f'{v:,.{dec}f}'
    return s.replace(',', '_').replace('.', ',').replace('_', '.')


def save(fig, name):
    for ext in ('svg', 'pdf'):
        fig.savefig(os.path.join(OUT, f'{name}.{ext}'), format=ext, transparent=True)
    fig.savefig(os.path.join(OUT, f'{name}_onizleme.png'), format='png', dpi=160, facecolor='white')
    plt.close(fig)


# 1 — donut: economic classification (≤6 slices, smallest folded into "Diğer")
def donut():
    labels = ['Personel Giderleri', 'Sosyal Güvenlik Kurumlarına\nDevlet Primi Giderleri', 'Mal ve Hizmet Alım Giderleri',
              'Cari Transferler', 'Sermaye Giderleri', 'Diğer (faiz, sermaye transferi,\nborç verme, yedek ödenek)']
    vals = [2_223_750_000, 402_150_000, 5_038_700_379, 744_200_000, 3_285_313_343, 210_816_469]
    total = sum(vals)
    fig, ax = plt.subplots(figsize=(WIDTH, 80 * MM))
    wedges, _ = ax.pie(vals, colors=S, startangle=90, counterclock=False,
                       wedgeprops=dict(width=0.32, edgecolor='white', linewidth=1.5))
    ax.set_aspect('equal')
    ax.text(0, 0.08, tr(total / 1e9, 1) + ' milyar TL', ha='center', va='center', fontsize=10, fontweight='semibold', family='Fira Sans')
    ax.text(0, -0.12, '2027 toplam', ha='center', va='center', fontsize=7, color=MUTED)
    import math
    for w, lab, v in zip(wedges, labels, vals):
        ang = math.radians((w.theta1 + w.theta2) / 2)
        x, y = math.cos(ang), math.sin(ang)
        ha = 'left' if x >= 0 else 'right'
        ax.annotate(f'{lab}\n%{tr(v / total * 100, 1)} · {tr(v / 1e6, 0)} milyon TL', xy=(0.86 * x, 0.86 * y),
                    xytext=(1.28 * x + (0.12 if x >= 0 else -0.12), 1.18 * y), ha=ha, va='center', fontsize=7,
                    arrowprops=dict(arrowstyle='-', color='#9a9a96', lw=0.5, shrinkA=0, shrinkB=0,
                                    connectionstyle='angle,angleA=0,angleB=90' if False else 'arc3'))
    ax.set_xlim(-2.4, 2.4); ax.set_ylim(-1.5, 1.5)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
    save(fig, '01_halka_ekonomik_siniflandirma')


# 2 — horizontal bar: 33 directorates, long labels, single series sorted
def bars_directorates():
    rows, _ = D.directorate_budget()
    vals = [(d, float(v.replace('.', '').replace(',', '.'))) for d, v, _ in rows]
    vals[5] = (vals[5][0], 1_189_138_909.0)   # keep the sample chart readable (table uses the maximum)
    vals.sort(key=lambda x: x[1])
    fig, ax = plt.subplots(figsize=(WIDTH, 205 * MM))
    y = range(len(vals))
    ax.barh(list(y), [v / 1e6 for _, v in vals], height=0.62, color=S[0], edgecolor='white', linewidth=0.5)
    ax.set_yticks(list(y), [d for d, _ in vals], fontsize=7)
    ax.tick_params(axis='y', length=0)
    for i, (_, v) in enumerate(vals):
        ax.text(v / 1e6 + 8, i, tr(v / 1e6, 1), va='center', fontsize=6.5, color='#262624')
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: tr(x, 0)))
    ax.set_xlabel('milyon TL', fontsize=7, color=MUTED, loc='right')
    ax.grid(axis='x', color=GRID, linewidth=0.5); ax.set_axisbelow(True)
    ax.spines['left'].set_visible(False)
    ax.set_xlim(0, max(v for _, v in vals) / 1e6 * 1.12)
    ax.set_ylim(-0.6, len(vals) - 0.4)
    fig.subplots_adjust(left=0.30, right=0.97, top=0.99, bottom=0.06)
    save(fig, '02_yatay_cubuk_mudurluk_butceleri')


# 3 — columns: population by year (single series)
def columns_population():
    years = list(range(2015, 2026))
    pop = [232_984, 236_440, 243_474, 247_736, 250_896, 257_362, 266_154, 272_021, 275_000, 279_312, 283_147]
    fig, ax = plt.subplots(figsize=(WIDTH, 75 * MM))
    ax.bar(years, pop, width=0.62, color=S[0], edgecolor='white', linewidth=0.5)
    for x, v in zip(years, pop):
        ax.text(x, v + 2500, tr(v), ha='center', va='bottom', fontsize=6.5)
    ax.set_ylim(0, max(pop) * 1.12)
    ax.set_xticks(years, [str(x) for x in years])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: tr(x)))
    ax.grid(axis='y', color=GRID, linewidth=0.5); ax.set_axisbelow(True)
    ax.tick_params(axis='x', length=0)
    fig.subplots_adjust(left=0.08, right=0.99, top=0.97, bottom=0.10)
    save(fig, '03_sutun_nufus_yillara_gore')


# 4 — lines: three programme groups over time (≤3 series, direct labels + legend)
def lines_programmes():
    years = list(range(2023, 2030))
    series = {
        'Hizmet Programları': [4.1, 5.2, 6.8, 8.6, 10.6, 12.9, 15.4],
        'Yönetim ve Destek Programı': [1.9, 2.4, 3.0, 3.9, 5.0, 6.1, 7.3],
        'Program Dışı Giderler': [0.3, 0.4, 0.5, 0.6, 0.7, 0.9, 1.1],
    }
    fig, ax = plt.subplots(figsize=(WIDTH, 80 * MM))
    for (name, v), c in zip(series.items(), S):
        ax.plot(years, v, color=c, linewidth=2, marker='o', markersize=4.5, markeredgecolor='white', markeredgewidth=1, label=name)
        ax.text(years[-1] + 0.15, v[-1], f'{name}\n{tr(v[-1], 1)} milyar TL', va='center', fontsize=6.8)
    ax.axvline(2026.5, color='#bdbcb6', linewidth=0.6, linestyle=(0, (2, 2)))
    ax.text(2026.6, 15.6, 'Tahmin →', fontsize=6.5, color=MUTED, va='bottom')
    ax.set_xticks(years, [str(x) for x in years])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: tr(x, 0)))
    ax.set_ylabel('milyar TL', fontsize=7, color=MUTED)
    ax.grid(axis='y', color=GRID, linewidth=0.5); ax.set_axisbelow(True)
    ax.set_xlim(2022.6, 2031.4)
    ax.legend(loc='upper center', bbox_to_anchor=(0.42, -0.09), frameon=False, fontsize=7, ncol=3)
    fig.subplots_adjust(left=0.07, right=0.99, top=0.97, bottom=0.18)
    save(fig, '04_cizgi_program_gruplari')


# 5 — 100% stacked horizontal bars: staff status by age group (3 segments, 2px gaps, labels)
def stacked_staff():
    groups = ['18–25', '26–35', '36–45', '46–55', '56 ve üzeri']
    parts = {'Memur': [12, 28, 41, 47, 52], 'İşçi': [38, 30, 33, 38, 41], 'Sözleşmeli Personel': [50, 42, 26, 15, 7]}
    fig, ax = plt.subplots(figsize=(WIDTH, 62 * MM))
    left = [0] * len(groups)
    for (name, v), c in zip(parts.items(), S):
        ax.barh(groups, v, left=left, color=c, edgecolor='white', linewidth=1.5, height=0.6, label=name)
        for i, (l, x) in enumerate(zip(left, v)):
            if x >= 6:
                ax.text(l + x / 2, i, f'%{x}', ha='center', va='center', fontsize=6.8, color='white', fontweight='semibold')
        left = [l + x for l, x in zip(left, v)]
    ax.set_xlim(0, 100); ax.invert_yaxis()
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f'%{int(x)}'))
    ax.tick_params(axis='y', length=0)
    ax.spines['left'].set_visible(False)
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=3, frameon=False, fontsize=7)
    fig.subplots_adjust(left=0.12, right=0.98, top=0.86, bottom=0.12)
    save(fig, '05_yuzde_yigilmis_personel_durumu')


if __name__ == '__main__':
    donut(); bars_directorates(); columns_population(); lines_programmes(); stacked_staff()
    print(sorted(os.listdir(OUT)))
