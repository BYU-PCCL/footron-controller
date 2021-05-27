/** @type {HTMLVideoElement} */
const videoElement = document.querySelector("#video")

document.addEventListener("DOMContentLoaded", () => {
    const urlParams = new URLSearchParams(window.location.search);
    videoElement.src = urlParams.get('url');
    // noinspection JSIgnoredPromiseFromCall
    videoElement.play()

    setInterval(() => {
        if (!videoElement.duration || !videoElement.currentTime) {
            return
        }

        const endTime = (Date.now() / 1000) + (videoElement.duration - videoElement.currentTime);

        fetch('http://localhost:5000/current-app', {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({"end_time": Math.floor(endTime)}),
        })
    }, 500)
});