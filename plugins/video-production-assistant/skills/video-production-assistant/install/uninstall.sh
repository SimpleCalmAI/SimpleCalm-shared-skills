#!/bin/sh
# Removes the tools that install.sh installed, and nothing else.
#
#   sh uninstall.sh --dry-run    show what would be removed; changes nothing
#   sh uninstall.sh              asks before each removal
#   sh uninstall.sh --yes        remove without asking
#
# Two things can also remove software that this skill did not install, so they are only ever
# offered as a question at the terminal; --yes never covers them:
#   - removing a tool that other packages have come to depend on (apt removes those too);
#   - clearing out libraries that are no longer needed ('brew autoremove', 'apt-get autoremove').
#
# It reads ~/.local/state/video-production-assistant/installed.txt, which install.sh writes.
# Tools you had before are never on that list, so they are never touched. At the end it lists
# the other things the video production assistant can leave on the computer, for you to remove
# by hand if you want.
set -eu

HERE=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
SCRIPTS=$(CDPATH='' cd -- "$HERE/../scripts" && pwd)
CONNECTORS=$(CDPATH='' cd -- "$HERE/../connectors" && pwd)
MANIFEST="${XDG_STATE_HOME:-$HOME/.local/state}/video-production-assistant/installed.txt"
TAB=$(printf '\t')
DRY=0
YES=0
REMOVED_BREW=0
REMOVED_APT=0

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY=1 ;;
    --yes) YES=1 ;;
    -h|--help) awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "$0"; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
  shift
done

if [ -t 0 ]; then HAVE_TTY=1; else HAVE_TTY=0; fi

BREW=""
for b in "$(command -v brew 2>/dev/null || true)" /opt/homebrew/bin/brew /usr/local/bin/brew \
         /home/linuxbrew/.linuxbrew/bin/brew; do
  if [ -n "$b" ] && [ -x "$b" ]; then BREW=$b; break; fi
done
BREW_ENV="HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_CLEANUP=1 HOMEBREW_NO_ENV_HINTS=1"

say() { printf '%-15s %s\n' "$1" "$2"; }

confirm() {
  if [ "$YES" -eq 1 ]; then return 0; fi
  ask "$1"
}

ask() {  # a yes typed at the terminal; --yes does not count
  if [ "$HAVE_TTY" -eq 0 ]; then return 1; fi
  printf '%s [y/N] ' "$1"
  read -r answer </dev/tty || return 1
  case "$answer" in y|Y|yes|Yes|YES) return 0 ;; *) return 1 ;; esac
}

still_installed() {  # METHOD PACKAGES
  case "$1" in
    brew)
      [ -n "$BREW" ] || return 1
      prefix=$(dirname "$(dirname "$BREW")")
      name=${2##* }
      case "$2" in
        --cask*) [ -e "$prefix/Caskroom/$name" ] ;;
        *) [ -e "$prefix/opt/$name" ] || ls -d "$prefix/opt/$name"@* >/dev/null 2>&1 ;;
      esac ;;
    apt) dpkg-query -W -f='${db:Status-Abbrev}' "${2%% *}" 2>/dev/null | grep -q '^ii' ;;
    *) return 1 ;;
  esac
}

forget() {  # KEY -> take it off the list
  grep -v "^$1$TAB" "$MANIFEST" > "$MANIFEST.tmp" || true
  mv "$MANIFEST.tmp" "$MANIFEST"
}

# The loop below reads its list from standard input. A package manager that also reads
# standard input would swallow the rest of that list, so it gets the terminal, or nothing.
run_cmd() {
  if [ "$HAVE_TTY" -eq 1 ]; then sh -c "$1" </dev/tty; else sh -c "$1" </dev/null; fi
}

also_removed() {  # PACKAGES -> other installed packages apt would remove with them. Read-only.
  # shellcheck disable=SC2086
  for p in $(apt-get -s remove $1 2>/dev/null </dev/null | sed -n 's/^Remv \([^ ]*\).*/\1/p'); do
    case " $1 " in *" $p "*) ;; *) printf ' %s' "$p" ;; esac
  done
}

if [ ! -f "$MANIFEST" ] || ! grep -q "$TAB" "$MANIFEST"; then
  say "[nothing]" "install.sh has not installed anything here, so there is nothing to remove."
