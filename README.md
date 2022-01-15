# footron-controller

## Setting up env

Create a file in `~/.config/footron/env`:
```ini
FT_ROLLBAR=<rollbar token>
FT_MSG_URL=wss://<messaging server>/messaging/out/
```

## Adding web shell

Build footron-web-shell using `yarn dist --linux` and copy the AppImage output to a file at
`~/.local/share/footron/bin/footron-web-shell` on the target machine. You may have to create
parent directories if you haven't run the controller yet.

## Adding loading screen

Follow the instructions for adding the web shell but substitute `footron-loader` for
`footron-web-shell`.
