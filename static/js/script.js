document.addEventListener("DOMContentLoaded", function () {
    const menuButton = document.querySelector(".menu-button");
    const sidebar = document.querySelector(".sidebar");
    if (menuButton && sidebar) {
        menuButton.addEventListener("click", () => sidebar.classList.toggle("collapsed"));
    }
    const searchButton = document.querySelector(".search-box button");
    const searchInput = document.querySelector(".search-box input");
    if (searchButton && searchInput) {
        searchButton.addEventListener("click", function () {
            const q = searchInput.value.trim().toLowerCase();
            document.querySelectorAll(".book").forEach(book => {
                book.style.display = !q || book.innerText.toLowerCase().includes(q) ? "" : "none";
            });
        });
    }
});
