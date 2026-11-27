#!/usr/bin/env python3
"""Check which video tools are installed. Read-only: installs nothing, changes nothing.

Usage:
  python doctor.py                  a table of every tool, with advice for anything not ready
  python doctor.py --plan KEY ...   one tab-separated line per tool, read by the installers

This file is the only place the tool rules live. install/install.sh and install/install.ps1
ask it what to do and only install what it reports as missing. Minimum versions are in
min_versions.txt next to this file.

Keys: ffmpeg python node uv blender ytdlp git

--plan line format (tab-separated, "-" for an empty field):
  KEY  STATE  ESSENTIAL  INSTALL  DETAIL  ADVICE
  STATE is ok | missing | too_old | incomplete | not_on_path
  INSTALL is "brew PACKAGES", "apt PACKAGES", "winget ID" or "manual TEXT" (for a missing tool)
"""
import glob
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
IS_WIN = os.name == "nt"
IS_MAC = sys.platform == "darwin"
HOME = str(Path.home())


def load_min_versions():
    values = {"NODE_MIN": "22", "PYTHON_MIN": "3.9"}
    try:
        for line in (HERE / "min_versions.txt").read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    except OSError:
        pass
    return int(values["NODE_MIN"]), tuple(int(x) for x in values["PYTHON_MIN"].split("."))


NODE_MIN, PYTHON_MIN = load_min_versions()
PYTHON_MIN_TEXT = ".".join(str(x) for x in PYTHON_MIN)

# The one tool table. Package columns: None means that package manager has no suitable package.
TOOLS = {
    "ffmpeg": {"label": "FFmpeg", "essential": True, "purpose": "cuts, renders, audio, captions",
               "brew": "ffmpeg", "apt": "ffmpeg", "winget": "Gyan.FFmpeg"},
    "python": {"label": "Python", "essential": True, "purpose": "runs the bundled scripts",
               "brew": "python", "apt": "python3 python3-venv python3-pip", "winget": "Python.Python.3.12"},
    "node": {"label": "Node.js", "essential": False, "purpose": "HyperFrames graphics",
             "brew": "node", "apt": None, "winget": "OpenJS.NodeJS.LTS"},
    "uv": {"label": "uv", "essential": False, "purpose": "runs the ElevenLabs connector",
           "brew": "uv", "apt": None, "winget": "astral-sh.uv"},
    "blender": {"label": "Blender", "essential": False, "purpose": "3D diagrams",
                "brew": "--cask blender", "apt": "blender", "winget": "BlenderFoundation.Blender"},
    "ytdlp": {"label": "yt-dlp", "essential": False, "purpose": "licensed outside clips",
              "brew": "yt-dlp", "apt": "yt-dlp", "winget": "yt-dlp.yt-dlp"},
    "git": {"label": "git", "essential": False, "purpose": "sharing and updating this skill",
            "brew": "git", "apt": "git", "winget": "Git.Git"},
}

NO_PACKAGE = {
    ("apt", "node"): f"Node.js {NODE_MIN}+ is needed and the apt version is often older. Install it with a "
                     "version manager such as NVM (https://github.com/nvm-sh/nvm), or see https://nodejs.org/en/download",
    ("apt", "uv"): "see https://docs.astral.sh/uv/getting-started/installation/",
}

OK, MISSING, TOO_OLD, INCOMPLETE, NOT_ON_PATH = "ok", "missing", "too_old", "incomplete", "not_on_path"
LABELS = {OK: "ok", MISSING: "missing", TOO_OLD: "too old", INCOMPLETE: "incomplete", NOT_ON_PATH: "not on PATH"}
# On Windows a tool is either a program or a launcher script: npx is npx.cmd, and pyenv-win's
# python is python.bat. Tried in the order Windows itself uses.
SUFFIXES = (".com", ".exe", ".bat", ".cmd") if IS_WIN else ("",)


class Result:
    def __init__(self, state, detail, advice="", manual=""):
        self.state = state      # one of the states above
        self.detail = detail    # what was found
        self.advice = advice    # what the user should do; for an ok tool, a note worth reading
        self.manual = manual    # for a missing tool: install it this way, never with a package manager


