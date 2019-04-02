# !/usr/bin/env python3


import pathlib
import sys
import argparse
import subprocess
import shutil

# Default values, can be overridden via command line:

ojdk_root = '/shared/projects/openjdk'


def build_export_dir():
    return ojdk_root + '/export'


def build_webrev_script_location():
    return ojdk_root + '/code-tools/webrev/webrev.ksh'


export_dir = build_export_dir()

webrev_script_location = build_webrev_script_location()

upload_url = 'stuefe@cr.openjdk.java.net:webrevs'


def trc(text):
    print("--- " + text)


def verbose(text):
    if args.is_verbose:
        print("--- " + text)


def run_command_and_return_stdout(command):
    verbose('calling: ' + ' '.join(command))
    try:
        stdout = subprocess.check_output(command)
    except subprocess.CalledProcessError as e:
        trc('Command failed ' + ' '.join(command))
        print(e)
        sys.exit('Sorry :-(')
    stdout = stdout.decode("utf-8")
    verbose('out: ' + stdout)
    return stdout


def user_confirm(question):
    print(question + " [y/n]: ")
    if args.yesyes:
        print("(-y: auto-yes)")
        return
    answer = None
    while answer is None:
        answer = input().lower()
        if answer == "y":
            answer = True
        elif answer == "n":
            sys.exit('No -> Cancelling.')
        else:
            print("Please respond with \'y\' or \'n\'.")
            answer = None


def build_webrev_path(patch_export_dir, webrev_num):
    return patch_export_dir + '/webrev.' + '{:02d}'.format(webrev_num)


def build_delta_webrev_path(patch_export_dir, webrev_num):
    return patch_export_dir + '/webrev_delta.' + '{:02d}'.format(webrev_num)


def remove_directory(path: str):
    shutil.rmtree(path)
    trc("Removed directory: " + path)


def remove_prefix_from_string(s: str, prefix: str) -> str:
    if s.startswith(prefix):
        s = s[len(prefix):]
    return s


# Returns a list of [(int, str)] tuples containing the local revision number and description, respectively,
# of all outgoing changes. First one in the list is the oldest change, last one the youngest (tip).
def get_outgoing_changes() -> list:
    # Note: print revision number and first line of patch description. The latter is used as base for the
    # patch name unless a patch name is given via --patch-name.
    s = run_command_and_return_stdout(["hg", "outgoing", "-q", "-T", "{rev}###{desc|firstline|lower}\n"])
    lines = s.splitlines()
    return_list = []
    for line in lines:
        list_entry = line.split('###')

        revision_number = int(list_entry[0])
        description = list_entry[1]
        # correct patch names for some typical mq pattern:
        description = remove_prefix_from_string(description, 'imported patch ')
        description = remove_prefix_from_string(description, '[mq]: ')

        list_entry_tuple = (revision_number, description)
        return_list.append(list_entry_tuple)
    return return_list


# build up a patch name from a patch description text which may contain spaces, colons and so on.
# The returned name shall have no space.
def sanitize_patch_name(dirty_name: str) -> str:
    return dirty_name.replace(' ', '-').replace(':', '-')


parser = argparse.ArgumentParser(
    description='Create a numbered webrev or a patch and optionally uploads it to a remote server using ssh.',
    formatter_class=argparse.RawTextHelpFormatter,
    epilog=
    'This tool knows two modes:\n'
    '- Webrev Mode (default): a numbered webrev is created in the export directory. The generated webrevs are \n'
    '  numbered in ascending order.\n'
    '- Patch Mode: Tool creates an (unnumbered) patch in the export directory.\n'
    '\n'
    'Examples:\n'
    '\n'
    'upload-webrev.py (no arguments)\n'
    '  generates a numbered webrev from the outgoing change.\n'
    '\n'
    'upload-webrev.py -vp\n'
    '  generates a patch file from the outgoing change, verbose mode.\n'
    '\n'
    'upload-webrev.py -u --upload-url thomas@cr.openjdk.java.net:my-webrevs\n'
    '  generates a numbered webrev from the outgoing change and uploads it to cr.openjdk.java.net\n'
    '\n'
    'upload-webrev.py -u --upload-url thomas@cr.openjdk.java.net:my-webrevs\n'
    '  generates a numbered webrev from the outgoing change and uploads it to cr.openjdk.java.net\n'
    '\n'
    'upload-webrev.py -d -u --overwrite-last --upload-url thomas@cr.openjdk.java.net:my-webrevs\n'
    '  generates a numbered delta webrev (base webrev and delta) from two outgoing changes - overwriting the last one\n'
    '  in the export directory - and uploads them both to cr.openjdk.java.net\n'
)

# Optional args
# (Note: variable name seems to be the first encountered long (--) option name)
parser.add_argument("-v", "--verbose", dest="is_verbose", default=False,
                    help="Debug output", action="store_true")
