config = {
    "charset": "utf8",
#    "charset": "cp1251",

    "stats_file": "stats.json",
    "pause_seconds": 1,

#    "vlc_gui": True,
    "vlc_opts": [
        "--play-and-exit", 
        "--no-random", "--no-loop", "--no-repeat",
        "--audio", 
    ],

    "playlists": {
        "common": {
            "enabled": False,
            "dir": "media/common",
            "wildcards": [
                "*.wav",
                "*.mp3",
            ],
            "devices": [
            	"Realtek(R) Audio",
            ],
            "begin": {
                "subdir": "begin",
                "repeat": 1,
                "stat": False,
            },
            "end": {
                "subdir": "end",
                "repeat": 1,
                "stat": False,
            },
            "middle": {
                "subdir": "middle",
                "wildcards": [
                    "*.wav",
                ],
                "repeat": 2,
                "stat": True,
            },
        },
        "list-3": {
            "base": "common",
            "enabled": True,
            "dir": "media/list-3",
            "devices": [
                "5- USB Audio Device",
            ],
        },
        "list-4": {
            "base": "common",
            "enabled": True,
            "dir": "media/list-4",
            "devices": [
                "6- USB Audio Device",
            ],
        },
    },
}
