// Use the local API during development. Replace with the deployed Render URL later.
const API_BASE_URL = "http://127.0.0.1:8001";

const taskForm = document.getElementById("task-form");
const titleInput = document.getElementById("title");
const descriptionInput = document.getElementById("description");
const taskList = document.getElementById("task-list");
const formMessage = document.getElementById("form-message");
const listMessage = document.getElementById("list-message");
const refreshButton = document.getElementById("refresh-button");
const addButton = document.getElementById("add-button");

function setMessage(element, text, type = "") {
    element.textContent = text;
    element.className = `message ${type}`.trim();
}

async function apiRequest(path, options = {}) {
    const url = `${API_BASE_URL.replace(/\/$/, "")}${path}`;
    const response = await fetch(url, {
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {}),
        },
        ...options,
    });

    if (response.status === 204) {
        return null;
    }

    let payload = null;
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
        payload = await response.json();
    } else {
        const text = await response.text();
        payload = text ? { message: text } : null;
    }

    if (!response.ok) {
        const message = (payload && (payload.error || payload.message)) || `HTTP ${response.status}`;
        throw new Error(message);
    }

    return payload;
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}
function formatDate(value) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
}

function renderTasks(tasks) {
    taskList.innerHTML = "";

    if (!tasks || tasks.length === 0) {
        const empty = document.createElement("li");
        empty.className = "empty-state";
        empty.textContent = "Chưa có công việc nào.";
        taskList.appendChild(empty);
        return;
    }

    tasks.forEach((task) => {
        const item = document.createElement("li");
        item.className = "task-item";
        item.dataset.id = task.id;

        const isDone = task.status === "done";
        item.innerHTML = `
            <h3 class="task-title">${escapeHtml(task.title || "")}</h3>
            <p class="task-description">${escapeHtml(task.description || "")}</p>
            <div class="task-meta">
                <span class="status ${escapeHtml(task.status || "pending")}">${escapeHtml(task.status || "pending")}</span>
                <span>${escapeHtml(formatDate(task.created_at))}</span>
            </div>
            <div class="task-actions">
                <button type="button" class="mark-done" ${isDone ? "disabled" : ""}>Mark done</button>
                <button type="button" class="delete danger">Delete</button>
            </div>
        `;

        const markDoneButton = item.querySelector(".mark-done");
        const deleteButton = item.querySelector(".delete");

        markDoneButton.addEventListener("click", async () => {
            try {
                markDoneButton.disabled = true;
                await apiRequest(`/tasks/${encodeURIComponent(task.id)}`, {
                    method: "PUT",
                    body: JSON.stringify({ status: "done" }),
                });
                setMessage(listMessage, "Đã cập nhật trạng thái công việc.", "success");
                await loadTasks();
            } catch (error) {
                setMessage(listMessage, `Lỗi: ${error.message}`, "error");
                markDoneButton.disabled = isDone;
            }
        });

        deleteButton.addEventListener("click", async () => {
            if (!window.confirm("Bạn có chắc muốn xóa công việc này?")) {
                return;
            }
            try {
                deleteButton.disabled = true;
                await apiRequest(`/tasks/${encodeURIComponent(task.id)}`, {
                    method: "DELETE",
                });
                setMessage(listMessage, "Đã xóa công việc.", "success");
                await loadTasks();
            } catch (error) {
                setMessage(listMessage, `Lỗi: ${error.message}`, "error");
                deleteButton.disabled = false;
            }
        });

        taskList.appendChild(item);
    });
}

async function loadTasks() {
    setMessage(listMessage, "Đang tải danh sách...");
    try {
        const data = await apiRequest("/tasks", { method: "GET" });
        renderTasks(data.tasks || []);
        setMessage(listMessage, `Đã tải ${data.count || 0} công việc.`, "success");
    } catch (error) {
        renderTasks([]);
        setMessage(listMessage, `Không thể tải danh sách: ${error.message}`, "error");
    }
}

taskForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    setMessage(formMessage, "");

    const title = titleInput.value.trim();
    const description = descriptionInput.value.trim();

    if (!title) {
        setMessage(formMessage, "Tiêu đề là bắt buộc.", "error");
        return;
    }

    addButton.disabled = true;
    try {
        await apiRequest("/tasks", {
            method: "POST",
            body: JSON.stringify({ title, description }),
        });
        taskForm.reset();
        setMessage(formMessage, "Đã thêm công việc.", "success");
        await loadTasks();
    } catch (error) {
        setMessage(formMessage, `Lỗi: ${error.message}`, "error");
    } finally {
        addButton.disabled = false;
    }
});

refreshButton.addEventListener("click", loadTasks);

window.addEventListener("DOMContentLoaded", loadTasks);
