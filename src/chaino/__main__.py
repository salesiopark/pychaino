"""
Chaino CLI entrypoint (__main__.py)

Usage:
  py -m chaino scan
  py -m chaino change <PORT> <NEW_ADDR>

Examples:
  py -m chaino scan
  py -m chaino change COM9 0x41
  py -m chaino change /dev/ttyACM0 0x41
"""

import argparse
import sys
from . import Chaino  # re-exported in __init__.py


def _cmd_scan(args) -> int:
    """
    Scan for Chaino MASTER devices on serial ports (CPython only).
    Chaino.scan() prints status for each detected port.
    """
    try:
        Chaino.scan()
        return 0
    except Exception as e:
        print(f"[ERROR] scan failed: {e}")
        return 1


def _cmd_change(args) -> int:
    """
    Connect to the MASTER on the given serial PORT and change the target
    slave I2C address to NEW_ADDR. This assumes firmware supports the
    'set_i2c_addr' function (e.g., func 201).
    """
    try:
        new_addr = int(args.new_addr, 0)
    except ValueError:
        print("[ERROR] new address must be 0xNN or a decimal integer.")
        return 2

    if not (0x08 <= new_addr <= 0x77):
        print("[ERROR] I2C address must be in the range of 0x08~0x77.")
        return 3

    try:
        # Note: We do not pass an old/current address here, by design.
        # The Chaino implementation should handle the current target address internally.
        master = Chaino(args.port)
        print( master.set_addr(new_addr) )  # firmware must implement this
        return 0
    except Exception as e:
        print(f"[ERROR] Failed to change I2C address: {e}")
        return 4


def main():
    parser = argparse.ArgumentParser(
        prog="chaino",
        description="Chaino CLI utility (scan / change)"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # scan
    p_scan = sub.add_parser("scan", help="scan Chaino MASTER (serial) devices")
    p_scan.set_defaults(func=_cmd_scan)

    # change <PORT> <NEW_ADDR>
    p_chg = sub.add_parser("change", help="change slave I2C address")
    p_chg.add_argument("port", help="serial port (e.g., COM9, /dev/ttyACM0)")
    p_chg.add_argument("new_addr", help="new address (e.g., 0x41 or 65)")
    p_chg.set_defaults(func=_cmd_change)

    args = parser.parse_args()
    rc = args.func(args)
    sys.exit(rc)


if __name__ == "__main__":
    main()
