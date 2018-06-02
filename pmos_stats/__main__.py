import glob
import subprocess
import os
import pmos_stats.chart as chart
import argparse
import re

cli = argparse.ArgumentParser(description="postmarketOS Stats generator")
subparsers = cli.add_subparsers(dest='subcommand')


def subcommand(args=None, parent=subparsers):
    args = args if args else []

    def decorator(func):
        name = func.__name__.replace('_', '-')
        parser = parent.add_parser(name, description=func.__doc__)
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
        parser.set_defaults(func=func)

    return decorator


def argument(*name_or_flags, **kwargs):
    return ([*name_or_flags], kwargs)


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


def get_devices_on_ref(ref):
    command = ['git', 'checkout', ref]
    subprocess.check_output(command, cwd='pmbootstrap')
    devices = glob.glob('pmbootstrap/aports/device/device-*')
    result = set()
    for device in devices:
        code = device.replace('pmbootstrap/aports/device/device-', '')
        result.add(code)
    return result


def get_device_name(code):
    infofile = 'pmbootstrap/aports/device/device-{}/deviceinfo'.format(code)
    with open(infofile) as handle:
        raw = handle.read()
    name = re.search(r'deviceinfo_name="([^"]+)"', raw)
    return name.group(1)


@subcommand([argument('filename', help="Output filename")])
def devices_over_time(args):
    init()

    initial_commit = 'bfde354b22ae4efd79d1036f79a9aeb1ff1927ce'
    commits = get_commit_per_day(initial_commit, 'master')
    dataset = []
    for commit in commits:
        value = get_value(commit[0])
        if value is not None:
            dataset.append((commit[1], value))

    c = chart.Chart(dataset)
    with open(args.filename, 'w') as handle:
        handle.write(c.generate())


@subcommand([argument('fromref', help='Oldest ref to check'),
             argument('--html', help='Create HTML table', action="store_true")])
def new_devices(args):
    init()
    a = get_devices_on_ref(args.fromref)
    b = get_devices_on_ref('master')

    added = b - a
    deleted = a - b

    if args.html:
        print('<table>')
        for device in sorted(added):
            name = get_device_name(device)
            print('<tr><td>{}</td><td>{}</td></tr>'.format(device, name))
        print('</table>')
        return

    print('--added--')
    for device in sorted(added):
        name = get_device_name(device)
        print("{} ({})".format(device, name))

    print('\n--deleted--')
    for device in sorted(deleted):
        print(device)


if __name__ == "__main__":
    args = cli.parse_args()
    if args.subcommand is None:
        cli.print_help()
    else:
        args.func(args)
