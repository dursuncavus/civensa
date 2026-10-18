import json, re, sys, os
import xml.etree.ElementTree as ET

D = sys.argv[1]
OUT = sys.argv[2]

dm = ET.parse(os.path.join(D, 'designmap.xml')).getroot()
spread_files = [e.get('src') for e in dm if e.tag.endswith('Spread') and e.get('src', '').startswith('Spreads/')]

# story -> list of page names where its frames appear (first page)
story_pages = {}
for si, sf in enumerate(spread_files):
    root = ET.parse(os.path.join(D, sf)).getroot()
    spread = root[0]
    pages = []
    for p in spread.iter():
        if p.tag == 'Page':
            pages.append(p.get('Name'))
    for tf in spread.iter():
        if tf.tag == 'TextFrame':
            st = tf.get('ParentStory')
            if st and st not in story_pages:
                # page determination: approximate by x of frame transform vs pages; take first page of spread if unknown
                tr = tf.get('ItemTransform', '1 0 0 1 0 0').split()
                x = float(tr[4])
                pg = pages[0] if pages else '?'
                if len(pages) == 2 and x > 0:
                    pg = pages[1]
                story_pages[st] = (si, pg)


def text_of(el):
    parts = []
    for n in el.iter():
        if n.tag == 'Content' and n.text:
            parts.append(n.text)
        elif n.tag == 'Br':
            parts.append(' ')
    return re.sub(r'\s+', ' ', ''.join(parts)).strip()

tables = []
for e in dm:
    if not e.tag.endswith('Story'):
        continue
    src = e.get('src')
    if not src:
        continue
    root = ET.parse(os.path.join(D, src)).getroot()
    story = root[0]
    sid = story.get('Self')
    sp = story_pages.get(sid, (9999, '?'))
    # collect paragraphs preceding tables (headings) in order
    last_text = []
    for node in story.iter():
        if node.tag == 'Table':
            ncols = int(node.get('ColumnCount'))
            nrows = int(node.get('BodyRowCount', 0)) + int(node.get('HeaderRowCount', 0)) + int(node.get('FooterRowCount', 0))
            grid = [[None] * ncols for _ in range(nrows)]
            cells = []
            for c in node:
                if c.tag != 'Cell':
                    continue
                col, row = map(int, c.get('Name').split(':'))
                rs, cs = int(c.get('RowSpan', 1)), int(c.get('ColumnSpan', 1))
                t = text_of(c)
                cells.append((row, col, rs, cs, t))
                if row < nrows and col < ncols:
                    grid[row][col] = t
                    for r in range(row, min(row + rs, nrows)):
                        for cc in range(col, min(col + cs, ncols)):
                            if (r, cc) != (row, col):
                                grid[r][cc] = '→' if r == row else '↓'
            tables.append({'id': node.get('Self'), 'story': sid, 'spread': sp[0], 'page': sp[1],
                           'rows': grid, 'context': ' | '.join(last_text[-3:])})
        elif node.tag == 'ParagraphStyleRange':
            pass
    # heading context: crude — paragraphs text before each table
    # second pass to get context properly
idx = {t['id']: t for t in tables}
for e in dm:
    if not e.tag.endswith('Story') or not e.get('src'):
        continue
    story = ET.parse(os.path.join(D, e.get('src'))).getroot()[0]
    buf = []
    def walk(n):
        for ch in n:
            if ch.tag == 'Table':
                if ch.get('Self') in idx:
                    idx[ch.get('Self')]['context'] = ' || '.join(x for x in buf[-4:] if x)
                buf.clear()
                continue
            if ch.tag == 'Content' and ch.text:
                if buf:
                    buf[-1] += ch.text
                else:
                    buf.append(ch.text)
            elif ch.tag in ('Br',):
                buf.append('')
            walk(ch)
    walk(story)

tables.sort(key=lambda t: (t['spread'], t['id']))
json.dump(tables, open(OUT, 'w'), ensure_ascii=False, indent=0)
print(len(tables), 'tables')