else
  ENTRIES=$(grep -v '^#' "$MANIFEST" || true)
  while IFS="$TAB" read -r key method packages; do
    [ -n "$key" ] || continue
    # The package names go into a command line, so accept only the characters real names use.
    if [ -z "$packages" ] || printf '%s' "$packages" | grep -q '[^A-Za-z0-9 ._+@-]'; then
      say "[skip]" "$key: its line in $MANIFEST looks damaged, so nothing was done for it."
      continue
    fi
    if ! still_installed "$method" "$packages"; then
      say "[gone]" "$key is no longer installed by $method."
      if [ "$DRY" -eq 0 ]; then forget "$key"; fi
      continue
    fi
    case "$method" in
      brew) cmd="env $BREW_ENV \"$BREW\" uninstall $packages" ;;
      apt) cmd="sudo apt-get remove -y $packages" ;;
      *) say "[skip]" "$key: unknown method '$method'"; continue ;;
    esac
    # Other packages may have come to depend on this tool since it was installed. apt removes
    # those too, so that needs a yes typed at the terminal; --yes does not cover it.
    others=""
    if [ "$method" = apt ]; then others=$(also_removed "$packages"); fi
    if [ "$DRY" -eq 1 ]; then
      say "[would remove]" "$key: $cmd"
      if [ -n "$others" ]; then say "" "apt would also remove:$others (asked at the terminal; --yes does not cover it)"; fi
      continue
    fi
    if [ -n "$others" ]; then
      say "" "Removing $key would also remove other packages that depend on it:$others"
      if ask "Remove $key and those packages too ($cmd)?"; then go=1
      else
        go=0
        if [ "$HAVE_TTY" -eq 0 ]; then say "" "That needs a yes typed at a terminal; --yes does not cover it."; fi
      fi
    elif confirm "Remove $key ($cmd)?"; then go=1
    else go=0
    fi
    if [ "$go" -eq 1 ]; then
      if run_cmd "$cmd"; then
        say "[removed]" "$key"
        forget "$key"
        if [ "$method" = brew ]; then REMOVED_BREW=1; else REMOVED_APT=1; fi
      else
        say "[warn]" "$key was not removed (another program may need it). It stays on the list."
      fi
    else
      say "[kept]" "$key"
    fi
  done <<EOF
$ENTRIES
EOF
fi

# Libraries that were pulled in only for the removed tools.
if [ "$REMOVED_BREW" -eq 1 ]; then
  # shellcheck disable=SC2086
  orphans=$(env $BREW_ENV "$BREW" autoremove --dry-run 2>/dev/null | grep -v '^==>' || true)
  if [ -n "$orphans" ]; then
    echo
    echo "Homebrew libraries that nothing installed needs any more (some may be older than this skill):"
    printf '%s\n' "$orphans" | sed 's/^/  /'
    if ask "Remove them with 'brew autoremove'?"; then
      # shellcheck disable=SC2086
      env $BREW_ENV "$BREW" autoremove
    else
      echo "Left in place. To remove them later: brew autoremove"
    fi
  fi
fi
if [ "$REMOVED_APT" -eq 1 ]; then
  orphans=$(apt-get -s autoremove 2>/dev/null | sed -n 's/^Remv \([^ ]*\).*/\1/p' | tr '\n' ' ')
  if [ -n "$orphans" ]; then
    echo
    echo "apt packages that nothing installed needs any more: $orphans"
    if ask "Remove them with 'sudo apt-get autoremove'?"; then sudo apt-get autoremove -y
    else echo "Left in place. To remove them later: sudo apt-get autoremove"
    fi
  fi
fi

echo
echo "Not removed automatically. Remove these yourself if you want no trace:"
echo "  - In each video library: _tools/venv (local Whisper) and _tools/models (its speech"
echo "    models), or the whole _tools folder. Your videos and notes are elsewhere in the library."
if [ -d "$HOME/.cache/huggingface/hub" ] && ls -d "$HOME/.cache/huggingface/hub"/models--Systran--faster-whisper-* >/dev/null 2>&1; then
  echo "  - Whisper models downloaded by older versions of this skill:"
  echo "    $HOME/.cache/huggingface/hub/models--Systran--faster-whisper-*"
fi
echo "  - Connector entries added to an MCP config file:"
echo "    python3 \"$CONNECTORS/setup_connectors.py\" --remove all --target <that file>"
echo "    (a <file>.bak copy sits next to it; delete it once you are happy)"
if command -v uv >/dev/null 2>&1; then
  echo "  - uv's copy of the ElevenLabs connector:   uv cache clean elevenlabs-mcp"
fi
if [ -d "$HOME/.npm/_npx" ]; then
  echo "  - npx's copies of HyperFrames and Desktop Commander: $HOME/.npm/_npx"
  echo "    (it holds every package npx has run; npx downloads again if needed)"
fi
echo "  - This skill's own folder, once you no longer want the skill: $(dirname "$SCRIPTS")"
if [ "$DRY" -eq 1 ]; then echo; echo "Dry run: nothing was removed or changed."; fi
