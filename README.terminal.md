# Windows Terminal

設定を開いて、

"profiles" の配列に次のような設定を入れておく。

<br>

```json
{
    "commandline": "wsl -e /usr/bin/telnet 192.168.122.212 5001",
    "hidden": false,
    "name": "telnet5001"
},
{
    "commandline": "wsl -e /usr/bin/telnet 192.168.122.212 5005",
    "hidden": false,
    "name": "telnet5002"
},
{
    "commandline": "wsl -e /usr/bin/telnet 192.168.122.212 5001",
    "hidden": false,
    "name": "telnet5003"
},
...

```

<br>
