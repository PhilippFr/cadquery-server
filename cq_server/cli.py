'''Module cli: handles command line interface.'''

from sys import exit as sys_exit
import argparse
import os.path as op

from . import __version__ as cqs_version


DEFAULT_PORT = 5000


def parse_args(parser: argparse.ArgumentParser) -> argparse.Namespace:
    '''Parse cli arguments with argparse.'''

    parser.description = 'A web server used to render 3d models from CadQuery code, ' \
        + 'and eventually build a static website as a showcase for your projects.'
    parser.add_argument('-V', '--version', action='store_true',
        help='print CadQuery Server version and exit')

    subparsers = parser.add_subparsers(title='subcommands', dest='cmd',
        description='type <command> -h for subcommand usage')

    parser_run = subparsers.add_parser('run',
        help='run the server',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog='''examples:
cq-server run                    # run cq-server with current folder as target on port 5000
cq-server run -p 8080 ./examples # run cq-server with "examples" as target on port 8080
cq-server run ./examples/box.py  # run cq-server with only box.py as target
''')

    parser_run.add_argument('target', nargs='?', default='.',
        help='python file or folder containing CadQuery script to load (default: ".")')
    parser_run.add_argument('-p', '--port', type=int, default=DEFAULT_PORT,
        help=f'server port (default: { DEFAULT_PORT })')
    parser_run.add_argument('-r', '--raise', dest='should_raise', action='store_true',
        help='when an error happen, raise it instead showing its title')
    parser_run.add_argument('-d', '--dead', action='store_true',
        help='disable live reloading')
    add_ui_options(parser_run)

    return parser.parse_args()


def add_ui_options(parser: argparse.ArgumentParser):
    '''Add ui option to the parser, that can be used in both run and build sub-commands.'''

    parse_ui = parser.add_argument_group('user interface options')
    parse_ui.add_argument('--ui-hide', metavar='LIST',
        help='a comma-separated list of buttons to hide'
            + ', among: axes, axes0, grid, ortho, more, help, all')
    parse_ui.add_argument('--ui-glass', action='store_true',
        help='activate tree view glass mode')
    parse_ui.add_argument('--ui-theme', choices=['light', 'dark'], metavar='THEME',
        help='set ui theme: light or dark (default: browser config)')
    parse_ui.add_argument('--ui-trackball', action='store_true',
        help='set control mode to trackball instead orbit')
    parse_ui.add_argument('--ui-perspective', action='store_true',
        help='set camera view to perspective instead orthogonal')
    parse_ui.add_argument('--ui-grid', metavar='AXES',
        help='display a grid in specified axes (x, y, z, xy, etc.)')
    parse_ui.add_argument('--ui-transparent', action='store_true',
        help='make objects semi-transparent')
    parse_ui.add_argument('--ui-black-edges', action='store_true',
        help='make edges black')

def get_ui_options(args: argparse.Namespace) -> dict:
    '''Generate the options dictionnary used in three-cad-viewer, based on cli options.'''

    hidden_buttons = []
    if args.ui_hide:
        hidden_buttons = args.ui_hide.split(',')
        if 'all' in hidden_buttons:
            hidden_buttons = [ 'axes', 'axes0', 'grid', 'ortho', 'more', 'help' ]

    return {
        'hideButtons': hidden_buttons,
        'glass': args.ui_glass,
        'theme': args.ui_theme,
        'control': 'trackball' if args.ui_trackball else 'orbit',
        'ortho': not args.ui_perspective,
        'grid': [ 'x' in args.ui_grid, 'y' in args.ui_grid, 'z' in args.ui_grid ] \
            if args.ui_grid else [ False, False, False ],
        'transparent': args.ui_transparent,
        'blackEdges': args.ui_black_edges
    }


def main() -> None:
    '''Main function, called when using the `cq-server` command.'''
    # pylint: disable=import-outside-toplevel

    parser = argparse.ArgumentParser()
    args = parse_args(parser)

    if args.version:
        print(f'CadQuery Server version: { cqs_version }')
        sys_exit()

    if not args.cmd or args.cmd not in [ 'run', 'build', 'info' ]:
        parser.print_help()
        sys_exit()

    ui_options = get_ui_options(args)

    if args.cmd == 'run':
        from .server import run

        run(args.port, ui_options)


if __name__ == '__main__':
    main()
