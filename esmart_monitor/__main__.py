import argparse

from esmart_monitor.monitor import ESolarMonitor


def main() -> None:
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--port", type=str, required=True)

    args = argparser.parse_args()

    mon = ESolarMonitor(args.path)
    mon.run()


if __name__ == "__main__":
    main()
