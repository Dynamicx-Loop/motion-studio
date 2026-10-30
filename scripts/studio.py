"""Launch persistent Motion Studio on loopback, using local assets only."""
import argparse
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from motion_studio.studio import Studio, StudioError
from motion_studio.studio.http import create_server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, default=Path('outputs/studio-state'))
    parser.add_argument('--port', type=int, default=8773)
    parser.add_argument('--history-root', type=Path, action='append', default=[],
                        help='Permit saved inspection registration beneath this root (repeatable)')
    parser.add_argument('--history', type=Path, action='append', default=[],
                        help='Register a saved inspection on startup (repeatable, within a permitted root)')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    try:
        studio = Studio(args.state, history_roots=tuple(args.history_root))
        for path in args.history:
            studio.register_history(path.name + ' · historical reference', path)
        with create_server(studio, port=args.port) as server:
            print(f'Motion Studio: http://127.0.0.1:{server.server_port}/', flush=True)
            print(f'State: {studio.roots.state}', flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
    except (StudioError, OSError) as error:
        parser.exit(1, f'Studio cannot start: {error}\n')


if __name__ == '__main__':
    main()
