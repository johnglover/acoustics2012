import numpy as np
import matplotlib.pyplot as plt
import modal
import notesegmentation as ns

sample = modal.db.samples("clarinet-C-octave0.wav")
audio = sample['samples']
metadata = sample

fig = plt.figure(1, figsize=(14, 9))
plt.plot(np.abs(audio), '0.4')

g = ns.segmentation.glt(audio, metadata)
for note in g:
    for boundary_name, boundary in note.iteritems():
        plt.axvline(boundary, c='r', linestyle='--')
        print "Boundary (%s): %d" % (boundary_name, boundary)

plt.show()
