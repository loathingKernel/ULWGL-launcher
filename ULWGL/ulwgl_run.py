#!/usr/bin/env python3

import os
import sys
from traceback import print_exception
from argparse import ArgumentParser, Namespace, RawTextHelpFormatter
from pathlib import Path
from typing import Dict, Any, List, Set, Union, Tuple
from ulwgl_plugins import enable_steam_game_drive, set_env_toml, enable_reaper
from re import match
from subprocess import run
from ulwgl_dl_util import get_ulwgl_proton
from ulwgl_consts import Level, PROTON_VERBS
from ulwgl_util import msg, setup_ulwgl
from ulwgl_log import log, console_handler, debug_formatter
from ulwgl_util import UnixUser


def parse_args() -> Union[Namespace, Tuple[str, List[str]]]:  # noqa: D103
    opt_args: Set[str] = {"--help", "-h", "--config"}
    exe: str = Path(__file__).name
    usage: str = f"""
example usage:
  GAMEID= {exe} /home/foo/example.exe
  WINEPREFIX= GAMEID= {exe} /home/foo/example.exe
  WINEPREFIX= GAMEID= PROTONPATH= {exe} /home/foo/example.exe
  WINEPREFIX= GAMEID= PROTONPATH= {exe} /home/foo/example.exe -opengl
  WINEPREFIX= GAMEID= PROTONPATH= {exe} ""
  WINEPREFIX= GAMEID= PROTONPATH= PROTON_VERB= {exe} /home/foo/example.exe
  WINEPREFIX= GAMEID= PROTONPATH= STORE= {exe} /home/foo/example.exe
  ULWGL_LOG= GAMEID= {exe} /home/foo/example.exe
  {exe} --config /home/foo/example.toml
    """
    parser: ArgumentParser = ArgumentParser(
        description="Unified Linux Wine Game Launcher",
        epilog=usage,
        formatter_class=RawTextHelpFormatter,
    )
    parser.add_argument("--config", help="path to TOML file (requires Python 3.11)")

    if not sys.argv[1:]:
        err: str = "Please see project README.md for more info and examples.\nhttps://github.com/Open-Wine-Components/ULWGL-launcher"
        parser.print_help(sys.stderr)
        raise SystemExit(err)

    if sys.argv[1:][0] in opt_args:
        return parser.parse_args(sys.argv[1:])

    if sys.argv[1] in PROTON_VERBS:
        if "PROTON_VERB" not in os.environ:
            os.environ["PROTON_VERB"] = sys.argv[1]
        sys.argv.pop(1)

    return sys.argv[1], sys.argv[2:]


def set_log() -> None:
    """Adjust the log level for the logger."""
    levels: Set[str] = {"1", "warn", "debug"}

    if os.environ["ULWGL_LOG"] not in levels:
        return

    if os.environ["ULWGL_LOG"] == "1":
        # Show the envvars and command at this level
        log.setLevel(level=Level.INFO.value)
    elif os.environ["ULWGL_LOG"] == "warn":
        log.setLevel(level=Level.WARNING.value)
    elif os.environ["ULWGL_LOG"] == "debug":
        # Show all logs
        console_handler.setFormatter(debug_formatter)
        log.addHandler(console_handler)
        log.setLevel(level=Level.DEBUG.value)

    os.environ.pop("ULWGL_LOG")


def setup_pfx(path: str) -> None:
    """Create a symlink to the WINE prefix and tracked_files file."""
    pfx: Path = Path(path).joinpath("pfx").expanduser()
    steam: Path = Path(path).expanduser().joinpath("drive_c/users/steamuser")
    user: UnixUser = UnixUser()
    wineuser: Path = (
        Path(path).expanduser().joinpath(f"drive_c/users/{user.get_user()}")
    )

    if pfx.is_symlink():
        pfx.unlink()

    if not pfx.is_dir():
        pfx.symlink_to(Path(path).expanduser())

    Path(path).joinpath("tracked_files").expanduser().touch()

    # Create a symlink of the current user to the steamuser dir or vice versa
    # Default for a new prefix is: unixuser -> steamuser
    if (
        not wineuser.is_dir()
        and not steam.is_dir()
        and not (wineuser.is_symlink() or steam.is_symlink())
    ):
        # For new prefixes with our Proton: user -> steamuser
        steam.mkdir(parents=True)
        wineuser.unlink(missing_ok=True)
        wineuser.symlink_to("steamuser")
    elif wineuser.is_dir() and not steam.is_dir() and not steam.is_symlink():
        # When there's a user dir: steamuser -> user
        # Be sure it's relative
        steam.unlink(missing_ok=True)
        steam.symlink_to(user.get_user())
    elif not wineuser.exists() and not wineuser.is_symlink() and steam.is_dir():
        wineuser.unlink(missing_ok=True)
        wineuser.symlink_to("steamuser")
    else:
        paths: List[str] = [steam.as_posix(), wineuser.as_posix()]
        log.warning(
            msg(
                f"Skipping link creation for prefix: {pfx}",
                Level.WARNING,
            )
        )
        log.warning(
            msg(
                f"Following paths already exist: {paths}",
                Level.WARNING,
            )
        )


