git = find_program('git')

# 'libdir' is likely a more FHS conformant target directory than 'datadir' for 'umu'
umu_install_path = get_option('datadir') / meson.project_name()

umu_run_cdata = configuration_data()
umu_run_cdata.set('INSTALL_PATH', get_option('prefix') / umu_install_path / 'umu_run.py')
configure_file(
    input : 'umu-run.in',
    output : 'umu-run',
    configuration : umu_run_cdata,
    install : true,
    install_dir : get_option('bindir'),
    install_mode: 'rwxr-xr-x',
)

install_data(
    [
        'umu_consts.py',
        'umu_proton.py',
        'umu_log.py',
        'umu_plugins.py',
        'umu_util.py',
        'umu_runtime.py',
    ],
    install_dir: umu_install_path,
)
install_data(
    [
        'umu_run.py',
    ],
    install_dir: umu_install_path,
    install_mode: 'rwxr-xr-x',
)

umu_version = run_command(
    git, '-C', meson.source_root(), 'describe', '--always', '--long', '--tags', check: true
).stdout().strip()
umu_version_cdata = configuration_data()
umu_version_cdata.set('UMU_VERSION', umu_version)
configure_file(
    input : 'umu_version.json.in',
    output : 'umu_version.json',
    configuration : umu_version_cdata,
    install : true,
    install_dir: umu_install_path,
)

subdir('umu-launcher')
