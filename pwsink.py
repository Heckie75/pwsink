#!/usr/bin/python3
import argparse
import json
import subprocess
import sys
import time


class MyLogger():

    DEBUG = 0
    INFO = 1
    WARN = 2
    ERROR = 3

    LEVELS = {
        "DEBUG": DEBUG,
        "INFO": INFO,
        "WARN": WARN,
        "ERROR": ERROR
    }

    NAMES = ["DEBUG", "INFO", "WARN", "ERROR"]

    def __init__(self, level: int) -> None:
        self.level = level

    def error(self, s):

        self.log(MyLogger.LEVELS["ERROR"], s)

    def warning(self, s):

        self.log(MyLogger.LEVELS["WARN"], s)

    def info(self, s):

        self.log(MyLogger.LEVELS["INFO"], s)

    def debug(self, s):

        self.log(MyLogger.LEVELS["DEBUG"], s)

    def log(self, level, s):

        if level >= self.level:
            print(f"{MyLogger.NAMES[level]}\t{s}", file=sys.stderr, flush=True)


LOGGER = MyLogger(level=MyLogger.LEVELS["WARN"])


class BluetoothDevice():

    def __init__(self, address: str, name: str, connected: bool):

        self.id = address
        self.address = address
        self.name = name
        self.connected = connected

    @staticmethod
    def get_bluetooth_devices() -> 'list[BluetoothDevice]':

        def _parse(address: str, response: str) -> 'BluetoothDevice':

            name = None
            connected = False
            paired = False
            audio = False

            for line in response.splitlines():

                line = line.strip()
                if line.startswith("UUID: Audio Sink"):
                    audio = True
                if line.startswith("Name: "):
                    name = line[6:]
                if line == "Connected: yes":
                    connected = True
                if line == "Paired: yes":
                    paired = True

            if audio and paired:
                return BluetoothDevice(address=address, name=name, connected=connected)
            else:
                None

        response = subprocess.run(
            ['bluetoothctl', 'devices'], capture_output=True)
        devices_str = response.stdout.decode("utf8").splitlines()

        devices = list()
        for device in devices_str:
            address = device.split(" ")[1]
            response = subprocess.run(
                ['bluetoothctl', 'info', address], capture_output=True)
            device = _parse(address, response.stdout.decode("utf8"))
            if device:
                devices.append(device)

        if LOGGER.level == LOGGER.DEBUG:
            LOGGER.debug(
                f"known Bluetooth audio devices are: {', '.join(str(d) for d in devices)}")

        return devices

    @staticmethod
    def disconnect() -> 'list[BluetoothDevice]':

        disconnected = list()

        bt_devices = BluetoothDevice.get_bluetooth_devices()
        for device in bt_devices:
            if device.connected:
                LOGGER.debug(
                    f"disconnect Bluetooth device {device.name} ({device.address})")
                subprocess.run(['bluetoothctl', 'disconnect', device.address])
                disconnected.append(device)

        return disconnected

    @staticmethod
    def connect(label: str, reconnect: bool = False) -> 'BluetoothDevice | None':

        bt_devices = BluetoothDevice.get_bluetooth_devices()
        other_connected = False
        to_connect = None
        for device in bt_devices:
            if (label in device.address or label in device.name):
                if not device.connected or reconnect:
                    to_connect = device

            elif device.connected:
                other_connected = True

        if not to_connect:
            LOGGER.debug(
                "No need to connect Bluetooth devices since it is already connected.")
            return None

        if other_connected or reconnect:
            LOGGER.debug(
                "Disconnect all Bluetooth audio devices before connecting new one.")
            BluetoothDevice.disconnect()

        LOGGER.debug(
            f"Connect new Bluetooth audio device with address {to_connect.address}")
        subprocess.run(['bluetoothctl', 'connect', to_connect.address])

        return to_connect

    def to_dict(self) -> 'dict':

        return {
            "address": self.address,
            "name": self.name,
            "connected": self.connected
        }

    def to_human(self) -> 'dict':

        return f"\n  Name:        {self.name}\n  MAC-Address: {self.address}\n  Connected:   {str(self.connected)}\n"

    def __str__(self):

        return f"BluetoothDevice(address={self.address}, name={self.name}, connected={str(self.connected)})"


