/** @type {HTMLVideoElement} */
const videoElement = document.querySelector("#video")

document.addEventListener("DOMContentLoaded", () => {
    const urlParams = new URLSearchParams(window.location.search);
    const videoId = urlParams.get('id');
    videoElement.src = urlParams.get('url');
    // noinspection JSIgnoredPromiseFromCall
    videoElement.poster = urlParams.get('posterUrl')
    videoElement.play()

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
            body: JSON.stringify({"id": videoId, "end_time": Math.floor(endTime)}),
        })
    }, 500)
});
