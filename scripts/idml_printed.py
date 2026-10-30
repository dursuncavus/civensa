"""Locate stories on printed IDML pages, including threads and anchored frames.

No story/table IDs or page numbers are special cases. Geometry is evaluated in
spread coordinates; touching a page boundary is retained conservatively.
"""
import xml.etree.ElementTree as ET

IDENTITY = (1, 0, 0, 1, 0, 0)


def transform(node):
    return tuple(map(float, node.get('ItemTransform', '1 0 0 1 0 0').split()))


def point(matrix, xy):
    a, b, c, d, tx, ty = matrix
    x, y = xy
    return a * x + c * y + tx, b * x + d * y + ty


def compose(parent, child):
    a, b, c, d, tx, ty = child
    x, y = point(parent, (tx, ty))
    pa, pb, pc, pd, _, _ = parent
    return pa*a + pc*b, pb*a + pd*b, pa*c + pc*d, pb*c + pd*d, x, y


def rectangle(points, matrix):
    coordinates = [point(matrix, p) for p in points]
    return (min(p[0] for p in coordinates), min(p[1] for p in coordinates),
            max(p[0] for p in coordinates), max(p[1] for p in coordinates))


def intersects(left, right):
    return left[0] <= right[2] and right[0] <= left[2] and left[1] <= right[3] and right[1] <= left[3]


def story_locations(archive, design):
    """Return printed placements and all spread pages for exclusion evidence.

    Threaded frames share ParentStory: any printed frame retains that story.
    Anchored frames use their enclosing story's placement, because their local
    coordinates are relative to text insertion, not to an absolute spread.
    Missing geometry raises rather than silently discarding possible print data.
    """
    stories = [ET.fromstring(archive.read(e.attrib['src']))[0] for e in design
               if e.tag.endswith('Story') and e.get('src')]
    printed, spreads = {}, {}
    for index, entry in enumerate(e for e in design
            if e.tag.endswith('Spread') and e.get('src', '').startswith('Spreads/')):
        spread = ET.fromstring(archive.read(entry.attrib['src']))
        pages, frames = [], []

        def walk(node, parent=IDENTITY):
            matrix = compose(parent, transform(node))
            if node.tag == 'Page':
                bounds = node.get('GeometricBounds')
                if not bounds:
                    raise ValueError('IDML sayfa geometrisi eksik; basılı tablo seçimi yapılamadı.')
                top, left, bottom, right = map(float, bounds.split())
                pages.append((node.get('Name', '?'), rectangle(
                    [(left, top), (right, top), (right, bottom), (left, bottom)], matrix)))
            elif node.tag == 'TextFrame' and node.get('ParentStory'):
                anchors = [tuple(map(float, p.attrib['Anchor'].split()))
                           for p in node.findall('./Properties//PathPointArray/PathPointType')]
                if not anchors:
                    raise ValueError('IDML metin çerçevesi geometrisi eksik: '
                                     + node.get('Self', node.get('ParentStory')))
                frames.append((node.get('ParentStory'), rectangle(anchors, matrix)))
            for child in node:
                walk(child, matrix)

        walk(spread)
        names = [name for name, _ in pages]
        for sid, bounds in frames:
            spreads.setdefault(sid, [])
            for name in names:
                if name not in spreads[sid]:
                    spreads[sid].append(name)
            for name, page in pages:
                if intersects(bounds, page):
                    printed.setdefault(sid, (index, name))
                    break

    anchors = [(story.get('Self'), frame.get('ParentStory')) for story in stories
               for frame in story.iter('TextFrame') if frame.get('ParentStory')]
    # A fixed point handles anchored stories nested to any depth; cycles without
    # a printed ancestor remain unplaced, and cannot manufacture a placement.
    changed = True
    while changed:
        changed = False
        for parent, child in anchors:
            if parent in printed and child not in printed:
                printed[child] = printed[parent]
                changed = True
            if parent in spreads and child not in spreads:
                spreads[child] = list(spreads[parent])
                changed = True
    return stories, printed, spreads
