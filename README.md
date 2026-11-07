# pwsink - Audio Sink Setter with Bluetooth support

`pwsink.py` switches Linux PipeWire audio sinks, including ALSA and Bluetooth devices. `winsink.py` provides a separate Windows command-line tool for listing and switching Windows audio outputs, including Bluetooth devices.

```
usage: pwsink.py [-h] [-l] [-s name of sink, mac-address or shortcut] [-c name of sink, mac-address or shortcut] [-d] [-j]

Shell script to set pipewire sinks incl. bluetooth sinks

options:
  -h, --help            show this help message and exit
  -l, --list            list audio sinks
  -s name of sink, mac-address or shortcut, --sink name of sink, mac-address or shortcut
                        name of address of sink
  -c name of sink, mac-address or shortcut, --connect name of sink, mac-address or shortcut
                        connect bluetooth audio device by name or address
  -d, --disconnect      force disconnecting bluetooth audio devices
  -j, --json            list audio sinks in JSON format
```

## Requirements / pre-conditions

Internally, `pwsink` leverages the following tools:

1.  **Python 3.6 or newer**: Required to run either script.

The following tools are required for Linux `pwsink.py` only:

2.  **`bluez`**: This suite provides the fundamental Bluetooth tools and daemons. Specifically, `pwsink.py` utilizes the `bluetoothctl` command to:
    * List already paired A2DP Bluetooth devices.
    * Connect to these devices by either their name or MAC address.

3.  **`pw-dump`**: The PipeWire state dumper, used by `pwsink`.

4.  **`wpctl`**: The PipeWire control command-line interface, also employed by `pwsink`.

Windows `winsink.py` uses the built-in Windows Core Audio APIs through Python's `ctypes`; it does not require PipeWire, BlueZ, or additional Python packages. Pair Bluetooth devices in Windows before using the script.

## Windows

Run these commands from PowerShell or Command Prompt with Python installed.

### List outputs

```powershell
python winsink.py
Windows audio outputs:
  Lautsprecher (Realtek(R) Audio) | {0.0.0.00000000}.{7acbc977-1f99-4d33-9cc1-181735429404} | default: False
  Lautsprecher (Wohnzimmer) | {0.0.0.00000000}.{a89f2a67-3946-4019-8ebc-cb0247f1013c} | default: True

Paired Bluetooth audio devices:
  Jabra Evolve 75 | be1f4e81-852b-5b83-82fc-236d1189b7e2 | connected: False
  Jabra Evolve2 75 | 2dd4efce-5128-53ca-8431-5b6463d70a5a | connected: False
  Wohnzimmer | 6b073096-53f8-54a5-b143-e8ca0bd91b92 | connected: True
```

The output includes each active audio output's name and endpoint ID, whether it is the default, and detected Bluetooth audio devices. Use the displayed name or ID to select an output. Names must match exactly (case-insensitive); use the ID if a name is ambiguous.

### Set the default output

```powershell
py winsink.py --sink "Speakers"
py winsink.py --sink "<endpoint ID>"
```

For Bluetooth devices that are not active, the script requests a reconnection and retries. Set the number of connection attempts with `--retry` (default: `1`):

```powershell
py winsink.py --sink "Headphones" --retry 3
```

### JSON output and logging

```powershell
python winsink.py -j
{
  "sinks": [
    {
      "id": "{0.0.0.00000000}.{7acbc977-1f99-4d33-9cc1-181735429404}",
      "name": "Lautsprecher (Realtek(R) Audio)",
      "address": null,
      "default": false
    },
    {
      "id": "{0.0.0.00000000}.{a89f2a67-3946-4019-8ebc-cb0247f1013c}",
      "name": "Lautsprecher (Wohnzimmer)",
      "address": "6b073096-53f8-54a5-b143-e8ca0bd91b92",
      "default": true
    }
  ],
  "bluetooth": [
    {
      "id": "be1f4e81-852b-5b83-82fc-236d1189b7e2",
      "name": "Jabra Evolve 75",
      "connected": false
    },
    {
      "id": "2dd4efce-5128-53ca-8431-5b6463d70a5a",
      "name": "Jabra Evolve2 75",
      "connected": false
    },
    {
      "id": "6b073096-53f8-54a5-b143-e8ca0bd91b92",
      "name": "Wohnzimmer",
      "connected": true
    }
  ]
}
```