def check_env(
    env: Dict[str, str], toml: Dict[str, Any] = None
) -> Union[Dict[str, str], Dict[str, Any]]:
    """Before executing a game, check for environment variables and set them.

    WINEPREFIX, GAMEID and PROTONPATH are strictly required.
    """
    if "GAMEID" not in os.environ:
        err: str = "Environment variable not set: GAMEID"
        raise ValueError(err)
    env["GAMEID"] = os.environ["GAMEID"]

    if "WINEPREFIX" not in os.environ:
        pfx: Path = Path.home().joinpath("Games/ULWGL/" + env["GAMEID"])
        pfx.mkdir(parents=True, exist_ok=True)
        os.environ["WINEPREFIX"] = pfx.as_posix()
    if not Path(os.environ["WINEPREFIX"]).expanduser().is_dir():
        pfx: Path = Path(os.environ["WINEPREFIX"])
        pfx.mkdir(parents=True, exist_ok=True)
        os.environ["WINEPREFIX"] = pfx.as_posix()

    env["WINEPREFIX"] = os.environ["WINEPREFIX"]

    # Proton Version
    if (
        "PROTONPATH" in os.environ
        and os.environ["PROTONPATH"]
        and Path(
            "~/.local/share/Steam/compatibilitytools.d/" + os.environ["PROTONPATH"]
        )
        .expanduser()
        .is_dir()
    ):
        log.debug(msg("Proton version selected", Level.DEBUG))
        os.environ["PROTONPATH"] = (
            Path("~/.local/share/Steam/compatibilitytools.d")
            .joinpath(os.environ["PROTONPATH"])
            .expanduser()
            .as_posix()
        )

    if "PROTONPATH" not in os.environ:
        os.environ["PROTONPATH"] = ""
        get_ulwgl_proton(env)

    env["PROTONPATH"] = os.environ["PROTONPATH"]

    # If download fails/doesn't exist in the system, raise an error
    if not os.environ["PROTONPATH"]:
        err: str = "Download failed.\nProton could not be found in cache or compatibilitytools.d\nPlease set $PROTONPATH or visit https://github.com/Open-Wine-Components/ULWGL-Proton/releases"
        raise FileNotFoundError(err)

    return env


def set_env(
    env: Dict[str, str], args: Union[Namespace, Tuple[str, List[str]]]
) -> Dict[str, str]:
    """Set various environment variables for the Steam RT.

    Filesystem paths will be formatted and expanded as POSIX
    """
    # PROTON_VERB
    # For invalid Proton verbs, just assign the waitforexitandrun
    if "PROTON_VERB" in os.environ and os.environ["PROTON_VERB"] in PROTON_VERBS:
        env["PROTON_VERB"] = os.environ["PROTON_VERB"]
    else:
        env["PROTON_VERB"] = "waitforexitandrun"

    # EXE
    # Empty string for EXE will be used to create a prefix
    if isinstance(args, tuple) and isinstance(args[0], str) and not args[0]:
        env["EXE"] = ""
        env["STEAM_COMPAT_INSTALL_PATH"] = ""
        env["PROTON_VERB"] = "waitforexitandrun"
    elif isinstance(args, tuple):
        env["EXE"] = Path(args[0]).expanduser().as_posix()
        env["STEAM_COMPAT_INSTALL_PATH"] = Path(env["EXE"]).parent.as_posix()
    else:
        # Config branch
        env["EXE"] = Path(env["EXE"]).expanduser().as_posix()
        env["STEAM_COMPAT_INSTALL_PATH"] = Path(env["EXE"]).parent.as_posix()

    if "STORE" in os.environ:
        env["STORE"] = os.environ["STORE"]

    # ULWGL_ID
    env["ULWGL_ID"] = env["GAMEID"]
    env["STEAM_COMPAT_APP_ID"] = "0"

    if match(r"^ulwgl-[\d\w]+$", env["ULWGL_ID"]):
        env["STEAM_COMPAT_APP_ID"] = env["ULWGL_ID"][env["ULWGL_ID"].find("-") + 1 :]
    env["SteamAppId"] = env["STEAM_COMPAT_APP_ID"]
    env["SteamGameId"] = env["SteamAppId"]

    # PATHS
    env["WINEPREFIX"] = Path(env["WINEPREFIX"]).expanduser().as_posix()
    env["PROTONPATH"] = Path(env["PROTONPATH"]).expanduser().as_posix()
    env["STEAM_COMPAT_DATA_PATH"] = env["WINEPREFIX"]
    env["STEAM_COMPAT_SHADER_PATH"] = env["STEAM_COMPAT_DATA_PATH"] + "/shadercache"
    env["STEAM_COMPAT_TOOL_PATHS"] = (
        env["PROTONPATH"]
        + ":"
        + Path.home().joinpath(".local", "share", "ULWGL").as_posix()
    )
    env["STEAM_COMPAT_MOUNTS"] = env["STEAM_COMPAT_TOOL_PATHS"]

    return env


