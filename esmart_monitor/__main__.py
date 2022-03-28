import argparse
import logging

from esmart_monitor.monitor import ESmartMonitor


def main() -> None:
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--port", type=str, required=True)
    argparser.add_argument("--device-addr", type=int, required=True)
    argparser.add_argument('--debug', action='store_true')

    args = argparser.parse_args()

    logging.basicConfig()
    log = logging.getLogger()
    if args.debug:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    mon = ESmartMonitor(args.port, args.device_addr)
    mon.run()


if __name__ == "__main__":
    main()
