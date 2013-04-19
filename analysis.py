import numpy as np
import matplotlib.pyplot as plt
from clint.textui import progress, puts, indent
import yaml
import modal
import notesegmentation as ns


# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
cbr_analysis = True
glt_analysis = True
plot_results = False

# boundary is said to be correctly detected if it lies within this time
# duration of the reference value
match_time_ms = 100

sound_types = ['Non-Pitched Percussive',
               'Pitched Percussive',
               'Pitched Non-Percussive']

boundaries = ['onset',
              'sustain',
              'release',
              'offset',
              'partial_stability']

# ----------------------------------------------------------------------------


def deviations(detected, reference, transients):
    result = {'onset': int(np.abs(detected['onset'] -
                                  reference['onsets'][0])),
              'sustain': int(np.abs(detected['sustain'] -
                                    reference['sustains'][0])),
              'release': int(np.abs(detected['release'] -
                                    reference['releases'][0])),
              'offset': int(np.abs(detected['offset'] -
                                   reference['offsets'][0]))}

    if transients:
        result['partial_stability'] = int(np.abs(detected['sustain'] -
                                                 transients[0]['end']))
    else:
        result['partial_stability'] = 0

    return result


def avg_deviations(deviations):
    return {b: np.mean([deviations[f][b] for f in deviations])
            for b in boundaries}


def accuracy(match_time, deviations, samples):
    max_deviation = (44100.0 / 1000) * match_time
    result = {b: 0 for b in boundaries}

    for boundary in result:
        for sample in deviations:
            if deviations[sample][boundary] <= max_deviation:
                result[boundary] += 1
        result[boundary] = (float(result[boundary]) / len(samples)) * 100

    return result


def accuracy_by_sound_type(match_time, deviations, samples):
    max_deviation = (44100.0 / 1000) * match_time
    result = {t: {b: 0 for b in boundaries} for t in sound_types}
    sound_type_counts = {t: 0 for t in sound_types}

    for sample in deviations:
        sound_type = samples[sample]['type']
        for boundary in boundaries:
            if deviations[sample][boundary] <= max_deviation:
                result[sound_type][boundary] += 1
        sound_type_counts[sound_type] += 1

    for sound_type in result:
        for boundary in result[sound_type]:
            result[sound_type][boundary] = (
                float(result[sound_type][boundary]) /
                sound_type_counts[sound_type]
            ) * 100

    return result


# ----------------------------------------------------------------------------
# Analyse audio samples
# ----------------------------------------------------------------------------
print 'Analysing samples...'

samples = modal.db.samples(attribute_name='notes', attribute_value=1)

c_deviations = {}
glt_deviations = {}

if cbr_analysis or glt_analysis:
    for file in progress.bar(samples):
        audio = samples[file]['samples']
        transients = ns.partial_stability.get_transients(audio, samples[file])

        if cbr_analysis:
            try:
                note = ns.segmentation.cbr(audio, samples[file])[0]
                c_deviations[file] = deviations(note, samples[file],
                                                transients)
            except ns.segmentation.NoOnsetsFound:
                print 'Warning: ignoring %s (no onsets found)' % file

        if glt_analysis:
            try:
                note = ns.segmentation.rtsegmentation(audio, samples[file])[0]
                glt_deviations[file] = deviations(note, samples[file],
                                                  transients)
            except ns.segmentation.NoOnsetsFound:
                print 'Warning: ignoring %s (no onsets found)' % file

if cbr_analysis:
    with open('cbr_deviations.yaml', 'w') as f:
        f.write(yaml.dump(c_deviations))
else:
    with open('cbr_deviations.yaml', 'r') as f:
        c_deviations = yaml.load(f.read())

if glt_analysis:
    with open('glt_deviations.yaml', 'w') as f:
        f.write(yaml.dump(glt_deviations))
else:
    with open('glt_deviations.yaml', 'r') as f:
        glt_deviations = yaml.load(f.read())


# ----------------------------------------------------------------------------
# Calculate average deviations from reference values
# ----------------------------------------------------------------------------
print 'Calculating results...'

