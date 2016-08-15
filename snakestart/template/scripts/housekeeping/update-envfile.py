import re, os, site, yaml, subprocess, argparse
from fnmatch import fnmatch

def parse(hfile):
    """
    parse the history file and return a list of
    tuples(datetime strings, set of distributions/diffs, comments)
    """
    hfile_data = []
    sep_pat = re.compile(r'==>\s*(.+?)\s*<==')
    with open(hfile) as f:
        lines = f.read().splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        m = sep_pat.match(line)
        if m:
            hfile_data.append((m.group(1), set(), []))
        elif line.startswith('#'):
            hfile_data[-1][2].append(line)
        else:
            hfile_data[-1][1].add(line)
    return hfile_data

def req2glob_tup(req_str):
    """turn user request string into tuple(package, version no. glob pattern)"""
    try:
        tup = ( req_str.split()[0], req_str.split()[1] )
    except IndexError:
        tup = ( req_str, '*' )
    return tup

def envyml2glob_tup(envyml_str):
    """turn environment.yml package string into tuple(package, version no. glob pattern)"""
    try:
        tup = ( envyml_str.split('=')[0], envyml_str.split('=')[1] + '*' )
    except IndexError:
        tup = ( envyml_str, '*' )
    return tup

def pkg_list2pkg_tup(pkg_list): 
    try:
        tup = ( pkg_list[0], pkg_list[1], pkg_list[2], pkg_list[3] )
    except IndexError:
        tup = ( pkg_list[0], pkg_list[1], pkg_list[2], '' )
    return tup
    

def get_user_requests(hfile_data):
    '''
    return tuple(user requested package installs, user requested package removals)
    each of these is a set containing package glob tuples as elements
    '''
    install = set()
    remove = set()
    spec_pat = re.compile(r'#\s*(\w+)\s*specs:\s*(.+)')
    for unused_dt, unused_cont, comments in hfile_data:
        for line in comments:
            m = spec_pat.match(line)
            if m:
                action, specs = m.groups()
                if action == 'install':
                    l = [ req2glob_tup(req) for req in eval(specs)[:-1] ]
                    install |= set(l)
                if action == 'remove':
                    l = [ req2glob_tup(req) for req in eval(specs)[:-1] ]
                    remove |= set(l)
    return (install, remove)

def get_installed_pkgs():
    '''
    run `conda list` in a shell and return output
    parsed into list of package tuples
    '''
    conda_list = subprocess.Popen("conda list", shell=True, stdout=subprocess.PIPE).stdout.read()
    installed_pkgs = [ pkg_list2pkg_tup(p.split()) for p in str(conda_list).split('\\n')[2:-1]]  
    return installed_pkgs  

def get_user_pkgs(install_list, installed_pkgs):
    '''
    return set of package tuples in installed_pkgs that match
    package glob tuples in install_list
    '''
    pkg_set = set()
    for req in install_list:
        pkg_set |= { p for p in installed_pkgs if (p[0] == req[0] and fnmatch(p[1],req[1])) }
    return pkg_set

def is_pip(pkg):
    if pkg[2] == '<pip>':
        return True
    else:
        return False

def get_pip_pkgs(installed_pkgs):
    '''returns set of pip installed packages'''
    pkg_set = { pkg for pkg in installed_pkgs if is_pip(pkg) }
    return pkg_set

def get_installed_chnls(installed_pkgs):
    '''returns set of channels present in set of installed packages'''
    return { p[3] for p in installed_pkgs if p[3] }

def pkg_str(pkg_tup, level=1):
    '''
    returns a string defining the package from pkg_tup
    in envirnoment.yml format with desired level of detail
    '''
    if level == 1:
        if pkg_tup[0] == 'python':
            return 'python=3'
        else:
            return pkg_tup[0]
    elif level == 2:
        return '='.join(pkg_tup[0:2])
    elif level == 3:
        return '='.join(pkg_tup[0:3])



parser = argparse.ArgumentParser(description='Update envirnoment.yml based on installed packages')
parser.add_argument('-e', '--exactpackages', action='store_true',
                    help='output version numbers in outfile')
parser.add_argument('infile', type=argparse.FileType('r'),
                    help='enivronment file to update')
args = parser.parse_args()

hfile = os.path.join( site.PREFIXES[0], 'conda-meta', 'history')
hfile_data = parse(hfile)
yfile_data = yaml.load(args.infile)

if args.exactpackages:
    lvl = 2
else:
    lvl = 1

user_install_list, user_remove_list = get_user_requests(hfile_data)
user_install_list |= { envyml2glob_tup(p) for p in yfile_data['dependencies'] }

installed = get_installed_pkgs()

user_pkgs  = get_user_pkgs(user_install_list, installed)
pip_pkgs   = get_pip_pkgs(installed)
user_chnls = set(yfile_data['channels']) | get_installed_chnls(installed)


if pip_pkgs:
    outyml = {
        'channels': list(user_chnls),
        'dependencies': 
            [ pkg_str(p,level=lvl) for p in user_pkgs ] + 
            [{'pip': [ pkg_str(p,level=lvl) for p in pip_pkgs ] }],
    }
else:
    outyml = {
        'channels': list(user_chnls),
        'dependencies': [ pkg_str(p,level=lvl) for p in user_pkgs ],
    }

print(yaml.dump(outyml, default_flow_style=False))