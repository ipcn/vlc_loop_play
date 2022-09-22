import sys, os, time, json, subprocess, glob

## pip install python-vlc
import vlc 

### pip install playsound==1.2.2
from playsound import playsound 

DEFAULT_CHARSET = "utf8"
from config import config

# show help message about usage
def usage():
    print("Usage:", sys.argv[0], "[<play_file>]", "[<max_count>]", "[<stats_file>]")

# show error message
def err(msg):
    print("ERROR:", msg)

# show error message and exit
def die(msg = None):
    err(msg)
    sys.exit(1)

# show error message with usage and exit
def die_usage(msg = None):
    err(msg)
    sys.exit(1)

# conwert byte string to unicode string with given charset
def s(str, charset = config.get("charset", DEFAULT_CHARSET)):
    if not str:
        return ""
    else:
        return str.decode(charset)

# get property following base chain
def get_base_prop(obj, prop, default):
    if not prop:
        return default
    visited = []
    while obj is not None:
        if prop in obj:
            return obj[prop]
        visited.append(obj)
        base_prop = obj.get("base")
        parent_obj = obj.get("parent")
        if base_prop and parent_obj is not None and base_prop in parent_obj:
            obj = parent_obj[base_prop]
        if not obj or obj in visited:
            break
    return default

# get properties chain following base chain
def get_chain_base_prop(obj, props, default):
    if not props or len(props) <= 0:
        return obj
    for prop in props:
        if obj is not None and prop in obj:
            obj = obj[prop]
        else:
            obj = get_base_prop(obj, prop, None)
            if obj is None: 
                return default
    return obj

# get properties chain following base chain
def get_chain_prop(obj, props, default):
    if not props or len(props) <= 0:
        return obj
    for prop in props:
        if obj is not None and prop in obj:
            obj = obj[prop]
        else:
            return default
    return obj

# set properties chain
def set_chain_prop(obj, props, val):
    if not props or len(props) <= 0:
        return None
    if obj is None:
        return None
    last_obj = obj
    last_prop = None
    for prop in props:
        if prop not in obj or obj[prop] is None:
            obj[prop] = {}
        last_obj = obj
        last_prop = prop
        obj = obj[prop]
    if last_prop:
        last_obj[last_prop] = val
    return last_obj

# load stats form given file or create empty
def load_stats(stats_file):
    stats = {}
    charset = config.get("charset", DEFAULT_CHARSET)
    try:
        if (os.path.exists(stats_file)):
            with open(stats_file, "r", encoding = charset) as f:
                    stats = json.load(f)
                    print("Stats loaded from:", stats_file)
        else:
            print("No stats file to load from:", stats_file)
    except Exception as e:
        err("Failed to load stats from:" + stats_file)
        err(str(e))
    return stats

# save stats to given file
def save_stats(stats, stats_file):
    charset = config.get("charset", DEFAULT_CHARSET)
    try:
        with open(stats_file, "w", encoding = charset) as f:
            json.dump(stats, f, indent = 4)
        print("Stats saved to:", stats_file)
    except Exception as e:
        err("Failed to save stats to:" + stats_file)
        err(str(e))
    return True

# initialize vlc 
def vlc_init():
    # setup environment
    """
        /* VLC does not change the thread locale, so gettext/libintil will use the
        * user default locale as reference. */
        /* gettext versions 0.18-0.18.1 will use the Windows Vista locale name
        * if the GETTEXT_MUI environment variable is set. If not set or if running
        * on Windows 2000/XP/2003 an hard-coded language ID list is used. This
        * putenv() call may become redundant with later versions of gettext. */
        putenv("GETTEXT_MUI=1");
    #ifdef TOP_BUILDDIR
        putenv("VLC_PLUGIN_PATH=Z:"TOP_BUILDDIR"/modules");
        putenv("VLC_DATA_PATH=Z:"TOP_SRCDIR"/share");
    #endif
    """

    argv = []
    argv += [
        "--media-library", 
        "--stats", 
        "--no-ignore-config",
    ]
    vlc_opts = config.get("vlc_opts")
    if (vlc_opts):
        argv += vlc_opts

    # create vlc instance
    vlc_obj = vlc.Instance(argv)
    #vlc_enumerate_audio_devices(vlc_obj)
    #vlc_list_audio_devices(vlc_obj)

    # show vlc gui
    show_gui = config.get("vlc_gui", False)
    if (show_gui):
