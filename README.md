# pwsink - Pipewire-Sink-Setter with Bluetooth support

`pwsink` is a command-line tool that simplifies switching audio sinks. It supports both ALSA devices and Bluetooth audio sinks, automatically connecting to previously paired Bluetooth devices for seamless audio output redirection.

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

1.  **`bluez`**: This suite provides the fundamental Bluetooth tools and daemons. Specifically, `pwsink` utilizes the `bluetoothctl` command to:
    * List already paired A2DP Bluetooth devices.
    * Connect to these devices by either their name or MAC address.

2.  **`pw-dump`**: The PipeWire state dumper, used by `pwsink`.

3.  **`wpctl`**: The PipeWire control command-line interface, also employed by `pwsink`.

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