c_avg_deviations = avg_deviations(c_deviations)
glt_avg_deviations = avg_deviations(glt_deviations)

print
print 'Average deviation from reference values (in ms) for Caetano, Burred ',
print 'and Rodet method:'
with indent(4):
    for k, v in c_avg_deviations.iteritems():
        puts('{0}: {1:.2f}'.format(k, v / 44.1))

print
print 'Average deviation from reference values (in ms) for Glover, Lazzarini ',
print 'and Timoney method:'
with indent(4):
    for k, v in glt_avg_deviations.iteritems():
        puts('{0}: {1:.2f}'.format(k, v / 44.1))

# ----------------------------------------------------------------------------
# Calculate accuracy (%)
# ----------------------------------------------------------------------------

cbr_accuracy = accuracy(match_time_ms, c_deviations, samples)
glt_accuracy = accuracy(match_time_ms, glt_deviations, samples)

print
print 'Percentage within', match_time_ms, 'ms of reference samples for ',
print 'Caetano, Burred and Rodet method:'
with indent(4):
    for k, v in cbr_accuracy.iteritems():
        puts('{0}: {1:.2f}'.format(k, v))
print
print 'Percentage within', match_time_ms, 'ms of reference samples for ',
print 'Glover, Lazzarini and Timoney method:'
with indent(4):
    for k, v in glt_accuracy.iteritems():
        puts('{0}: {1:.2f}'.format(k, v))


# ----------------------------------------------------------------------------
# Calculate accuracy (%) by sound type
# ----------------------------------------------------------------------------

c_accuracy_by_sound_type = accuracy_by_sound_type(
    match_time_ms, c_deviations, samples)
glt_accuracy_by_sound_type = accuracy_by_sound_type(
    match_time_ms, glt_deviations, samples)

print
print 'Percentage within', match_time_ms, 'ms of reference samples for ',
print 'Caetano, Burred and Rodet method (by sound type):'
for sound_type in sound_types:
    with indent(4):
        puts('{0}:'.format(sound_type))
    for boundary in boundaries:
        with indent(8):
            puts('{0}: {1:.2f}'.format(
                boundary, c_accuracy_by_sound_type[sound_type][boundary]))

print
print 'Percentage within', match_time_ms, 'ms of reference samples for ',
print 'Glover, Lazzarini and Timoney method (by sound type):'
for sound_type in sound_types:
    with indent(4):
        puts('{0}:'.format(sound_type))
    for boundary in boundaries:
        with indent(8):
            puts('{0}: {1:.2f}'.format(
                boundary, glt_accuracy_by_sound_type[sound_type][boundary]))


# ----------------------------------------------------------------------------
# Plot results
# ----------------------------------------------------------------------------
if plot_results:
    fig = plt.figure(1, figsize=(12, 8))
    plt.title('Avg. Deviation From Reference Values (in samples)')
    ax = plt.axes()
    ax.autoscale(False, 'y')

    width = 0.4
    indexes = np.arange(len(c_avg_deviations))

    max_deviation = max([i for i in (c_avg_deviations.values() +
                                     glt_avg_deviations.values())])
    ax.set_ylim(0.0, max_deviation + (max_deviation * 0.1))

    c_bars = ax.bar(indexes, c_avg_deviations.values(), width, color='#9baca1')
    for bar in c_bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2.,
                height + 500,
                '%.1f' % height,
                ha='center',
                va='bottom')

    glt_bars = ax.bar(indexes + width, glt_avg_deviations.values(), width,
                      color='#81aac4', hatch='')
    for bar in glt_bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2.,
                height + 500,
                '%.1f' % height,
                ha='center',
                va='bottom')

    ax.set_ylabel('Deviation (in samples)')
    ax.set_xlabel('Segmentation boundary')
    ax.set_xticks(indexes + 0.4)
    ax.set_xticklabels(c_avg_deviations.keys())
    ax.legend((c_bars[0], glt_bars[0]),
              ('Caetano, Burred and Rodet', 'Glover, Lazzarini and Timoney'))
    plt.savefig('results.png')