class Sink():

    WAIT_FOR_SINK = 0.5
    WAIT_FOR_SINK_TIMEOUT = 3

    def __init__(self, id: int, name: str, api: str, address: str, default: bool):

        self.id = id
        self.address = address
        self.name = name
        self.api = api
        self.default = default

    @staticmethod
    def get_pipewire_sinks() -> 'list[Sink]':

        def _get_default_sink_name(dump: dict) -> str:

            default = [d for d in pwdump if d["type"] ==
                       "PipeWire:Interface:Metadata" and d["props"]["metadata.name"] == "default"]
            if not default or "metadata" not in default[0]:
                return None

            meta = [m for m in default[0]["metadata"]
                    if m["key"] == "default.audio.sink"]
            if not meta or not "value" in meta[0] or not "name" in meta[0]["value"]:
                return None

            return meta[0]["value"]["name"]

        known_sinks = list()
        response = subprocess.run(["pw-dump"], capture_output=True)
        pwdump = json.loads(response.stdout.decode("utf8"))
        default_sink_name = _get_default_sink_name(pwdump)

        LOGGER.info(f"Current default sink is {default_sink_name}")

        for d in pwdump:

            if "info" not in d or "props" not in d["info"] or "media.class" not in d["info"]["props"] or not d["info"]["props"]["media.class"] == "Audio/Sink":
                continue

            sink = Sink(id=d["id"],
                        name=d["info"]["props"]["node.description"],
                        api=d["info"]["props"]["device.api"] if "device.api" in d["info"]["props"] else "",
                        address=d["info"]["props"]["api.bluez5.address"] if d["info"]["props"]["device.api"].startswith(
                            "bluez") else None,
                        default=("node.name" in d["info"]["props"] and d["info"]["props"]["node.name"] == default_sink_name))

            known_sinks.append(sink)

        if LOGGER.level == LOGGER.DEBUG:
            LOGGER.debug(
                f"Current known sinks are: {", ".join(str(s) for s in known_sinks)}")

        return known_sinks

    @staticmethod
    def get_default_pipewire_sink() -> 'Sink | None':

        sinks = [s for s in Sink.get_pipewire_sinks() if s.default]
        return sinks[0] if sinks else None

    @staticmethod
    def set_sink(label: str, retry: int = 1, timeout: float = 3.0, reconnect: bool = False) -> 'Sink | None':

        def _get_pipewire_sink_gracefully(label: str, timeout: float = Sink.WAIT_FOR_SINK + 0.1) -> Sink:

            start = time.time()
            now = start
            while (now <= start + timeout):

                sinks = [s for s in Sink.get_pipewire_sinks() if label ==
                         str(s.id) or label in s.name]
                if sinks:
                    LOGGER.info(f"Sink {sinks[0].name} ({sinks[0].id}) found.")
                    return sinks[0]

                LOGGER.warning(
                    f"Sink with label {label} not found. Wait 500ms ...")
                time.sleep(Sink.WAIT_FOR_SINK)
                now = time.time()

            LOGGER.error(f"Sink with label {label} finally not found.")
            return None

        devices = [d for d in BluetoothDevice.get_bluetooth_devices(
        ) if d.name.startswith(label) or d.address.startswith(label)]

        for i in range(retry):
            if devices:
                BluetoothDevice.connect(devices[0].address, reconnect)
                label = devices[0].name
                time.sleep(Sink.WAIT_FOR_SINK)

            sink = _get_pipewire_sink_gracefully(label, timeout=timeout)
            if sink:
                if not sink.default:
                    LOGGER.info(f"Set sink {sink.name} to be new default.")
                    subprocess.run(['wpctl', 'set-default', str(sink.id)])
                return sink

            reconnect = True

        return None

    def to_dict(self) -> dict:

        return {
            "id": self.id,
            "name": self.name,
            "api": self.api,
            "address": self.address,
            "default": self.default
        }

    def to_human(self) -> 'dict':

        s = [f"\n  Name:    {self.name}", f"  Api:     {self.api}"]
        if self.address:
            s.append(f"  Address: {self.address}")

        if self.default:
            s.append(f"  Default: {str(self.default)}")

        return "\n".join(s)

    def __str__(self) -> str:

        return f"Sink(id={self.id}, name={self.name}, api={self.api}, address={self.address}, default={str(self.default)})"


def print_status() -> None:

    pw_sinks = Sink.get_pipewire_sinks()
    pw_sinks.sort(key=lambda s: s.name)
    pw_sinks.sort(key=lambda s: not s.default)

    bt_devices = BluetoothDevice.get_bluetooth_devices()
    bt_devices.sort(key=lambda d: d.name)

    print("Pipewire sinks:")
    for sink in pw_sinks:
        print(sink.to_human())

    print("\nBluetooth devices:")
    for device in bt_devices:
        print(device.to_human())


def print_list() -> None:

    print("\n".join([str(s) for s in Sink.get_pipewire_sinks()]))
    print("\n".join([str(s) for s in BluetoothDevice.get_bluetooth_devices()]))


def print_json() -> None:

    all_devices = dict()
    all_devices["sinks"] = [s.to_ddict() for s in Sink.get_pipewire_sinks()]
    all_devices["bluez"] = [b.to_dict()
                            for b in BluetoothDevice.get_bluetooth_devices()]

    print(json.dumps(all_devices, indent=2))


def arg_parse(args: 'list[str]') -> dict:

    parser = argparse.ArgumentParser(
        prog='pwsink.py', description='Shell script to set pipewire sinks incl. bluetooth sinks')

    parser.add_argument(
        '-l', '--list', help='list audio sinks', action='store_true')
    parser.add_argument(
        '-s', '--sink', metavar="id or name of sink, mac-address or shortcut", help='name of address of sink', required=False)
    parser.add_argument(
        '-c', '--connect', metavar="name of device, mac-address or shortcut", help='connect bluetooth audio device by name or address', type=str)
    parser.add_argument(
        '-r', '--retry', help='max. retries to connect', type=int, default=1)
    parser.add_argument(
        '-d', '--disconnect', help='disconnect bluetooth audio devices', action='store_true')
    parser.add_argument(
        '-f', '--force', help='force reconnect bluetooth audio devices', action='store_true')
    parser.add_argument(
        '-j', '--json', help='list audio sinks in JSON format', action='store_true')
    parser.add_argument(
        '--log', help='print logging information', choices=MyLogger.NAMES)

    return parser.parse_args(args)


if __name__ == '__main__':

    args = arg_parse(sys.argv[1:])
    try:
        if args.log:
            LOGGER.level = MyLogger.NAMES.index(args.log)

        if args.connect:
            BluetoothDevice.connect(args.connect)

        elif args.disconnect:
            BluetoothDevice.disconnect()

        elif args.sink:
            Sink.set_sink(args.sink, args.retry,
                          timeout=Sink.WAIT_FOR_SINK_TIMEOUT, reconnect=args.force)

        elif args.json:
            print_json()

        elif args.list:
            print_list()

        else:
            print_status()

    except KeyboardInterrupt:
        pass
