function toggleTheme() {
    document.body.classList.toggle('dark-mode');
    const mode = document.body.classList.contains('dark-mode') ? "dark" : "light";
    localStorage.setItem("theme", mode);
}

window.onload = () => {
    if (localStorage.getItem("theme") === "dark") {
        document.body.classList.add("dark-mode");
    }
};