def run(args, timeout=30):
    """(exit code, output) or (None, "") if it would not start. Used only for version checks."""
    try:
        res = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                             timeout=timeout, encoding="utf-8", errors="replace")
        return res.returncode, res.stdout or ""
    except (OSError, subprocess.SubprocessError):
        return None, ""


# ---- Finding executables -------------------------------------------------------------------

def extra_dirs():
    """Folders where tools often live without being on PATH in every shell."""
    env = os.environ.get
    if IS_WIN:
        local, prog = env("LOCALAPPDATA", ""), env("ProgramFiles", r"C:\Program Files")
        dirs = [os.path.join(local, "Microsoft", "WinGet", "Links"), os.path.join(HOME, ".local", "bin"),
                os.path.join(HOME, "scoop", "shims"), os.path.join(prog, "nodejs"),
                os.path.join(prog, "Git", "cmd"), os.path.join(env("VOLTA_HOME") or os.path.join(local, "Volta"), "bin")]
        dirs += sorted(glob.glob(os.path.join(local, "Programs", "Python", "Python3*")), reverse=True)
        for conda in ("miniconda3", "anaconda3", "miniforge3"):
            dirs += [os.path.join(HOME, conda), os.path.join(HOME, conda, "Scripts")]
        return dirs
    data = env("XDG_DATA_HOME") or HOME + "/.local/share"
    dirs = [HOME + "/.local/bin", HOME + "/.cargo/bin", (env("PYENV_ROOT") or HOME + "/.pyenv") + "/shims",
            (env("ASDF_DATA_DIR") or HOME + "/.asdf") + "/shims", (env("MISE_DATA_DIR") or data + "/mise") + "/shims",
            (env("VOLTA_HOME") or HOME + "/.volta") + "/bin", HOME + "/bin",
            "/opt/homebrew/bin", "/usr/local/bin", "/home/linuxbrew/.linuxbrew/bin", "/snap/bin"]
    for conda in ("miniconda3", "anaconda3", "miniforge3", "mambaforge"):
        dirs.append(f"{HOME}/{conda}/bin")
    dirs += sorted(glob.glob(HOME + "/Library/Python/3.*/bin"), reverse=True)  # pip --user on a Mac
    return dirs


_command_line_tools = None


def is_stub(path):
    """True for placeholders that are not real tools and may open an installer if run:
    the Microsoft Store python on Windows, and Apple's python3 and git when the
    Command Line Tools are not installed. Checking never runs the placeholder."""
    global _command_line_tools
    if IS_WIN:
        return "\\windowsapps\\" in path.lower() and os.path.basename(path).lower().startswith("python")
    if not IS_MAC or path not in ("/usr/bin/python3", "/usr/bin/git"):
        return False
    if _command_line_tools is None:
        code, _ = run(["xcode-select", "-p"], timeout=10)
        _command_line_tools = code == 0
    return not _command_line_tools


def find(cmd):
    """(path, on_path) for a real copy of cmd, searching PATH first, then extra_dirs()."""
    on_path = [d for d in os.environ.get("PATH", "").split(os.pathsep) if d]
    seen = {os.path.normcase(d) for d in on_path}
    dirs = on_path + [d for d in extra_dirs() if os.path.normcase(d) not in seen]
    for i, folder in enumerate(dirs):
        for suffix in SUFFIXES:
            candidate = os.path.join(folder, cmd + suffix)
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK) and not is_stub(candidate):
                return candidate, i < len(on_path)
    return None, False


def beside(path, name):
    """Is there a tool called name in the same folder as path?"""
    return any(os.path.isfile(os.path.join(os.path.dirname(path), name + suffix)) for suffix in SUFFIXES)


def path_advice(path):
    return (f"Open a new terminal. If it is still not found, add {os.path.dirname(path)} to PATH. "
            "It was not installed again.")


def major_version(path):
    code, out = run([path, "--version"])
    m = re.search(r"(\d+)\.", out)
    return int(m.group(1)) if code == 0 and m else 0