parser.add_argument("-p", "--patch-mode", dest="patch_mode", default=False,
                    help="Patch mode (default: webrev mode). In patch mode a single unnumbered patch is generated",
                    action="store_true")
parser.add_argument("-d", "--delta", dest="delta_mode", default=False,
                    help="[Webrev mode]: Produce a delta webrev in addition to the full webrev. Two outgoing changes "
                         "are expected (base change + delta).",
                    action="store_true")

parser.add_argument("-y", dest="yesyes", default=False, help="Autoconfirm (use with care).", action="store_true")

parser.add_argument("--name", dest="patch_name", metavar="NAME",
                    help="Name of patch directory (when omitted, name is generated from the mercurial change "
                         "description).")

parser.add_argument("-o", "--overwrite-last", dest="overwrite_last_webrev", default=False,
                    help="[Webrev mode]: Overwrite the last webrev (\"webrev_<n>\") instead of creating a new one "
                         "(\"webrev_<n+1>\").",
                    action="store_true")

parser.add_argument("-n", "--number", dest="webrev_number", default=-1, type=int,
                    help="[Webrev mode]: Specify exactly the number of webrev to create. Will overwrite existing webrev of that number.")

parser.add_argument("-u", "--upload", dest="upload", default=False, help="Upload to remote location (see --upload-url)",
                    action="store_true")

parser.add_argument("--openjdk-root", dest="ojdk_root", default=ojdk_root, metavar="DIRECTORY",
                    help="Openjdk base directory - base for export directory and webrev script location. "
                         "Default: %(default)s")

parser.add_argument("--export-dir", dest="export_dir", metavar="DIRECTORY",
                    help="Patch export base directory. Default: <openjdk-root-dir>/export.")

parser.add_argument("--webrev-script-location", dest="webrev_script_location", metavar="DIRECTORY",
                    help="Location of webrev script. Default: <openjdk-root-dir>/codetools/webrev/webrev.ksh.")

parser.add_argument("--upload-url", dest="upload_url", metavar="URL",
                    help="Remote upload url in the form <username>@<host>:<path>. "
                         "Example: john_smith@cr.openjdk.java.net:my_webrevs")

args = parser.parse_args()
if args.is_verbose:
    trc(str(args))

ojdk_root = args.ojdk_root
export_dir = build_export_dir()
webrev_script_location = build_webrev_script_location()

if not pathlib.Path(ojdk_root).exists():
    sys.exit("OpenJDK root directory not found (" + ojdk_root + ")")

if args.webrev_script_location is not None:
    webrev_script_location = args.webrev_script_location

if not pathlib.Path(webrev_script_location).exists():
    sys.exit("webrev.ksh not found at " + webrev_script_location + ".")

if args.export_dir is not None:
    export_dir = args.export_dir
    if not pathlib.Path(export_dir).exists():
        # Let this be an error if the directory was specified manually.
        sys.exit("export directory not found at " + export_dir + ".")
else:
    if not pathlib.Path(export_dir).exists():
        # If export directory name is default, create it on the fly if needed
        verbose("Creating export directory " + export_dir + "..")
        pathlib.Path(export_dir).mkdir(parents=True, exist_ok=True)

if args.upload_url is not None:
    upload_url = args.upload_url

# upload-url must have the rsync form of: [USER@]HOST:DEST
if ":" not in upload_url:
    sys.exit("invalid upload url ([USER@]HOST:DEST expected)")

# ---

# sanity: some args only sense in webrev mode
if args.patch_mode:
    if args.overwrite_last_webrev:
        sys.exit("Option -o|--overwrite-last-webrev only supported in webrev mode.")
    if args.delta_mode:
        sys.exit("Option -d|--delta only supported in webrev mode.")
    if args.webrev_number != -1:
        sys.exit("Option -n|--number only supported in webrev mode.")

# check that all changes are qrefresh'ed
if run_command_and_return_stdout(['hg', 'diff']) != '':
    sys.exit('There are open changes in the workspace. Please commit/qrefresh first.')
else:
    verbose('No outstanding changes in workspace - OK.')

# Now find out the outgoing changes and put them into a list:
# [(revision, description), (revision, description), ...]
outgoing_changes = get_outgoing_changes()
if len(outgoing_changes) == 0:
    sys.exit("Found no outgoing changes. Not sure what you want from me?")
else:
    trc("Found {0} outgoing changes - oldest to youngest (tip):.".format(len(outgoing_changes)))
    print(outgoing_changes)


# Patch-Mode, Webrev-Mode: Need 1 outgoing change.
# Delta-Webrev-Mode: need 2 outgoing changes.
if args.patch_mode:
    if len(outgoing_changes) > 1:
        trc("Found multiple outgoing changes. Will only produce patch for the topmost one (" +
            outgoing_changes[-1][1] + ")")
