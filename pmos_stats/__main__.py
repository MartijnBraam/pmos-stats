import glob
import subprocess
import os
import json
import pmos_stats.chart as chart


def init():
    if not os.path.isdir('pmbootstrap'):
        command = ['git', 'clone', 'git@github.com:postmarketOS/pmbootstrap.git']
        subprocess.run(command)


def get_commit_per_day(start_ref, end_ref):
    command = ['git', 'log', '--reverse', '--ancestry-path', '{}..{}'.format(start_ref, end_ref)]
    command.append("--pretty=format:'%h %cd'")
    command.append("--date=format:'%Y-%m-%d'")
    raw = subprocess.check_output(command, universal_newlines=True, cwd='pmbootstrap')
    result = []
    last_date = ''
    for line in raw.splitlines(keepends=False):
        c_hash, c_date = line.split(' ')
        if c_date != last_date:
            result.append((c_hash.replace("'", ''), c_date.replace("'", '')))
            last_date = c_date
    return result


def get_value(git_ref):
    command = ['git', 'checkout', git_ref]
    subprocess.check_output(command, cwd='pmbootstrap')
    if not os.path.isdir('pmbootstrap/aports'):
        return None
    if os.path.isdir('pmbootstrap/aports/device'):
        devices = len(glob.glob('pmbootstrap/aports/device/device-*'))
        kernels = len(glob.glob('pmbootstrap/aports/device/linux-*'))
        kernels += len(glob.glob('pmbootstrap/aports/main/linux-*'))
        return devices
    devices = len(glob.glob('pmbootstrap/aports/device-*'))
    return devices


def make_gnuplot(dataset):
    result = "#Day\tDevices\n"
    for line in dataset:
        result += '{} 00:00:00\t{}\n'.format(*line)
    return result


if __name__ == '__main__':
    init()

    initial_commit = 'bfde354b22ae4efd79d1036f79a9aeb1ff1927ce'
    commits = get_commit_per_day(initial_commit, 'master')
    dataset = []
    for commit in commits:
        value = get_value(commit[0])
        if value is not None:
            dataset.append((commit[1], value))
    result = make_gnuplot(dataset)
    with open('chart.dat', 'w') as handle:
        handle.write(result)

    c = chart.Chart(dataset)
    with open('chart.svg', 'w') as handle:
        handle.write(c.generate())

    with open('dataset.json', 'w') as handle:
        json.dump(dataset, handle)
