#!/bin/sh
# Installs the free tools the video production assistant uses, on macOS (Homebrew)
# or Debian/Ubuntu Linux (apt).
#
# Essentials (always): ffmpeg, python
# Options (--with a,b,c): node (HyperFrames graphics), uv (ElevenLabs connector),
#                         blender (3D diagrams), ytdlp (licensed outside clips), git
#
#   sh install.sh --dry-run        show what would happen; changes nothing
#   sh install.sh                  asks before each install
#   sh install.sh --with node,uv
#   sh install.sh --all
#   sh install.sh --yes            install without asking (needed when no one is at a terminal)
#
# Safety rules this script keeps:
#   - scripts/doctor.py decides what is ready, too old or missing. A tool found by any method
#     (PATH, NVM, fnm, mise, asdf, Volta, n, pyenv, conda, pip --user, ~/.local/bin, Homebrew
#     or apt, even when not loaded in this shell) is never installed again, upgraded or replaced.
#   - Nothing is installed without a yes, typed at the terminal or given as --yes.
#   - Homebrew runs without updating itself, upgrading other formulae or cleaning up.
#   - Each tool it installs is listed in ~/.local/state/video-production-assistant/installed.txt
#     (outside the skill folder, so updating the skill keeps the list); uninstall.sh removes
#     only those.
#   - --dry-run only reads. Running the script twice changes nothing the second time.
#   - Exits 1 if an essential tool is still not ready.
set -eu

HERE=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
SCRIPTS=$(CDPATH='' cd -- "$HERE/../scripts" && pwd)
# The list of what this script installed lives in the user's own folder, not the skill folder:
# a skill update replaces the skill folder, and it may be read-only.
STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/video-production-assistant"
MANIFEST="$STATE_DIR/installed.txt"
TAB=$(printf '\t')
ALL_OPTS="ffmpeg python node uv blender ytdlp git"
WANT="ffmpeg python"
DRY=0
YES=0
ATTENTION=""
ESSENTIAL_BAD=0

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY=1 ;;
    --yes) YES=1 ;;
    --all) WANT="$ALL_OPTS" ;;
    --with)
      shift
      [ $# -gt 0 ] || { echo "--with needs a list, e.g. --with node,uv" >&2; exit 2; }
      WANT="$WANT $(echo "$1" | tr ',' ' ')" ;;
    -h|--help) awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "$0"; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
  shift
done

# Check every name before anything is looked at or installed.
for name in $WANT; do
  case " $ALL_OPTS " in
    *" $name "*) ;;
    *) echo "Unknown option '$name'. Choose from: $ALL_OPTS" >&2; exit 2 ;;
  esac
done

if [ -t 0 ]; then HAVE_TTY=1; else HAVE_TTY=0; fi

# Same package manager choice as doctor.py: Homebrew (even if not on PATH), else apt.
BREW=""
for b in "$(command -v brew 2>/dev/null || true)" /opt/homebrew/bin/brew /usr/local/bin/brew \
         /home/linuxbrew/.linuxbrew/bin/brew; do
  if [ -n "$b" ] && [ -x "$b" ]; then BREW=$b; break; fi
done
if [ -n "$BREW" ]; then PM=brew
elif command -v apt-get >/dev/null 2>&1; then PM=apt
else PM=none
fi
BREW_ENV="HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_UPGRADE=1 HOMEBREW_NO_INSTALLED_DEPENDENTS_CHECK=1 HOMEBREW_NO_INSTALL_CLEANUP=1 HOMEBREW_NO_ENV_HINTS=1"

PY_MIN=$(sed -n 's/^PYTHON_MIN=//p' "$SCRIPTS/min_versions.txt" 2>/dev/null || true)
PY_MIN=${PY_MIN:-3.9}

say() { printf '%-15s %s\n' "$1" "$2"; }

attention() { ATTENTION="${ATTENTION}  - $1
"; }

essential_bad() { if [ "$1" = 1 ]; then ESSENTIAL_BAD=1; fi; }

confirm() {
  if [ "$YES" -eq 1 ]; then return 0; fi
  if [ "$HAVE_TTY" -eq 0 ]; then return 1; fi
  printf '%s [y/N] ' "$1"
  read -r answer </dev/tty || return 1
  case "$answer" in y|Y|yes|Yes|YES) return 0 ;; *) return 1 ;; esac
}

