const BASE_URL = "http://192.168.137.251:5000";
const API_KEY = "mysecret";

/* ================= MODAL CONTROL ================= */
function openModal(id) {
    document.getElementById(id).classList.add("show");
}

function closeModal(id) {
    document.getElementById(id).classList.remove("show");
}

/* ================= FIELD TOGGLE ================= */
function toggleFields(type) {
    document.getElementById('textField').style.display = (type === 'text') ? 'block' : 'none';
    document.getElementById('fileField').style.display = (type === 'image' || type === 'video') ? 'block' : 'none';
    document.getElementById('slideField').style.display = (type === 'slideshow') ? 'block' : 'none';
}

/* ================= LOAD NOTICES ================= */
function loadNotices() {
    fetch(BASE_URL + "/notices", {
        method: "GET",
        headers: { "API-KEY": API_KEY }
    })
    .then(res => res.json())
    .then(data => {

        document.getElementById("viewSection").style.display = "block";

        let table = document.getElementById("tableBody");
        table.innerHTML = "";

        data.forEach(n => {			
			let id = n[0];
			let title = n[1];
			let content = n[2];
			let media_type = n[3];
			let file_path = n[4];

			let contentHTML = "";
			let actionButtons = "";

			/* -------- CONTENT -------- */
			if (media_type === 'text') {
				contentHTML = `<span>${content || ''}</span>`;
			}

			else if (media_type === 'image') {
				contentHTML = `<img src="${BASE_URL}/${file_path}" style="width:100px;">`;
				actionButtons += `<button onclick="viewContent('image','${file_path}')">View</button>`;
			}

			else if (media_type === 'video') {
				contentHTML = `
					<div style="width:120px;height:80px;background:#111;color:white;
					display:flex;align-items:center;justify-content:center;">
					🎥 Video
					</div>`;
				actionButtons += `<button onclick="viewContent('video','${file_path}')">View</button>`;
			}

			else if (media_type === 'slideshow') {
				contentHTML = `<button onclick="viewContent('slideshow','${file_path}')">View Slides</button>`;
			}

			/* -------- ACTIONS -------- */
			actionButtons += `
				<button onclick="editNotice(${id}, '${title}')">Edit</button>
				<button onclick="deleteNotice(${id})">Delete</button>
			`;

			let row = `
			<tr>
				<td>${id}</td>
				<td>${title}</td>
				<td>${media_type}</td>
				<td>${contentHTML}</td>
				<td>${actionButtons}</td>
			</tr>
			`;

			table.innerHTML += row;			
        });
    })
    .catch(err => console.error("Error:", err));
}

/* ================= VIEW CONTENT ================= */
function viewContent(type, path) {
    let modal = document.getElementById("contentModal");
    let container = document.getElementById("contentContainer");

    container.innerHTML = "";

    /* -------- IMAGE -------- */
    if (type === "image") {
        container.innerHTML = `
            <img src="${BASE_URL}/${path}" 
                 style="max-width:100%; border-radius:8px;">
        `;
    }

    /* -------- VIDEO (LOAD ONLY ON CLICK) -------- */
    else if (type === "video") {
        container.innerHTML = `
            <video controls preload="metadata" style="width:100%">
                <source src="${BASE_URL}/${path}#t=1">
            </video>
        `;
    }

    /* -------- SLIDESHOW -------- */
    else if (type === "slideshow") {
        fetch(BASE_URL + "/slides?path=" + path)
        .then(res => res.json())
        .then(images => {

            container.innerHTML = `
                <div style="
                    display:grid;
                    grid-template-columns: repeat(auto-fill, minmax(150px,1fr));
                    gap:10px;
                ">
                    ${images.map(img => `
                        <img src="${BASE_URL}/${img}" 
                             style="width:100%; border-radius:6px;">
                    `).join('')}
                </div>
            `;
        });
    }

    openModal("contentModal");
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