def python_version(path, pre=()):
    # No percent signs: a .bat launcher (pyenv-win) would have cmd.exe read them as variables.
    code, out = run([path, *pre, "-c", "import sys; print('.'.join(map(str, sys.version_info[:3])))"])
    m = re.match(r"(\d+)\.(\d+)\.(\d+)", out.strip())
    return tuple(int(x) for x in m.groups()) if code == 0 and m else None


def dotted(version):
    return ".".join(str(x) for x in version)


# ---- Package managers (read-only checks) ---------------------------------------------------

def brew_path():
    found = shutil.which("brew")
    if found:
        return found
    for candidate in ("/opt/homebrew/bin/brew", "/usr/local/bin/brew", "/home/linuxbrew/.linuxbrew/bin/brew"):
        if os.access(candidate, os.X_OK):
            return candidate
    return None


def package_manager():
    if IS_WIN:
        return "winget" if shutil.which("winget") else None
    if brew_path():
        return "brew"
    if shutil.which("apt-get") and shutil.which("dpkg-query"):
        return "apt"
    return None


def package_installed(manager, package):
    """Is the package already installed by this package manager? Looks only; never asks it to change."""
    if manager == "brew":
        prefix = Path(brew_path()).resolve().parent.parent
        name = package.split()[-1]
        if package.startswith("--cask"):
            return (prefix / "Caskroom" / name).exists()
        return (prefix / "opt" / name).exists() or bool(glob.glob(str(prefix / "opt" / (name + "@*"))))
    if manager == "apt":
        # "ii" = installed. A removed package that left its config files behind shows "rc".
        code, out = run(["dpkg-query", "-W", "-f=${db:Status-Abbrev}", package.split()[0]])
        return code == 0 and out.startswith("ii")
    if manager == "winget":
        code, _ = run(["winget", "list", "--id", package, "-e", "--disable-interactivity",
                       "--accept-source-agreements"], timeout=90)
        return code == 0
    return False


# ---- Node version managers -----------------------------------------------------------------

def node_managers():
    """Node version managers present on this computer, whether or not they are loaded in this shell.
    Each is (name, root folder, glob for its node binaries, install command, make-default command or None)."""
    env, n = os.environ.get, NODE_MIN
    if IS_WIN:
        local, roaming = env("LOCALAPPDATA", ""), env("APPDATA", "")
        found = [("nvm-windows", env("NVM_HOME") or os.path.join(roaming, "nvm"), "v*/node.exe",
                  f"nvm install {n}", f"nvm use {n}"),
                 ("fnm", env("FNM_DIR") or os.path.join(roaming, "fnm"), "node-versions/v*/installation/node.exe",
                  f"fnm install {n}", f"fnm default {n}"),
                 ("Volta", env("VOLTA_HOME") or os.path.join(local, "Volta"), "tools/image/node/*/node.exe",
                  f"volta install node@{n}", f"volta install node@{n}")]
    else:
        data = env("XDG_DATA_HOME") or HOME + "/.local/share"
        fnm = ("node-versions/v*/installation/bin/node", f"fnm install {n}", f"fnm default {n}")
        found = [("NVM", env("NVM_DIR") or HOME + "/.nvm", "versions/node/v*/bin/node",
                  f"nvm install {n}", f"nvm alias default {n}"),
                 ("fnm", env("FNM_DIR") or data + "/fnm") + fnm,
                 ("fnm", HOME + "/Library/Application Support/fnm") + fnm,
                 ("fnm", HOME + "/.fnm") + fnm,
                 ("mise", env("MISE_DATA_DIR") or data + "/mise", "installs/node/*/bin/node",
                  f"mise use -g node@{n}", f"mise use -g node@{n}"),
                 ("asdf", env("ASDF_DATA_DIR") or HOME + "/.asdf", "installs/nodejs/*/bin/node",
                  f"asdf install nodejs latest:{n}", None),
                 ("Volta", env("VOLTA_HOME") or HOME + "/.volta", "tools/image/node/*/bin/node",
                  f"volta install node@{n}", f"volta install node@{n}"),
                 ("n", (env("N_PREFIX") or "/usr/local") + "/n", "versions/node/*/bin/node", f"n {n}", f"n {n}")]
    present, roots = [], set()
    for manager in found:
        if os.path.isdir(manager[1]) and manager[1] not in roots:
            roots.add(manager[1])
            present.append(manager)
    return present