command_for() {  # METHOD PACKAGES -> the command that installs them
  case "$1" in
    brew) echo "env $BREW_ENV \"$BREW\" install $2" ;;
    apt) echo "sudo apt-get install -y $2" ;;
  esac
}

preview() {  # METHOD PACKAGES -> show what the package manager would add. Read-only.
  case "$1" in
    brew)
      # shellcheck disable=SC2086
      if out=$(env $BREW_ENV "$BREW" install --dry-run $2 2>&1 </dev/null); then
        printf '%s\n' "$out" | head -n 25 | sed 's/^/                /'
        say "" "Homebrew may also upgrade libraries you already have if this tool needs newer ones."
      else
        say "" "This Homebrew cannot list what it would add in advance. To see it: brew deps $2"
      fi ;;
    apt)
      # shellcheck disable=SC2086
      n=$(apt-get -s install $2 2>/dev/null </dev/null | grep -c '^Inst ' || true)
      if [ "$n" -gt 0 ]; then say "" "apt would install $n package(s), including dependencies."
      else say "" "apt cannot list what it would add yet (its package lists may need 'sudo apt-get update')."
      fi ;;
  esac
}

record() {  # KEY METHOD PACKAGES -> add to the list uninstall.sh reads; fails if it cannot be written
  mkdir -p "$STATE_DIR" 2>/dev/null || return 1
  if [ ! -f "$MANIFEST" ]; then
    printf '# Tools install.sh installed. uninstall.sh removes only these.\n' > "$MANIFEST" || return 1
  fi
  if ! grep -q "^$1$TAB" "$MANIFEST"; then
    printf '%s\t%s\t%s\n' "$1" "$2" "$3" >> "$MANIFEST" || return 1
  fi
}

# The loops below read their list from standard input. A package manager that also reads
# standard input would swallow the rest of that list, so it gets the terminal, or nothing.
run_cmd() {
  if [ "$HAVE_TTY" -eq 1 ]; then sh -c "$1" </dev/tty; else sh -c "$1" </dev/null; fi
}

install_tool() {  # KEY METHOD PACKAGES ESSENTIAL
  cmd=$(command_for "$2" "$3")
  if [ "$DRY" -eq 1 ]; then
    say "[would install]" "$1: $cmd"
    preview "$2" "$3"
    return 0
  fi
  say "[missing]" "$1 can be installed with: $cmd"
  preview "$2" "$3"
  if ! confirm "Install $1 now?"; then
    if [ "$YES" -eq 0 ] && [ "$HAVE_TTY" -eq 0 ]; then
      say "[skipped]" "$1: no terminal to ask. Run this in a terminal, or add --yes."
    else
      say "[skipped]" "$1 was not installed."
    fi
    essential_bad "$4"
    return 0
  fi
  if run_cmd "$cmd"; then
    say "[installed]" "$1"
    if ! record "$1" "$2" "$3"; then
      say "[warn]" "Could not write $MANIFEST, so uninstall.sh will not know about $1."
      say "" "To remove it later, do it by hand."
    fi
  else
    say "[warn]" "$1 did not install. Carrying on."
    if [ "$2" = apt ]; then say "" "If apt could not find it, run 'sudo apt-get update' and try again."; fi
    essential_bad "$4"
  fi
}

is_mac_stub() {  # Apple's placeholder python3 opens an installer dialog if run without Command Line Tools
  [ "$(uname)" = Darwin ] || return 1
  case "$1" in /usr/bin/python3) ! xcode-select -p >/dev/null 2>&1 ;; *) return 1 ;; esac
}

py_ok() {
  "$1" -c "import sys; sys.exit(0 if sys.version_info >= tuple(int(x) for x in '$PY_MIN'.split('.')) else 1)" \
    >/dev/null 2>&1
}

