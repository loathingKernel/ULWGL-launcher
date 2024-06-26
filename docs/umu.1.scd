umu(1)

# NAME

umu-run - Unified Launcher for Windows Games on Linux

# SYNOPSIS

*umu-run* [_OPTIONS_...] [_FILE_ [_ARG_...] | _FILE_]

# OPTIONS

*-h, --help*
	Show this help message.

*--config* <config>
	Path to TOML configuration file (Requires Python 3.11+).

	See *umu*(5) for more info and examples.

# DESCRIPTION

The Unified Launcher for Windows Games on Linux (umu) was created to make
Valve's *Proton*[1] and the *protonfixes*[2] project accessible outside the Steam client,
providing a standardized way for other clients (e.g., Lutris, Heroic Games
Launcher, Bottles, or Rare) to run games via Proton and configure WINE
prefixes.

As a result, clients:
- No longer require Steam or Steam binaries to be installed
- Can contribute and benefit from protonfixes
- Can run games through Proton as it were a native Steam game
- Can reference a unified online database of game fixes (protonfixes)

You can run umu directly from a terminal emulator, or through your launcher of 
choice if supported.

# EXAMPLES

*Example 1. Run a game*

```
$ WINEPREFIX=~/.wine GAMEID=0 PROTONPATH=~/GE-Proton9-4 umu-run ~/foo.exe
```

*Example 2. Run a game and apply a Protonfix*

```
# Applies a GOG Protonfix to the current WINE prefix
# See https://github.com/Open-Wine-Components/umu-protonfixes
$ WINEPREFIX=~/.wine GAMEID=umu-1228964594 PROTONPATH=~/GE-Proton9-4 STORE=gog umu-run ~/foo.exe
```

*Example 3. Run a game via a configuration file*

```
# config.toml
[umu]
prefix = "~/.wine"
proton = "~/GE-Proton30"
game_id = "0"
exe = "~/foo.exe"
launch_args = ["-opengl", "-SkipBuildPatchPrereq"]
store = "gog"
$ umu-run --config config.toml
```

*Example 4. Create a umu WINE prefix*

```
$ WINEPREFIX=~/foo GAMEID=0 PROTONPATH=~/GE-Proton9-4 umu-run ""
```

*Example 5. Run a game and automatically set Proton*

```
# Always checks for the latest release of UMU-Proton, and will download then
# use it when available
# NOTE: Previous stable versions of UMU-Proton will be auto removed in
# compatibilitytools.d after the latest has been downloaded
$ WINEPREFIX=~/.wine GAMEID=0 umu-run foo.exe
```

*Example 6. Run a game, automatically set Proton, and create a WINE prefix*

```
# This will create the prefix as ~/Games/umu/$GAMEID and will
# set the latest UMU-Proton for the game
$ GAMEID=0 umu-run foo.exe
```

*Example 7. Run a game and explicitly set a valid Proton verb*

```
$ WINEPREFIX=~/.wine GAMEID=0 PROTONPATH=~/GE-Proton9-4 PROTON_VERB=waitforexitandrun umu-run ~/foo.exe
```

*Example 8. Run a game and enable debug logs*

```
# Shows environment variables and command at this level
# Valid values for UMU_LOG include: 1, warn, debug
$ UMU_LOG=1 WINEPREFIX=~/.wine GAMEID=0 PROTONPATH=~/GE-Proton9-4 umu-run ~/foo.exe
```

*Example 9. Run a game and set a Proton by its version name*

```
# The launcher will check for GE-Proton9-1 at
# ~/.local/share/Steam/compatibilitytools.d
$ WINEPREFIX=~/.wine GAMEID=0 PROTONPATH=GE-Proton9-1 umu-run ~/foo.exe
```

*Example 10. Run a game and automatically use the latest GE-Proton*

```
# This will fetch for the latest GE-Proton build each run and set it
$ WINEPREFIX=~/.wine GAMEID=0 PROTONPATH=GE-Proton umu-run ~/foo.exe
```

*Example 11. Run winetricks verbs*

```
$ GAMEID=0 PROTONPATH=GE-Proton umu-run winetricks quartz wmp11 qasf
```

# SEE ALSO

_umu_(5)

# NOTES

. https://github.com/ValveSoftware/Proton
. https://github.com/Open-Wine-Components/umu-protonfixes

# AUTHORS

Maintained by Open Wine Components members, and assisted by other open source
contributors. For more information about umu development, see
https://github.com/Open-Wine-Components/umu-launcher.
