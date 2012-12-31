#!/usr/bin/env python

import cv2
import matplotlib.pyplot as plt
import numpy as np


class WatermarkRemover(object):

    OPACITY_RANGE = [10, 50]

    @classmethod
    def load_image(cls, path):
        return cls(cv2.imread(path))

    def __init__(self, image):
        self.arr = image
        self.opacity_bins = [0] * 256
        self.process()

    def process(self, window_size=(40, 40), step=(10, 10), show_rect=False, show_hist=True):
        assert step[0] < window_size[0] and step[1] < window_size[1]
        a = self.arr
        histograms = []
        row_starts = range(0, a.shape[0] - window_size[0], step[0])
        col_starts = range(0, a.shape[1] - window_size[1], step[1])
        for r in row_starts:
            for c in col_starts:
                win = a[r:r + window_size[0], c:c + window_size[1]]
                h = [cv2.calcHist([win], [ch], None, [256], [0, 255])[:, 0] for ch in range(3)]
                h = np.column_stack(h)
                histograms.append(h)

        h_index = 0
        for r in row_starts:
            for c in col_starts:
                if c:
                    self.test_levels(histograms[h_index - 1], histograms[h_index], show_hist=show_hist)
                if r:
                    self.test_levels(histograms[h_index - len(col_starts)], histograms[h_index], show_hist=False)
                if show_rect and (c or r):
                    canvas = np.copy(a)
                    cv2.rectangle(canvas, (c, r), (c + window_size[1], r + window_size[0]), (0, 0, 255))
                    cv2.imshow("Demo", canvas)
                    cv2.waitKey()
                h_index += 1

        print self.opacity_bins

    def test_levels(self, h1, h2, show_hist=False):
        d = h2 - h1
        orig_ss = np.sqrt(np.sum(d ** 2) / d.size)
        best_ss = orig_ss
        best_opacity = 0
        for opacity in range(self.OPACITY_RANGE[0], self.OPACITY_RANGE[1] + 1):
            alpha = opacity / 100.
            new_h2 = np.copy(h2)
            for n, hchans in enumerate(d):
                new_n = (n - alpha * 255) / (1 - alpha)
                if 0 <= new_n <= 255:
                    for c in range(3):
                        if 0 < hchans[c] and d[new_n, c] < 0:
                            new_h2[n, c] -= hchans[c]
                            new_h2[new_n, c] += hchans[c]
            new_d = new_h2 - h1
            ss = np.sqrt(np.sum(new_d ** 2) / new_d.size)
            if ss < best_ss:
                best_ss = ss
                best_opacity = opacity
                best_h2 = new_h2
                best_d = new_d

        if show_hist and best_opacity:
            print 'orig=%.2f, new=%.2f, opac=%d' % (orig_ss, best_ss, best_opacity)
            fig = plt.figure()
            # Will crash if pure black
            xmin = min(np.nonzero(h2)[0][0], np.nonzero(best_h2)[0][0])
            xmax = max(np.nonzero(h2)[0][-1], np.nonzero(best_h2)[0][-1])
            xs = range(int(xmin), int(xmax) + 1)
            ax = fig.add_subplot(2, 2, 1)
            ax.plot(xs, h2[xmin:xmax + 1, 0], 'b-', xs, h2[xmin:xmax + 1, 1], 'g-', xs, h2[xmin:xmax + 1, 2], 'r-')
            ax.grid(True)
            plt.xlabel('Base')

            ax = fig.add_subplot(2, 2, 3)
            ax.plot(xs, best_h2[xmin:xmax + 1, 0], 'b-', xs, best_h2[xmin:xmax + 1, 1], 'g-', xs, best_h2[xmin:xmax + 1, 2], 'r-')
            ax.grid(True)
            plt.xlabel('New')

            ax = fig.add_subplot(2, 2, 2)
            ax.plot(xs, d[xmin:xmax + 1, 0], 'b-', xs, d[xmin:xmax + 1, 1], 'g-', xs, d[xmin:xmax + 1, 2], 'r-')
            ax.grid(True)
            plt.xlabel('Base Diff')

            ax = fig.add_subplot(2, 2, 4)
            ax.plot(xs, best_d[xmin:xmax + 1, 0], 'b-', xs, best_d[xmin:xmax + 1, 1], 'g-', xs, best_d[xmin:xmax + 1, 2], 'r-')
            ax.grid(True)
            plt.xlabel('New Diff')

            plt.show()

        self.opacity_bins[best_opacity] += 1
        return best_opacity


if __name__ == '__main__':
    import sys
    WatermarkRemover.load_image(sys.argv[1])