py_dirs() {  # PATH first, then the folders doctor.py also searches for Python
  printf '%s\n' "$PATH" | tr ':' '\n'
  for d in "$HOME/.local/bin" "${PYENV_ROOT:-$HOME/.pyenv}/shims" "${ASDF_DATA_DIR:-$HOME/.asdf}/shims" \
           "${MISE_DATA_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/mise}/shims" /opt/homebrew/bin \
           /usr/local/bin /home/linuxbrew/.linuxbrew/bin "$HOME/miniconda3/bin" "$HOME/anaconda3/bin" \
           "$HOME/miniforge3/bin" "$HOME/mambaforge/bin"; do
    printf '%s\n' "$d"
  done
}

find_python() {  # sets PY to a Python new enough to run doctor.py, or OLD_PY to an older one
  PY=""; OLD_PY=""
  while IFS= read -r dir; do
    [ -n "$dir" ] || continue
    for n in python3 python3.14 python3.13 python3.12 python3.11 python3.10 python3.9 python; do
      c="$dir/$n"
      if [ ! -x "$c" ] || [ -d "$c" ] || is_mac_stub "$c"; then continue; fi
      if py_ok "$c"; then PY=$c; return 0; fi
      if [ -z "$OLD_PY" ]; then OLD_PY=$c; fi
    done
  done <<EOF
$(py_dirs)
EOF
  return 1
}

# 1. Python runs doctor.py, so find (or install) it first.
if ! find_python; then
  if [ -n "$OLD_PY" ]; then
    say "[too old]" "$OLD_PY is older than Python $PY_MIN"
    say "" "Upgrade Python the way you installed it (pyenv: 'pyenv install 3.12' then 'pyenv global 3.12')."
    say "" "A second Python was not installed, to avoid clashes. Then run this script again."
    exit 1
  fi
  case "$PM" in
    brew) install_tool python brew python 1 ;;
    apt) install_tool python apt "python3 python3-venv python3-pip" 1 ;;
    *) say "[manual]" "python - no Homebrew or apt found. See references/tools-setup.md."; exit 1 ;;
  esac
  if [ "$DRY" -eq 1 ]; then
    echo
    echo "The other tools are checked once Python is installed."
    echo "Dry run: nothing was installed or changed."
    exit 0
  fi
  if ! find_python; then
    echo "Python is not available, so the other tools cannot be checked."
    exit 1
  fi
fi

# 2. Ask doctor.py about every tool wanted, then act on its answers.
# shellcheck disable=SC2086
PLAN=$("$PY" "$SCRIPTS/doctor.py" --plan $WANT)

while IFS="$TAB" read -r key state essential install detail advice; do
  [ -n "$key" ] || continue
  case "$state" in
    ok)
      say "[ok]" "$detail"
      if [ "$advice" != "-" ]; then attention "$key: $advice"; fi ;;
    too_old|incomplete|not_on_path)
      case "$state" in
        too_old) label="[too old]" ;;
        incomplete) label="[incomplete]" ;;
        *) label="[not on PATH]" ;;
      esac
      say "$label" "$detail"
      say "" "$advice"
      attention "$key: $detail. Nothing was changed; see the advice above."
      essential_bad "$essential" ;;
    missing)
      method=${install%% *}
      packages=${install#* }
      case "$method" in
        brew|apt) install_tool "$key" "$method" "$packages" "$essential" ;;
        *)
          say "[manual]" "$key: $packages"
          essential_bad "$essential" ;;
      esac ;;
  esac
done <<EOF
$PLAN
EOF

echo
if [ -n "$ATTENTION" ]; then
  echo "Needs your attention (nothing was changed for these):"
  printf '%s' "$ATTENTION"
  echo
fi
if [ "$DRY" -eq 1 ]; then echo "Dry run: nothing was installed or changed."; fi
echo "Check any time with:   \"$PY\" \"$SCRIPTS/doctor.py\""
echo "Remove what this installed:   sh \"$HERE/uninstall.sh\"   (its list: $MANIFEST)"
echo "Local Whisper is optional and is set up per video library (it asks first):"
echo "  \"$PY\" \"$SCRIPTS/init_library.py\" \"/path/to/Video Library\" --venv"
if [ "$DRY" -eq 0 ] && [ "$ESSENTIAL_BAD" -eq 1 ]; then exit 1; fi
