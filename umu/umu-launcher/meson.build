fs = import('fs')

umu_launcher_run_cdata = configuration_data()
if get_option('flatpak')
    umu_launcher_run_cdata.set('INSTALL_PATH', 'org.openwinecomponents.umu.launcher')
else
    umu_launcher_run_cdata.set('INSTALL_PATH', umu_run_cdata.get('INSTALL_PATH'))
endif

# Alternative path using 'umu' as parent folder instead of 'umu-launcher'
#umu_launcher_install_path = get_option('datadir') / 'steam' / 'compatibilitytools.d' / meson.project_name()
umu_launcher_install_path = get_option('datadir') / 'steam' / 'compatibilitytools.d' / fs.name(meson.current_source_dir())

configure_file(
    input : 'umu-run.in',
    output : 'umu-run',
    configuration : umu_launcher_run_cdata,
    install : true,
    install_dir : umu_launcher_install_path,
    install_mode: 'rwxr-xr-x',
)

install_data(
    [
        'compatibilitytool.vdf',
        'toolmanifest.vdf'
    ],
    install_dir: umu_launcher_install_path,
)