def install_steps(m):
    """What to type to install Node with manager m and make it the default."""
    if m[4] is None:
        return f"'{m[3]}', then make that version your default with {m[0]}"
    return f"'{m[3]}'" if m[3] == m[4] else f"'{m[3]}', then '{m[4]}'"


def default_step(m):
    return f"make it your default with {m[0]}" if m[4] is None else f"run '{m[4]}'"


def newest_managed_node(managers):
    """(major, path, manager) of the newest Node any version manager holds. Reads folder names only."""
    best = (0, None, None)
    for manager in managers:
        for path in glob.glob(os.path.join(manager[1], manager[2])):
            m = re.search(r"[\\/]v?(\d+)\.\d+\.\d+[\\/]", path)
            if m and int(m.group(1)) > best[0]:
                best = (int(m.group(1)), path, manager)
    return best


# ---- Checks, one per tool ------------------------------------------------------------------

def check_ffmpeg():
    path, on_path = find("ffmpeg")
    if not path:
        return Result(MISSING, "not found")
    if not on_path:
        return Result(NOT_ON_PATH, f"ffmpeg at {path}, which is not on PATH in this shell", path_advice(path))
    if not beside(path, "ffprobe") and not find("ffprobe")[0]:
        return Result(INCOMPLETE, f"ffmpeg ({path}) is installed but ffprobe is missing",
                      "Reinstall FFmpeg the way you installed it, choosing a full build that includes ffprobe.")
    _, filters = run([path, "-hide_banner", "-filters"])
    if not re.search(r"^\s*\S+\s+subtitles\s", filters, re.M):
        return Result(OK, f"ffmpeg ({path})", "This FFmpeg has no 'subtitles' filter (built without libass). "
                      "Everything works except burned-in captions. For those, switch to a full FFmpeg build "
                      "the way you installed it.")
    return Result(OK, f"ffmpeg ({path})")


def check_python():
    if IS_WIN:
        names = [("python", ()), ("python3", ()), ("py", ("-3",))]
    else:
        names = [("python3", ()), ("python", ())] + [(f"python3.{minor}", ()) for minor in range(14, PYTHON_MIN[1] - 1, -1)]
    old = off_path = None
    for name, pre in names:
        path, on_path = find(name)
        version = python_version(path, pre) if path else None
        if not version:
            continue
        if version >= PYTHON_MIN:
            if on_path:
                return Result(OK, f"Python {dotted(version)} ({path})")
            off_path = off_path or (version, path)
        else:
            old = old or (version, path)
    if off_path:
        return Result(NOT_ON_PATH, f"Python {dotted(off_path[0])} at {off_path[1]}, which is not on PATH in this shell",
                      path_advice(off_path[1]) + " If it belongs to conda or pyenv, activate that environment first.")
    if old:
        if os.path.isdir(os.environ.get("PYENV_ROOT") or HOME + "/.pyenv"):
            advice = "You use pyenv: run 'pyenv install 3.12' then 'pyenv global 3.12'."
        else:
            advice = "Upgrade Python the way you installed it. A second Python was not installed, to avoid clashes."
        return Result(TOO_OLD, f"{old[1]} is Python {dotted(old[0])}; the scripts need {PYTHON_MIN_TEXT} or newer", advice)
    return Result(MISSING, "not found")


