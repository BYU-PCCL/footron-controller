/** @type {HTMLVideoElement} */
const videoElement = document.querySelector("#video")
const stateIconContainer = document.querySelector("#state-icon-container")

const SEEK_EPSILON_S = 5;

document.addEventListener("DOMContentLoaded", () => {
    const urlParams = new URLSearchParams(window.location.search);
    const videoId = urlParams.get('id');
    videoElement.src = urlParams.get('url');
    // noinspection JSIgnoredPromiseFromCall
    videoElement.poster = urlParams.get('posterUrl')
    videoElement.play()

    const client = new FootronMessaging.Messaging();

    const play = () => {
        videoElement.play()
        stateIconContainer.style.opacity = "";
    }

    const pause = () => {
        videoElement.pause()
        stateIconContainer.style.opacity = "1";
    }

    const messageHandler = (message) => {
        if (message.type === "toggle") {
            let state;
            if (videoElement.paused) {
                play()
                state = "playing";
            } else {
                pause()
                state = "paused";
            }

            client.sendMessage({type: "state", state});
        } else if (message.type === "scrub") {
            const newTime = videoElement.duration * message.progress;
            if (Math.abs(videoElement.currentTime - newTime) > SEEK_EPSILON_S) {
                videoElement.currentTime = newTime;
            }
        } else if (message.type === "jump") {
            videoElement.currentTime += message.delta;
        }
    }

    const connectionHandler = (connection) => {
        connection.addCloseListener(play)
    }

    client.mount();
    client.addMessageListener(messageHandler);

    client.addConnectionListener(connectionHandler)

    setInterval(() => {
        if (!videoElement.duration || !videoElement.currentTime) {
            return
        }

        const endTime = (Date.now() / 1000) + (videoElement.duration - videoElement.currentTime);

        fetch('http://localhost:8000/current', {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({"id": videoId, "end_time": Math.floor(endTime * 1000)}),
        })

        client.sendMessage({"type": "progress", "progress": videoElement.currentTime / videoElement.duration, "duration": videoElement.duration})
    }, 500)
});
