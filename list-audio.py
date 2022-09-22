import vlc, subprocess

#CHARSET="cp1251"
CHARSET="utf8"

audio = "mmdevice"
mmdevice_name = "{15b13b9c-bcd3-4cfc-a29a-453944ab9865}"

audio = "waveout"
waveout_name = "4- USB Audio Device"

play_file="tada.m3u"

# conwert byte string to unicode string with given charset
def s(str, charset = CHARSET):
    if not str:
        return ""
    else:
        return str.decode(charset)

# print ouput devices in VLC
def vlc_enum_player_audio_devices(vlc_player, device_name, mmdevice_name):
    device = None
    out_devices = vlc_player.audio_output_device_enum()
    if not out_devices:
        die("No player output devices")
    print("Player output devices:")
    dev = out_devices
    while dev:
#        print(dev.contents._fields_)
        print(f"-- {s(dev.contents.device)} -- {s(dev.contents.description)}")
#        print(f"{s(dev['name'])} -- {s(dev['description'])}")
        if waveout_name and dev.contents.description and waveout_name in s(dev.contents.description):
            print(f">> waveout_name: {s(dev.contents.description)}")
            device = {
                "waveout": dev.contents.description,
                "mmdevice": dev.contents.device,
                "output": dev.contents.description,
            }
        elif mmdevice_name and dev.contents.device and mmdevice_name in s(dev.contents.device):
            print(f">> waveout_name: {s(dev.contents.device)}")
            device = {
                "waveout": dev.contents.description,
                "mmdevice": dev.contents.device,
                "output": dev.contents.device,
            }
        dev = dev.contents.next
#    vlc_player.audio_output_device_list_release()
    return device

vlc_obj = vlc.Instance(['--no-xlib'])
vlc_player = vlc_obj.media_player_new()
dev = vlc_enum_player_audio_devices(vlc_player, waveout_name, mmdevice_name)

if dev:
    cmd = [
        "C:/Program Files/VideoLAN/VLC/vlc.exe", 
        "--play-and-exit", 
        "--no-random", "--no-loop", "--no-repeat",
        "--audio", 
        "-A", audio, 
        f"--{audio}-audio-device={dev['output']}", 
        play_file
    ]
    subprocess.run(cmd)
else:
   print("Device not fouund")