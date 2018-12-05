# Easy webrev generation/upload with [upload-webrev.py](upload-webrev.py)

Small script to generate webrevs or patches and to optionally upload them to a remote server via ssh. Needs python3.

It will generate the webrev or patch into a local export directory. It then will upload it via rsync to a remote
server.

```
usage: upload-webrev.py [-h] [-v] [-p] [-d] [-y] [-n NAME] [--overwrite-last]
                        [-u] [--openjdk-root DIRECTORY]
                        [--export-dir DIRECTORY]
                        [--webrev-script-location DIRECTORY]
                        [--upload-url URL]

Create a numbered webrev or a patch and optionally uploads it to a remote server using ssh.

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Debug output
  -p, --patch-mode      Patch mode (default: webrev mode). In patch mode a single unnumbered patch is generated
  -d, --delta           Delta mode: Produce a delta webrev in addition to the full webrev. Two outgoing changes are expected (base change + delta).
  -y                    Autoconfirm (use with care).
  -n NAME, --name NAME  Name of patch directory (when omitted, name is generated from the mercurial change description).
  --overwrite-last      [Webrev mode only]: Overwrite the last webrev ("webrev_<n>") instead of creating a new one ("webrev_<n+1>").
  -u, --upload          Upload to remote location (see --upload-url)
  --openjdk-root DIRECTORY
                        Openjdk base directory - base for export directory and webrev script location. Default: /shared/projects/openjdk
  --export-dir DIRECTORY
                        Patch export base directory. Default: <openjdk-root-dir>/export.
  --webrev-script-location DIRECTORY
                        Location of webrev script. Default: <openjdk-root-dir>/codetools/webrev/webrev.ksh.
  --upload-url URL      Remote upload url in the form <username>@<host>:<path>. Example: john_smith@cr.openjdk.java.net:my_webrevs

This tool knows two modes:
- Webrev Mode (default): a numbered webrev is created in the export directory. The generated webrevs are 
  numbered in ascending order.
- Patch Mode: Tool creates an (unnumbered) patch in the export directory.

Examples:

upload-webrev.py (no arguments)
  generates a numbered webrev from the outgoing change.

upload-webrev.py -vp
  generates a patch file from the outgoing change, verbose mode.

upload-webrev.py -u --upload-url thomas@cr.openjdk.java.net:my-webrevs
  generates a numbered webrev from the outgoing change and uploads it to cr.openjdk.java.net

upload-webrev.py -u --upload-url thomas@cr.openjdk.java.net:my-webrevs
  generates a numbered webrev from the outgoing change and uploads it to cr.openjdk.java.net

upload-webrev.py -d -u --overwrite-last --upload-url thomas@cr.openjdk.java.net:my-webrevs
  generates a numbered delta webrev (base webrev and delta) from two outgoing changes - overwriting the last one
  in the export directory - and uploads them both to cr.openjdk.java.net

```

## Basics

This tool knows two modes:
- Webrev Mode (the default): a webrev is generated into the export directory.
    - Webrevs are numbered (webrev_<n>, webrev_<n+1>). Each time the script is run a new webrev is created.
        - Exception: in "overwrite mode" `-o` or `--overwrite-last`, the highest-numbered webrev is overwritten instead 
    - Script expects exactly one outgoing change in the mercurial repository
    - "delta mode" (`-d` or `--delta`): two outgoing changes are expected, the first being the base change, the top
     one the delta change. Two webrevs are created from these, a delta webrev and a complete webrev.
- Patch Mode (`-p` resp. `--patch-mode`): Tool creates a simple patch in the export directory. Unlike webrevs, the patch is not numbered. This is usually faster than generating webrevs.

## Directory setup

The script needs a local export directory, by default located in the openjdk root directory. In addition, it
expects the webrev tool to be available locally.

This is the expected directory structure:


```
/shared/projects/openjdk
   |
   |-- codetools
   |     |
   |     |-- webrev
   |           |
   |           webrev.ksh
   |
   |-- export
         |
         |-- <patch directories are generated here>
          
```

The export directory is created on the fly if needed.

All directory locations can be overwritten via command line (`--openjdk-root`, `--export-dir`, `--webrev-script-location`). 

## Examples

Cd into the jdk repository. 

Commit or `hg qrefresh` all outstanding changes.


```
python3 upload-patch.py
```

  generates a numbered webrev from the outgoing change.

```
python3 upload-patch.py -vp
```

  generates a patch file from the outgoing change, verbose mode.

```
python3 upload-patch.py -u --upload-url thomas@cr.openjdk.java.net:my-webrevs
```

  generates a numbered webrev from the outgoing change and uploads it to cr.openjdk.java.net

```
python3 upload-patch.py -u --upload-url thomas@cr.openjdk.java.net:my-webrevs
```

  generates a numbered webrev from the outgoing change and uploads it to cr.openjdk.java.net

```
python3 upload-patch.py -d -u --overwrite-last --upload-url thomas@cr.openjdk.java.net:my-webrevs
```

  generates a numbered delta webrev (base webrev and delta) from two outgoing changes - overwriting the last one
  in the export directory - and uploads them both to cr.openjdk.java.net