else:
    if not args.delta_mode:
        if len(outgoing_changes) > 1:
            trc("Found multiple outgoing changes. Will produce webrev for the topmost one (" +
                outgoing_changes[-1][1] + ")")
    else:
        if len(outgoing_changes) != 2:
            sys.exit('We expect exactly two outgoing changes in delta webrev mode.')

# name of patch is generated from the first line of the mercurial change description of the outgoing change. In delta
# mode, from the first line of the mercurial change description of the base change.
# However, with option --patch-name the name can be overwritten from the command line.
patch_name = args.patch_name
if patch_name is None:
    patch_name = outgoing_changes[-1][1]
# Sanitize patch name
patch_name = sanitize_patch_name(patch_name)
trc("Patch name is " + patch_name)

patch_directory = export_dir + '/' + patch_name
pathlib.Path(patch_directory).mkdir(parents=True, exist_ok=True)

if args.patch_mode:

    # patch mode:
    # Produce new patch with hg export. Delete any pre-existing patches but ask
    # user first.
    patch_file_path = patch_directory + '/' + patch_name + '.patch'
    if pathlib.Path(patch_file_path).exists():
        user_confirm('Remove pre-existing patch: ' + patch_file_path)
        pathlib.Path(patch_file_path).unlink()
        trc("Removed pre-existing patch at " + patch_file_path + ".")
    run_command_and_return_stdout(["hg", "export", "-o", patch_file_path])
    trc("Created new patch at " + patch_file_path + " - OK.")

else:

    # webrev mode:
    # First, find existing highest-numbered webrev directory for this change
    # ( export/<patch name>/webrev_<iteration>)
    webrev_number_first_invalid = 0
    webrev_number_last_valid = -1
    while pathlib.Path(build_webrev_path(patch_directory, webrev_number_first_invalid)).exists():
        webrev_number_last_valid = webrev_number_first_invalid
        webrev_number_first_invalid += 1

    webrev_number = -1
    if args.overwrite_last_webrev and webrev_number_last_valid >= 0:
        webrev_number = webrev_number_last_valid
    else:
        webrev_number = webrev_number_first_invalid

    if args.webrev_number != -1:
        webrev_number = args.webrev_number

    webrev_dir_path = build_webrev_path(patch_directory, webrev_number)
    delta_webrev_dir_path = build_delta_webrev_path(patch_directory, webrev_number)

    # ask before overwriting
    if pathlib.Path(webrev_dir_path).exists():
        user_confirm('Remove pre-existing webrev directory: ' + webrev_dir_path)
        remove_directory(webrev_dir_path)
        # ... and also remove old webrev delta, should it exist
        # (we do not ask again, just do it)
        if pathlib.Path(delta_webrev_dir_path).exists():
            remove_directory(delta_webrev_dir_path)

    # Now create the new webrev:
    if not args.delta_mode:
        # In normal (non-delta) mode, we run webrev.ksh.
        if len(outgoing_changes) == 1:
            # if we have only one outgoing change, we just call webrev without revision
            run_command_and_return_stdout(["ksh", webrev_script_location, "-o", webrev_dir_path])

        else:
            # if there are more than one outgoing change, we only want a webrev for the latest one, so
            # we have to specify the revision with -r. Note however that webrev wants the *parent* revision
            run_command_and_return_stdout(["ksh", webrev_script_location, "-o", webrev_dir_path, "-r",
                                          str(outgoing_changes[-2][0])])
        trc("Created new webrev at " + webrev_dir_path + " - OK.")

    else:
        # In delta mode, we create two webrevs, one for the delta part, one for the full part.
        # (Note: to keep coding simple here I insist on exactly two outgoing changes, see above)
        if len(outgoing_changes) != 2:
            sys.exit("Expecting exactly two outgoing changes.")

        # Delta part: use -r <rev> where revision is the parent, which in this case is the base part.
        run_command_and_return_stdout(["ksh", webrev_script_location, "-o", delta_webrev_dir_path, "-r",
                                       str(outgoing_changes[0][0])])
        trc("Created new delta webrev at " + delta_webrev_dir_path + " - OK.")

        # Full part: just run webrev normally without specifying a revision. It will pick up all outgoing changes,
        # which are two (base + delta)
        run_command_and_return_stdout(["ksh", webrev_script_location, "-o", webrev_dir_path])
        trc("Created full webrev (base + delta) at " + webrev_dir_path + " - OK.")

# upload to remote: For simplicity, I just transfer the whole patch dir, regardless if that transfers
# older webrevs too. rsync will only transfer stuff not remote already.
if args.upload:
    trc("Uploading patch...")
    source = patch_directory
    result = run_command_and_return_stdout(["rsync", "-avz", "-e", "ssh", source, upload_url])
    trc("Did upload " + patch_directory + " to " + upload_url + " - OK.")
