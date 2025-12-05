console.log("Faculty Invigilation System UI Loaded");

document.addEventListener("DOMContentLoaded", function () {
    const buttons = document.querySelectorAll("button");

    buttons.forEach(btn => {
        btn.addEventListener("click", function () {
            console.log("Button clicked:", btn.innerText);
        });
    });
});
