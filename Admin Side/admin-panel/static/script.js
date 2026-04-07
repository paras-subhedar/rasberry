const BASE_URL = "http://192.168.137.251:5000";
const API_KEY = "mysecret";

function openModal(id) {
    document.getElementById(id).style.display = "block";
}

function closeModal(id) {
    document.getElementById(id).style.display = "none";
}

function toggleFields(type) {
    document.getElementById('textField').style.display = (type === 'text') ? 'block' : 'none';
    document.getElementById('fileField').style.display = (type === 'image' || type === 'video') ? 'block' : 'none';
    document.getElementById('slideField').style.display = (type === 'slideshow') ? 'block' : 'none';
}

/* ================= LOAD NOTICES ================= */
function loadNotices() {
    fetch(BASE_URL + "/notices", {
        headers: { "API-KEY": API_KEY }
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById("viewSection").style.display = "block";
        let table = document.getElementById("tableBody");
        table.innerHTML = "";

        data.forEach(n => {
            let row = `
                <tr>
                    <td>${n[0]}</td>
                    <td>${n[1]}</td>
                    <td>${n[2]}</td>
                    <td>
                        <button onclick="editNotice(${n[0]}, '${n[1]}')">Edit</button>
                        <button onclick="deleteNotice(${n[0]})">Delete</button>
                    </td>
                </tr>
            `;
            table.innerHTML += row;
        });
    });
}

/* ================= ADD ================= */
document.getElementById("addForm").addEventListener("submit", function(e){
    e.preventDefault();

    let formData = new FormData(this);

    fetch(BASE_URL + "/upload", {
        method: "POST",
        headers: { "API-KEY": API_KEY },
        body: formData
    })
    .then(res => res.json())
    .then(() => {
        alert("Added!");
        closeModal("addModal");
        loadNotices();
    });
});

/* ================= DELETE ================= */
function deleteNotice(id) {
    if (!confirm("Delete this notice?")) return;

    fetch(BASE_URL + "/delete/" + id, {
        method: "DELETE",
        headers: { "API-KEY": API_KEY }
    })
    .then(() => loadNotices());
}

/* ================= UPDATE ================= */
function editNotice(id, title) {
    document.getElementById("updateId").value = id;
    document.getElementById("updateTitle").value = title;

    openModal("updateModal");
}

document.getElementById("updateForm").addEventListener("submit", function(e){
    e.preventDefault();

    let id = document.getElementById("updateId").value;

    let data = new FormData();
    data.append("title", document.getElementById("updateTitle").value);
    data.append("content", document.getElementById("updateContent").value);
    data.append("duration", document.getElementById("updateDuration").value);

    fetch(BASE_URL + "/update/" + id, {
        method: "POST",
        headers: { "API-KEY": API_KEY },
        body: data
    })
    .then(() => {
        alert("Updated!");
        closeModal("updateModal");
        loadNotices();
    });
});