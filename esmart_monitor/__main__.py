import argparse

from esmart_monitor.monitor import ESmartMonitor


def main() -> None:
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--port", type=str, required=True)

    args = argparser.parse_args()

    mon = ESmartMonitor(args.path)
    mon.run()


if __name__ == "__main__":
    main()