#        res = vlc_obj.set_app_id ("org.VideoLAN.VLC", PACKAGE_VERSION, PACKAGE_NAME);
#        res = vlc_obj.set_user_agent ("VLC media player", "VLC/"PACKAGE_VERSION);
        res = vlc_obj.add_intf ("hotkeys,none");
        res = vlc_obj.add_intf ("globalhotkeys,none");
        res = vlc_obj.add_intf (None);

        if res != 0:
            err("Failed to start VLC window with code:" + str(res))
    return vlc_obj

# close vlc object
def vlc_close(vlc_obj):
    time.sleep(1)
#    vlc_obj.wait();
    if (vlc_obj):
        vlc_obj.release()

# make vlc player
def vlc_make_player(vlc_obj):
    vlc_player = vlc_obj.media_player_new()
    return vlc_player

# close vlc player
def vlc_close_player(vlc_player):
    if (vlc_player):
        vlc_player.release()

# get ouput devices in VLC
def vlc_get_devices(vlc_player):
    devices = {}
    out_devices = vlc_player.audio_output_device_enum()
    if not out_devices:
        die("No player output devices")
    print("Player output devices:")
    dev = out_devices
    while dev:
        mmdevice = s(dev.contents.device)
        waveout = s(dev.contents.description)
        print(f"-- {waveout} -- {mmdevice}")
        vlc_device = {
            "waveout": waveout,
            "mmdevice": mmdevice,
        }
        devices[waveout] = vlc_device
        dev = dev.contents.next
    return devices

# play in vlc player specified or current media source
def vlc_cmd_play(src, device):
    # prepare VLC command
    cmd = [
        "C:/Program Files/VideoLAN/VLC/vlc.exe", 
    ]
    vlc_opts = config.get('vlc_opts')
    if vlc_opts:
        cmd += vlc_opts

    # add device id
    if device:
        device_id = None
        for audio in ["mmdevice", "waveout"]:
            if audio in device and device[audio]:
                device_id = device[audio]
                break
        if not device_id:
            die("Not found audio device:" + str(device))
        cmd += [
            "-A", audio, 
            f"--{audio}-audio-device={device_id}", 
        ]

    # add source file
    cmd += [
        src
    ]

    # play file
    play_sec = 0
    print("Command:", cmd)
    subprocess.run(cmd)

    # return remaining seconds
    return play_sec 

# play in vlc player specified or current media source
def vlc_lib_play(vlc_obj, vlc_player, device, src = None):
    # set source file
    if (src):
        vlc_media = vlc_obj.media_new(src) 
        vlc_player.set_media(vlc_media) 
    # set output device
    if device:
        vlc_player.audio_output_device_set(None, device["mmdevice"])
    # start playing file
    play_ms = 0
    vlc_player.play()
    # wait for 1 seconds and get duration
    time.sleep(1)
    play_ms = vlc_player.get_length() 
    play_sec = play_ms // 1000 
    # return remaining seconds
    return play_sec 

# play in playsound
def playsound_play(src):
    # play file
    playsound(src) 
    # return remaining seconds
    play_sec = 0
    return play_sec

def get_matched_files(dir, wildcards):
    dir_files = set()
    for w in wildcards:
        files = glob.glob(dir + "/" + w, recursive = False)
        if files:
            dir_files.update(files)
    dir_files = list(dir_files)
    dir_files.sort()
    return dir_files

