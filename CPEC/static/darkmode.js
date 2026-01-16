function toggleDarkMode() {
    document.body.classList.toggle("dark-mode");

    if (document.body.classList.contains("dark-mode")) {
        localStorage.setItem("modo", "dark");
    } else {
        localStorage.setItem("modo", "light");
    }
}

/* Mantém o modo após recarregar */
window.onload = () => {
    const modo = localStorage.getItem("modo");
    if (modo === "dark") {
        document.body.classList.add("dark-mode");
    }
};