def build_command(
    env: Dict[str, str], local: Path, command: List[str], opts: List[str] = None
) -> List[str]:
    """Build the command to be executed."""
    entry_point: str = ""
    verb: str = env["PROTON_VERB"]

    # Raise an error if the _v2-entry-point cannot be found
    if not local.joinpath("ULWGL").is_file():
        home: str = Path.home().as_posix()
        dir: str = Path(__file__).parent.as_posix()
        msg: str = f"Path to _v2-entry-point cannot be found in: {home}/.local/share or {dir}\nPlease install a Steam Runtime platform"
        raise FileNotFoundError(msg)

    entry_point = local.as_posix()

    if not Path(env.get("PROTONPATH")).joinpath("proton").is_file():
        err: str = "The following file was not found in PROTONPATH: proton"
        raise FileNotFoundError(err)

    enable_reaper(env, command, entry_point)

    command.extend([entry_point, "--verb", verb, "--"])
    command.extend(
        [
            Path(env.get("PROTONPATH")).joinpath("proton").as_posix(),
            verb,
            env.get("EXE"),
        ]
    )

    if opts:
        command.extend([*opts])

    return command


def main() -> int:  # noqa: D103
    env: Dict[str, str] = {
        "WINEPREFIX": "",
        "GAMEID": "",
        "PROTON_CRASH_REPORT_DIR": "/tmp/ULWGL_crashreports",
        "PROTONPATH": "",
        "STEAM_COMPAT_APP_ID": "",
        "STEAM_COMPAT_TOOL_PATHS": "",
        "STEAM_COMPAT_LIBRARY_PATHS": "",
        "STEAM_COMPAT_MOUNTS": "",
        "STEAM_COMPAT_INSTALL_PATH": "",
        "STEAM_COMPAT_CLIENT_INSTALL_PATH": "",
        "STEAM_COMPAT_DATA_PATH": "",
        "STEAM_COMPAT_SHADER_PATH": "",
        "FONTCONFIG_PATH": "",
        "EXE": "",
        "SteamAppId": "",
        "SteamGameId": "",
        "STEAM_RUNTIME_LIBRARY_PATH": "",
        "STORE": "",
        "PROTON_VERB": "",
        "ULWGL_ID": "",
    }
    command: List[str] = []
    opts: List[str] = None
    # Expected files in this dir: pressure vessel, launcher files, runtime platform, runner, config
    # root: Path = Path("/usr/share/ULWGL")
    root: Path = Path(__file__).resolve().parent
    # Expects this dir to be in sync with root
    # On update, files will be selectively updated
    local: Path = Path.home().joinpath(".local/share/ULWGL")
    args: Union[Namespace, Tuple[str, List[str]]] = parse_args()

    if "musl" in os.environ.get("LD_LIBRARY_PATH", ""):
        err: str = "This script is not designed to run on musl-based systems"
        raise SystemExit(err)

    if "ULWGL_LOG" in os.environ:
        set_log()

    setup_ulwgl(root, local)

    if isinstance(args, Namespace) and getattr(args, "config", None):
        set_env_toml(env, args)
    else:
        # Reference the game options
        opts = args[1]
        check_env(env)

    setup_pfx(env["WINEPREFIX"])
    set_env(env, args)

    # Game Drive
    enable_steam_game_drive(env)

    # Set all environment variables
    # NOTE: `env` after this block should be read only
    for key, val in env.items():
        log.info(msg(f"{key}={val}", Level.INFO))
        os.environ[key] = val

    build_command(env, local, command, opts)
    log.debug(msg(command, Level.DEBUG))
    return run(command).returncode


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log.warning(msg("Keyboard Interrupt", Level.WARNING))
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        log.exception(msg(str(e), Level.ERROR))
        sys.exit(1)
    finally:
        # Cleanup .ref file on every exit
        Path.home().joinpath(".local/share/ULWGL/.ref").unlink(missing_ok=True)