# choose next playlist stage
def next_stage(stage):
    if not stage:
        stage = "begin"
    elif stage == "begin":
        stage = "middle"
    elif stage == "middle":
        stage = "end"
    elif stage == "end":
        stage = None
    else:
        die("Unexpected playlist stage: " + stage)
    return stage

# set stage dependent state props
def set_state_stage(name, dev, dev_play, state, stage):
    state['stage'] = stage
    if not stage:
        return

    # propagate props brom base
    props = {
        "dir": ".", 
        "subdir": ".", 
        "wildcards": ["*"], 
        "repeat": 1, 
        "stat": False,
    }
    # create new stage dependent props
    stage_state = state['stages'].get(stage)
    if not stage_state:
        stage_state = {}
        state['stages'][stage] = stage_state
    # copy stage props from dev_play
    for prop in props.keys():
        stage_state[prop] = get_chain_base_prop(dev_play, [stage, prop], get_base_prop(dev_play, prop, props[prop]))
    # collect files for current stage
    dir_path = stage_state["dir"] + "/" + stage_state["subdir"]
    stage_state["dir_path"] = dir_path
    stage_state["files"] = get_matched_files(dir_path, stage_state["wildcards"])
    return stage_state

def init_state(vlc_obj, vlc_devices, name, dev, dev_play):
    # create state
    stage = "begin"
    state = {
        "stage": stage,
        "stages": {},
        "player": None,
    }
    # create palyer
    player = vlc_make_player(vlc_obj)
    if not player:
        die(f"failed to create palyer for playlist: {name}/{stage}/{dev}")
    state["player"] = player;
    # set stage dependent props
    set_state_stage(name, dev, dev_play, state, stage)
#    dev_play['state'] = state
    return state

def process_state(vlc_obj, vlc_devices, name, dev, dev_play, state, stats):
    # check if empty stage for finished task
    stage = state.get("stage")
    if not stage:
        return False

    # get current stage props
    stage_state = state['stages'].get(stage)
    if not stage_state:
        die("Missing playlist stage data")

    # get current files
    files = stage_state.get("files")
    file = None

    # check current file
    file_idx = stage_state.get("file_idx", -1)
    if file_idx >= 0:
        started = stage_state.get("started")
        duration = stage_state.get("duration")
        elapsed = int(time.time() - started)
        if elapsed < duration:
            # still playing, return
            return True
        else:
            print(f"{name}/{stage}/{dev}: file finished: {files[file_idx]}")
            file_idx += 1
        
    # choose next file to play
    if files and 0 <= file_idx and file_idx < len(files):
        file = files[file_idx]
    else:
        # if finished stage files, update stats
        if files and len(files) > 0 and len(files) <= file_idx:
            repeat =  get_chain_prop(dev_play, [stage, 'repeat'], get_chain_prop(dev_play, ['repeat'], 1))
            count = stage_state.get('count', 0) + 1
            stage_state['count'] = count
            print(f"{name}/{stage}/{dev}: playlist stage finished: {count} of {repeat} times")
            needs_stats = get_chain_prop(dev_play, [stage, 'stat'], get_chain_prop(dev_play, ['stat'], False))
            if needs_stats and stats is not None:
                stats_count = get_chain_prop(stats, [name, stage, 'count'], 0)
                stats_count += 1
                set_chain_prop(stats, [name, stage, 'count'], stats_count)
            # check if repeat required from first file
            if repeat > count:
                print(f"{name}/{stage}/{dev}: playlist stage started")
                file_idx = 0
                file = files[file_idx]
            else:
                file_idx = -1
                files = None

        # switch to bext stage
        if file_idx < 0:
#            files = None
            while not files or len(files) <= 0:
                print(f"{name}/{stage}/{dev}: no files to play")
                stage = next_stage(stage)
                if (not stage):
                    break
                stage_state = set_state_stage(name, dev, dev_play, state, stage)
                files = stage_state.get("files")

            # for no more files finish playing
            if not files or len(files) <= 0:
                print(f"{name}/{dev}: all stages finished")
                vlc_close_player(state["player"])
                state["player"] = None
                return False

            # found files, start from first
            print(f"{name}/{stage}/{dev}: playslist stage started")
            file_idx = 0 
            file = files[file_idx]

    # start playing current file
    #    play_seconds = playsound_play(play_file)
    #    play_seconds = vlc_cmd_play(play_file, device)
    print(f"{name}/{stage}/{dev}: play file: {file}")
    play_seconds = vlc_lib_play(vlc_obj, state["player"], vlc_devices[dev], file)
#    print("Play duration:", play_seconds + 1, "seconds")
    # wait for play to finish
    stage_state["file_idx"] = file_idx
#    stage_state["count"] = 0
    stage_state["started"] = time.time()
    stage_state["duration"] = play_seconds
    return True

# main program
def main():
    # check command line args
    argc = len(sys.argv)
    #if argc <= 1:
    #    die_usage("Specify file name to play")
    if argc > 1:
        config['play_file'] = sys.argv[1]
    if argc > 2:
        config['max_count'] = sys.argv[2]
    if argc > 3:
        die_usage("Too many command line argments: " +  argc)
        
    # load stats
    stats = load_stats(config['stats_file'])
    print("Loaded stats:", stats)

    # set initial counter
    count = stats.get("count", 0)
    print("Initial count:", count)

    # get playlists
    playlists = config.get("playlists", {})
    names = playlists.keys()
    if len(names) <= 0:
        die("No playlists defined in configs")
    # app parremn links to enable base prop traveling
    for name in names:
        if playlists[name]:
            playlists[name]['parent'] = playlists
    # reduce to only enabled playlists
    names = [name for name in names if playlists[name] and playlists[name].get("enabled", True)]
    if len(names) <= 0:
        die("No playlists enabled in configs")

    init_dev_plays = {}
    for name in names:
        devs = playlists[name].get("devices")
        if devs and len(devs) > 0:
            for dev in devs:
                if dev not in init_dev_plays:
                    init_dev_plays[dev] = name
                else:
                    die(f"Overlapped devices enabled in config: {name}/{dev}")
    if len(init_dev_plays) <= 0:
        die("No audio devices enabled in configs")

    # create vlc player
    vlc_obj = vlc_init()
    vlc_player = vlc_make_player(vlc_obj)
    vlc_devices = vlc_get_devices(vlc_player)

    dev_plays = {}
    for dev in init_dev_plays.keys():
        matched = [vlc_dev_name for vlc_dev_name in vlc_devices.keys() if (dev in vlc_dev_name)]
        if len(matched) <= 0:
            die("No audio device found: " + dev)
        if len(matched) > 1:
            die("Vague audio device name: " + dev)
        vlc_dev_name = matched[0]
        if vlc_dev_name in dev_plays:
            die("Ambigous audio device name: " + dev)
        dev_plays[vlc_dev_name] = init_dev_plays[dev]
    if len(dev_plays) <= 0:
        die("No matched devices enabled in configs")

    # process running playlists by stagges
    pause_seconds = config.get("pause_seconds", 0)
    states = {}
    while True:
        running = 0
        for dev, name in dev_plays.items():
            state_name = f"{name}/{dev}"
            print(f">> check: {name}/{dev}")
            dev_play = playlists[name]
            state = states.get(state_name)
            if not state:
                state = init_state(vlc_obj, vlc_devices, name, dev, dev_play)
                states[state_name] = state
            if process_state(vlc_obj, vlc_devices, name, dev, dev_play, state, stats):
                running += 1
        if running <= 0:
            break
        if pause_seconds:
            print("Pause:", pause_seconds, "seconds")
            time.sleep(pause_seconds)

    # close vlc instance
    if (vlc_obj):
        vlc_close(vlc_obj)

    # save stats
#    stats["count"] = count
    print("Final stats:", stats)
    save_stats(stats, config['stats_file'])

# run main script
main()
