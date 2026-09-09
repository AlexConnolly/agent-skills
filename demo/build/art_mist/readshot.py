# What the mist actually did to the frame, measured rather than squinted at.
#
#   python readshot.py <dir> <tag>          measure and cut
#
# Reads <dir>/<tag>_mist.png and <dir>/<tag>_bare.png -- the same frame with
# the sheets shown and hidden -- and writes three things beside them:
#
#   <tag>_crop_*.png   1:1 cuts of the bands the sheets live in, so a 1600 px
#                      frame can be looked at without being scaled to 900
#   <tag>_diff.png     the lift the mist put on the frame, times eight, which
#                      is the only picture that shows what a 3 per cent change
#                      in a near-black image is doing
#   a table            per band: mean sRGB value with and without the mist, the
#                      lift, and the peak. ART-DIRECTION 2 caps everything cool
#                      at 0.42 luminance, so the peak column is a hard limit and
#                      not a matter of taste.
import os
import sys

import numpy as np
from PIL import Image

# (name, left%, top%, right%, bottom%) -- the bands the frame report says the
# sheets project into.
BANDS = [
    ('hollow', 0.66, 0.68, 1.00, 0.86),
    ('ditch', 0.36, 0.78, 1.00, 1.00),
    ('foreground', 0.20, 0.86, 1.00, 1.00),
    ('leftfield', 0.00, 0.68, 0.22, 0.82),
]


def load(path):
    return np.asarray(Image.open(path).convert('RGB'), dtype=np.float32) / 255.0


def lum(a):
    return a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722


def main():
    d, tag = sys.argv[1], sys.argv[2]
    mist = load(os.path.join(d, '%s_mist.png' % tag))
    bare = load(os.path.join(d, '%s_bare.png' % tag))
    h, w = mist.shape[:2]
    print('%s  %dx%d' % (tag, w, h))
    print('  %-12s %8s %8s %8s %8s %8s'
          % ('band', 'bare', 'mist', 'lift', 'peak', 'peak@'))
    for name, x0, y0, x1, y1 in BANDS:
        sl = (slice(int(y0 * h), int(y1 * h)), slice(int(x0 * w), int(x1 * w)))
        a, b = lum(bare[sl]), lum(mist[sl])
        i = int(np.argmax(b))
        py, px = divmod(i, b.shape[1])
        print('  %-12s %8.4f %8.4f %+8.4f %8.4f  %3d%%,%3d%%'
              % (name, a.mean(), b.mean(), b.mean() - a.mean(), b.max(),
                 int(100 * (sl[1].start + px) / w),
                 int(100 * (sl[0].start + py) / h)))
        Image.fromarray((mist[sl] * 255).astype(np.uint8)).save(
            os.path.join(d, '%s_crop_%s.png' % (tag, name)))
        # A levels stretch of the same cut. It lies about the density on
        # purpose and it is the only way to judge the SHAPE of something whose
        # whole range is 0.05 to 0.14 -- the numbers above are what to quote.
        cut = mist[sl]
        lo, hi = np.percentile(cut, 0.5), np.percentile(cut, 99.8)
        st = np.clip((cut - lo) / max(1e-6, hi - lo), 0, 1)
        Image.fromarray((st * 255).astype(np.uint8)).save(
            os.path.join(d, '%s_stretch_%s.png' % (tag, name)))

    # Where did the mist ACTUALLY change the frame? Fixed percentage bands go
    # stale the moment an instance moves, and a band that is mostly empty
    # ground reports a mean lift of +0.000 for a sheet that is perfectly
    # visible inside it. This finds the changed pixels and describes them.
    dl = lum(mist) - lum(bare)
    m = dl > (1.0 / 255.0)
    if m.any():
        ys, xs = np.nonzero(m)
        sel = dl[m]
        print('  MIST FOOTPRINT  %d px (%.2f%% of frame)  x %d..%d%%  '
              'y %d..%d%%' % (m.sum(), 100.0 * m.sum() / m.size,
                              100 * xs.min() // w, 100 * xs.max() // w,
                              100 * ys.min() // h, 100 * ys.max() // h))
        print('  lift inside it   mean %+.4f  median %+.4f  max %+.4f'
              % (sel.mean(), float(np.median(sel)), sel.max()))
        print('  value inside it  bare %.4f -> mist %.4f  (brightest mist '
              'pixel %.4f)' % (lum(bare)[m].mean(), lum(mist)[m].mean(),
                               lum(mist)[m].max()))
    else:
        print('  MIST FOOTPRINT  NOTHING CHANGED - the sheets are not in shot')

    diff = np.clip((mist - bare) * 8.0, 0, 1)
    Image.fromarray((diff * 255).astype(np.uint8)).save(
        os.path.join(d, '%s_diff.png' % tag))
    print('  whole frame peak with mist %.4f  (ART-DIRECTION 2 caps cool at '
          '0.42)' % lum(mist).max())
    print('  wrote %s_diff.png and %d crops' % (tag, len(BANDS)))


if __name__ == '__main__':
    main()
