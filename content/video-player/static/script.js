/** @type {HTMLVideoElement} */
const videoElement = document.querySelector("#video")

document.addEventListener("DOMContentLoaded", () => {
    const urlParams = new URLSearchParams(window.location.search);
    videoElement.src = urlParams.get('url');
    // noinspection JSIgnoredPromiseFromCall
    videoElement.play()
});