def check_node():
    managers = node_managers()
    best_major, best_path, best_manager = newest_managed_node(managers)
    no_clash = "Node was not installed another way, to avoid clashes."
    path, on_path = find("node")
    if path and on_path:
        major = major_version(path)
        if major >= NODE_MIN:
            return Result(OK, f"Node {major} ({path})")
        detail = f"Node {major} at {path} is older than {NODE_MIN}"
        if best_major >= NODE_MIN:
            return Result(TOO_OLD, detail, f"{best_manager[0]} already has Node {best_major}: "
                          f"{default_step(best_manager)} and open a new terminal. {no_clash}")
        if managers:
            m = managers[0]
            return Result(TOO_OLD, detail, f"You use {m[0]}: run {install_steps(m)}. {no_clash}")
        return Result(TOO_OLD, detail, f"Upgrade Node the way you installed it. {no_clash}")
    if best_major >= NODE_MIN:
        return Result(NOT_ON_PATH, f"Node {best_major} from {best_manager[0]} ({best_path}) is not active in this shell",
                      f"In your usual terminal 'node --version' should show it. If not, "
                      f"{default_step(best_manager)} and open a new terminal.")
    if path:
        major = major_version(path)
        if major >= NODE_MIN:
            return Result(NOT_ON_PATH, f"Node {major} at {path}, which is not on PATH in this shell", path_advice(path))
        return Result(TOO_OLD, f"Node {major} at {path} is older than {NODE_MIN}",
                      f"Upgrade Node the way you installed it. {no_clash}")
    if best_path:
        m = best_manager
        return Result(TOO_OLD, f"{m[0]} has Node {best_major}, older than {NODE_MIN}",
                      f"Run {install_steps(m)}. {no_clash}")
    if managers:
        m = managers[0]
        return Result(MISSING, f"{m[0]} is installed but has no Node yet",
                      manual=f"Install Node with {m[0]}: {install_steps(m)}. "
                             "It is not installed with a package manager, to avoid two copies of Node.")
    return Result(MISSING, "not found")


def check_uv():
    path, on_path = find("uv")
    if path:
        if not beside(path, "uvx"):
            return Result(INCOMPLETE, f"uv at {path} has no uvx beside it, so it is too old for the ElevenLabs connector",
                          "Update uv the way you installed it: 'uv self update' for the standalone installer, "
                          "'brew upgrade uv' for Homebrew, 'pipx upgrade uv' for pipx.")
        if not on_path:
            return Result(NOT_ON_PATH, f"uv at {path}, which is not on PATH in this shell", path_advice(path))
        return Result(OK, f"uv and uvx ({path})")
    uvx, _ = find("uvx")
    if uvx:
        return Result(INCOMPLETE, f"uvx found at {uvx} but uv is missing",
                      "Reinstall uv the way you installed uvx. It was not installed again, to avoid a second copy.")
    return Result(MISSING, "not found")


def check_ytdlp():
    path, on_path = find("yt-dlp")
    if path:
        if not on_path:
            return Result(NOT_ON_PATH, f"yt-dlp at {path}, which is not on PATH in this shell", path_advice(path))
        return Result(OK, f"yt-dlp ({path})")
    pythons = [sys.executable] + [p for p in (find("python3")[0], find("python")[0]) if p]
    for python in dict.fromkeys(pythons):
        code, _ = run([python, "-m", "yt_dlp", "--version"])
        if code == 0:
            return Result(OK, f"yt-dlp as a Python module (run it as: {python} -m yt_dlp)")
    return Result(MISSING, "not found")


def check_blender():
    path, on_path = find("blender")
    if path:
        if not on_path:
            return Result(NOT_ON_PATH, f"Blender at {path}, which is not on PATH in this shell", path_advice(path))
        return Result(OK, f"Blender ({path})")
    if IS_MAC:
        apps = ["/Applications/Blender.app/Contents/MacOS/Blender", HOME + "/Applications/Blender.app/Contents/MacOS/Blender"]
    elif IS_WIN:
        apps = sorted(glob.glob(os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"),
                                             "Blender Foundation", "*", "blender.exe")), reverse=True)
    else:
        apps = []
    for app in apps:
        if os.access(app, os.X_OK):
            return Result(OK, f"Blender app ({app})", "Blender is not on PATH; call it by this full path.")
    return Result(MISSING, "not found")


def check_git():
    path, on_path = find("git")
    if not path:
        return Result(MISSING, "not found")
    code, _ = run([path, "--version"])
    if code != 0:
        return Result(INCOMPLETE, f"git at {path} does not run", "Reinstall git the way you installed it.")
    if not on_path:
        return Result(NOT_ON_PATH, f"git at {path}, which is not on PATH in this shell", path_advice(path))
    return Result(OK, f"git ({path})")


CHECKS = {"ffmpeg": check_ffmpeg, "python": check_python, "node": check_node, "uv": check_uv,
          "blender": check_blender, "ytdlp": check_ytdlp, "git": check_git}


