# Setting up base Chrome profile

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
