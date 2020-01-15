import argparse
import logging

from esolar_modbus.server import run_server


def main() -> None:
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--esmart-port", type=str, required=True)
    argparser.add_argument("--modbus-host", type=str, required=True)
    argparser.add_argument("--modbus-port", type=int, required=True)
    argparser.add_argument('--debug', action='store_true')

    args = argparser.parse_args()

    logging.basicConfig()
    log = logging.getLogger()
    if args.debug:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    run_server(args.esmart_port, args.modbus_host, args.modbus_port)


if __name__ == "__main__":
    main()