def check(key):
    """Check one tool, then, if it looks missing, whether the package manager already has it."""
    result = CHECKS[key]()
    if result.state == MISSING and not result.manual:
        manager = package_manager()
        package = TOOLS[key].get(manager) if manager else None
        if package and package_installed(manager, package):
            hint = " (Homebrew: 'brew link " + package.split()[-1] + "')" if manager == "brew" else ""
            return Result(NOT_ON_PATH, f"{TOOLS[key]['label']} is already installed by {manager} but is not on PATH",
                          f"Open a new terminal. If it is still not found, fix PATH{hint}. It was not installed again.")
    return result


def install_for(key, result):
    """How the installers should install a missing tool."""
    if result.manual:
        return "manual " + result.manual
    manager = package_manager()
    if manager is None:
        where = r"references\tools-setup.md" if IS_WIN else "references/tools-setup.md"
        found = "winget was not found. Install 'App Installer' from the Microsoft Store" if IS_WIN \
            else "No Homebrew or apt found"
        return f"manual {found}, or see {where}."
    package = TOOLS[key][manager]
    if package is None:
        return "manual " + NO_PACKAGE.get((manager, key), "see references/tools-setup.md")
    return f"{manager} {package}"


def one_line(text):
    return " ".join(str(text).split()) or "-"


def plan(keys):
    for key in keys:
        r = check(key)
        install = install_for(key, r) if r.state == MISSING else "-"
        fields = [key, r.state, "1" if TOOLS[key]["essential"] else "0", install, r.detail, r.advice]
        print("\t".join(one_line(f) for f in fields))


def report():
    print(f"Video tools check (read-only). Running on Python {sys.version.split()[0]} ({sys.executable})")
    print()
    rows, essential_bad, optional_missing = [], [], []
    for key, tool in TOOLS.items():
        r = check(key)
        rows.append((tool["label"], LABELS[r.state], tool["purpose"], r.detail, r.advice))
        if r.state != OK:
            (essential_bad if tool["essential"] else optional_missing).append(tool["label"])

    npx, _ = find("npx")
    if npx:
        code, out = run([npx, "--no-install", "hyperframes", "--version"], timeout=40)
        rows.append(("HyperFrames CLI", "ok" if code == 0 else "missing", "titles, lower thirds",
                     out.strip().splitlines()[0][:60] if code == 0 and out.strip() else "used as: npx hyperframes", ""))
    venv_python = HERE / "venv" / ("Scripts/python.exe" if IS_WIN else "bin/python")
    whisper_python = str(venv_python) if venv_python.exists() else sys.executable
    for module, label, purpose in (("faster_whisper", "Local Whisper", "free local transcripts"),
                                   ("PIL", "Pillow", "labelled contact sheets")):
        code, _ = run([whisper_python, "-c", f"import {module}"])
        rows.append((label, "ok" if code == 0 else "missing", purpose,
                     whisper_python if code == 0 else "optional", ""))

    width = max(len(r[0]) for r in rows)
    for label, state, purpose, detail, advice in rows:
        print(f"{label:<{width}}  {state:<12} {purpose:<32} {detail}")
        if advice:
            print(f"{'':<{width}}  -> {advice}")
    print()
    if essential_bad:
        print("ESSENTIAL NOT READY: " + ", ".join(essential_bad) + " - see the advice above and references/tools-setup.md")
        sys.exit(1)
    print("Essentials ready. Optional not ready: " + (", ".join(optional_missing) or "none"))


def main():
    args = sys.argv[1:]
    if args[:1] in (["-h"], ["--help"]):
        print(__doc__)
        return
    if args[:1] == ["--plan"]:
        keys = args[1:] or list(TOOLS)
        unknown = [k for k in keys if k not in TOOLS]
        if unknown:
            sys.exit(f"Unknown tool(s): {', '.join(unknown)}. Choose from: {' '.join(TOOLS)}")
        plan(list(dict.fromkeys(keys)))
        return
    if args:
        sys.exit("Usage: python doctor.py [--plan KEY ...]")
    report()


if __name__ == "__main__":
    main()