For debug logging:

```powershell
py winsink.py --list --log DEBUG
```

The JSON output contains `sinks` and `bluetooth` arrays. Log levels are `DEBUG`, `INFO`, `WARN`, and `ERROR`.

## Examples

### List sinks
You can list available audio sinks and paired Bluetooth devices using the following command:

```
$ ./pwsink.py 
Pipewire sinks:

  Name:    Built-in Audio Digital Stereo (HDMI)
  Api:     alsa
  Default: True

  Name:    Küche
  Api:     bluez5
  Address: XX:XX:XX:XX:XX:XX

Bluetooth devices:
  Name:        LE-Bose QC35 II
  MAC-Address: XX:XX:XX:XX:XX:XX
  Connected:   False

  Name:        Livingroom
  MAC-Address: XX:XX:XX:XX:XX:XX
  Connected:   False
```

### Set sink
This command sets the default audio sink. If the specified sink is a Bluetooth device and is not currently connected, the script will automatically initiate the connection before setting it as the default.

The parameter can represent the device name, MAC address or a shortcut.

#### Set sink by device name:
```
$ ./pwsink.py -s Livingroom
```

#### Set sink by MAC address:
```
$ ./pwsink.py -s XX:XX:XX:XX:XX:XX
```

#### Set sink by shortcut:
```
$ ./pwsink.py -s Livin
```
or
```
$ ./pwsink.py -s XX:XX:
```
or
```
$ ./pwsink.py -s USB
```
or
```
$ ./pwsink.py -s HDMI
```

### Connect bluetooth device
This command establishes a connection to a specified Bluetooth audio device. Note that the device must already be paired with your system. This command solely focuses on establishing the connection and does not set the device as the default audio sink. Typically, you would use the sink-switching command, which automatically connects to a Bluetooth device if it's not already connected. Furthermore, if necessary, the sink-switching command will first disconnect other active Bluetooth audio devices.

#### Connect by device name:
```
$ ./pwsink.py -c Livingroom
Attempting to connect to ....
...
Connection successful
```

#### Connect by MAC address:
```
$ ./pwsink.py -c XX:XX:XX:XX:XX:XX
Attempting to connect to ....
...
Connection successful
```

#### Connect by shortcut:
```
$ ./pwsink.py -c Livin
Attempting to connect to ....
...
Connection successful
```

### Disconnect bluetooth devices
This command disconnects all currently connected Bluetooth audio devices.
```
$ ./pwsink.py -d
Attempting to disconnect from ...
...
Successful disconnected
```

### Get output in JSON format
```
$ pwsink -j
{
  "sinks": [
    {
      "id": 76,
      "name": "Livingroom",
      "api": "bluez5",
      "address": "XX:XX:XX:XX:XX:XX",
      "default": true
    },
    {
      "id": 48,
      "name": "Aureon Dual USB Digital Stereo (IEC958)",
      "api": "alsa",
      "address": null,
      "default": false
    },
    {
      "id": 56,
      "name": "Built-in Audio Digital Stereo (HDMI)",
      "api": "alsa",
      "address": null,
      "default": false
    }
  ],
  "bluez": [
    {
      "address": "XX:XX:XX:XX:XX:XX",
      "name": "LE-Bose QC35 II",
      "connected": false
    },
    {
      "address": "XX:XX:XX:XX:XX:XX",
      "name": "Livingroom",
      "connected": true
    }
  ]
}
```


## FAQ
### Choppy sound
After updating to Ubuntu 24.04 I recognized that the Bluetooth audio stream was choppy. After some internet investigation I found the solution which is to change the following value:
```
pw-metadata -n settings 0 clock.force-quantum 16384
```

see also https://askubuntu.com/questions/1528042/choppy-sound-with-bluetooth-speaker-and-pipewire

Note that root priveledges are required for the folling steps.
To make it permanent do the following:

1. Copy default pipewire config file to `/etc/pipewire` if it is not already available there:
```
$ sudo -s
$ mkdir /etc/pipewire/
$ cp -av /usr/share/pipewire/pipewire.conf /etc/pipewire/
```

2. Change the value in `/etc/pipewire/pipewire.conf`
```
tbd.
```
