# footron-controller

## Setting up Rollbar

Create a file in `~/.config/footron/env`:
```ini
FT_ROLLBAR=<rollbar token>
```

## Setting up base Chrome profile

1. Open Chrome with a new profile:
    ```sh
    google-chrome --user-data-dir=/tmp/base-chrome-profile
    ```
2. Install the
   [Just Black theme](https://chrome.google.com/webstore/detail/just-black/aghfnjkcakhmadgdomlmlhhaocbkloab?hl=en-US)
3. Clear browsing data
4. ```sh
   cd /tmp/base-chrome-profile
    ```
5. Remove everything except `Default/`, `'Local State'`, and `'Webstore Downloads'`
6. Copy to `/home/footron/.local/share/footron/base-chrome-profile` on the host machine

## Adding web shell

Build footron-web-shell using `yarn dist --linux` and copy the AppImage output to a file at
`~/.local/share/footron/bin/footron-web-shell` on the target machine. You may have to create
parent directories if you haven't run the controller yet.

## Adding loading screen

Follow the instructions for adding the web shell but substitute `footron-loader` for
`footron-web-shell`.