/**
 * TaskPilot frontend — API layer connects to Flask backend with session cookies.
 */
async function apiRequest(url, options = {}) {
  const headers = { ...options.headers };
  if (options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  const res = await fetch(url, {
    ...options,
    headers,
    credentials: "same-origin",
  });
  let data = {};
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { error: text || "Invalid server response" };
    }
  }
  if (res.status === 401) {
    window.location.href = "/login/";
    throw new Error("Please sign in again.");
  }
  if (!res.ok) {
    throw new Error(data.error || `Request failed (${res.status})`);
  }
  return data;
}

const API = {
  health: () => apiRequest("/api/health"),
  config: () => apiRequest("/api/config"),
  tasks: () => apiRequest("/api/tasks"),
  createTask: (body) => apiRequest("/api/tasks", { method: "POST", body: JSON.stringify(body) }),
  updateTask: (id, body) =>
    apiRequest(`/api/tasks/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteTask: (id) => apiRequest(`/api/tasks/${id}`, { method: "DELETE" }),
  dashboard: () => apiRequest("/api/dashboard"),
  chat: (message) =>
    apiRequest("/api/chat", { method: "POST", body: JSON.stringify({ message }) }),
  chatHistory: () => apiRequest("/api/chat/history"),
  recalculate: () => apiRequest("/api/tasks/recalculate", { method: "POST" }),
  applySuggestions: () => apiRequest("/api/tasks/apply-suggestions", { method: "POST" }),
  seed: (replace = true) =>
    apiRequest("/api/seed-demo", {
      method: "POST",
      body: JSON.stringify({ replace }),
    }),
  team: () => apiRequest("/api/team"),
  addTeam: (body) => apiRequest("/api/team", { method: "POST", body: JSON.stringify(body) }),
  removeTeam: (id) => apiRequest(`/api/team/${id}`, { method: "DELETE" }),
  teamMessages: (since = 0) =>
    apiRequest(since ? `/api/team/messages?since=${since}` : "/api/team/messages"),
  sendTeamMessage: (content) =>
    apiRequest("/api/team/messages", {
      method: "POST",
      body: JSON.stringify({ content }),
    }),
  activity: () => apiRequest("/api/activity"),
  explain: (id) => apiRequest(`/api/priority/${id}`),
};

let state = {
  tasks: [],
  stats: null,
  connected: false,
  currentUser: "",
  boardMode: "list",
  teamMembers: [],
  lastTeamMsgId: 0,
  teamPollTimer: null,
};

function setConnectionStatus(ok, detail = "") {
  state.connected = ok;
  const badge = document.getElementById("connectionBadge");
  if (!badge) return;
  badge.textContent = ok ? "Connected" : "Offline";
  badge.className = `badge ${ok ? "badge-live" : "badge-offline"}`;
  badge.title = detail || (ok ? "Backend API reachable" : "Cannot reach server");
}

function showToast(message, extraClass = "") {
  const toast = document.getElementById("appToast");
  if (!toast) return;
  toast.textContent = message;
  toast.className = `app-toast visible${extraClass ? ` ${extraClass}` : ""}`;
  setTimeout(() => toast.classList.remove("visible", "team-toast"), 5000);
}

function showError(message) {
  console.error(message);
  showToast(message);
  if (!document.getElementById("appToast")) alert(message);
}

function priorityClass(score) {
  if (score >= 75) return "critical";
  if (score >= 55) return "high";
  if (score >= 35) return "medium";
  return "low";
}

function priorityLabel(score) {
  return priorityClass(score).charAt(0).toUpperCase() + priorityClass(score).slice(1);
}

function formatStatus(s) {
  return s.replace(/_/g, " ");
}

function renderMarkdownLite(text) {
  return String(text)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br>");
}

function addMessage(role, content) {
  const el = document.getElementById("chatMessages");
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.innerHTML = role === "assistant" ? renderMarkdownLite(content) : escapeHtml(content);
  el.appendChild(div);
  el.scrollTop = el.scrollHeight;
}

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

function getFilteredTasks() {
  const search = document.getElementById("taskSearch")?.value.toLowerCase() || "";
  const statusFilter = document.getElementById("filterStatus")?.value || "";
  let tasks = [...state.tasks];
  if (search) {
    tasks = tasks.filter(
      (t) =>
        t.title.toLowerCase().includes(search) ||
        (t.description || "").toLowerCase().includes(search)
    );
  }
  if (statusFilter) tasks = tasks.filter((t) => t.status === statusFilter);
  return tasks;
}

function setBoardMode(mode) {
  state.boardMode = mode;
  const list = document.getElementById("taskList");
  const kanban = document.getElementById("kanbanBoard");
  document.getElementById("btnBoardList")?.classList.toggle("active", mode === "list");
  document.getElementById("btnBoardKanban")?.classList.toggle("active", mode === "kanban");
  if (list) list.classList.toggle("hidden", mode !== "list");
  if (kanban) kanban.classList.toggle("hidden", mode !== "kanban");
  if (mode === "kanban") renderKanban();
  else renderTasks();
}

function renderKanban() {
  const board = document.getElementById("kanbanBoard");
  if (!board) return;
  const cols = [
    { id: "todo", label: "To Do" },
    { id: "in_progress", label: "In Progress" },
    { id: "blocked", label: "Blocked" },
    { id: "done", label: "Done" },
  ];
  const tasks = getFilteredTasks();
  board.innerHTML = cols
    .map((col) => {
      const colTasks = tasks.filter((t) => t.status === col.id);
      const cards = colTasks
        .map(
          (t) => `
        <div class="kanban-card" draggable="true" data-id="${t.id}" data-status="${col.id}">
          <h5>#${t.id} ${escapeHtml(t.title)}</h5>
          <span class="priority-pill ${priorityClass(t.priority_score)}">${t.priority_score}</span>
        </div>`
        )
        .join("");
      return `
      <div class="kanban-col" data-status="${col.id}">
        <div class="kanban-col-head">${col.label} (${colTasks.length})</div>
        <div class="kanban-col-body" data-drop-status="${col.id}">${cards || '<span style="font-size:0.75rem;color:var(--text-muted)">Drop here</span>'}</div>
      </div>`;
    })
    .join("");

  board.querySelectorAll(".kanban-card").forEach((card) => {
    card.addEventListener("dragstart", (e) => {
      e.dataTransfer.setData("text/plain", card.dataset.id);
    });
    card.addEventListener("dblclick", () => {
      const t = state.tasks.find((x) => x.id === parseInt(card.dataset.id, 10));
      if (t) openTaskModal(t);
    });
  });

  board.querySelectorAll(".kanban-col-body").forEach((zone) => {
    zone.addEventListener("dragover", (e) => {
      e.preventDefault();
      zone.classList.add("drag-over");
    });
    zone.addEventListener("dragleave", () => zone.classList.remove("drag-over"));
    zone.addEventListener("drop", async (e) => {
      e.preventDefault();
      zone.classList.remove("drag-over");
      const id = parseInt(e.dataTransfer.getData("text/plain"), 10);
      const newStatus = zone.dataset.dropStatus;
      const task = state.tasks.find((t) => t.id === id);
      if (!task || task.status === newStatus) return;
      try {
        await API.updateTask(id, { status: newStatus });
        await refresh();
        renderKanban();
      } catch (err) {
        showError(err.message);
      }
    });
  });
}

async function renderActivity() {
  const ul = document.getElementById("activityFeed");
  if (!ul) return;
  try {
    const { activity } = await API.activity();
    if (!activity?.length) {
      ul.innerHTML = '<li class="empty-state" style="list-style:none">No activity yet — create or update tasks</li>';
      return;
    }
    const labels = {
      created_task: "created task",
      updated_task: "updated task",
      updated_status: "changed status",
      deleted_task: "deleted task",
      demo_data: "loaded demo data",
      team_join: "team",
      team_leave: "team",
      team_message: "team chat",
    };
    ul.innerHTML = activity
      .slice()
      .reverse()
      .map((a) => {
        const verb = labels[a.action] || a.action;
        return `<li><strong>${escapeHtml(a.actor_name)}</strong> ${verb}: ${escapeHtml(a.detail || "")}<time>${formatTeamTime(a.created_at)}</time></li>`;
      })
      .join("");
  } catch {
    ul.innerHTML = "";
  }
}

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("taskpilot-theme", theme);
}

function initTheme() {
  const saved = localStorage.getItem("taskpilot-theme") || "dark";
  applyTheme(saved);
}

function toggleTheme() {
  const next = document.documentElement.getAttribute("data-theme") === "light" ? "dark" : "light";
  applyTheme(next);
}

function renderTeamMessageHtml(content) {
  let safe = escapeHtml(content);
  const names = state.teamMembers.map((m) => m.name).filter(Boolean);
  names.sort((a, b) => b.length - a.length);
  names.forEach((name) => {
    const re = new RegExp(`@${name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, "gi");
    safe = safe.replace(re, `<span class="mention">@${escapeHtml(name)}</span>`);
  });
  return safe;
}

function renderTasks(highlightId) {
  if (state.boardMode === "kanban") {
    renderKanban();
    return;
  }
  const list = document.getElementById("taskList");
  const tasks = getFilteredTasks();

  if (!tasks.length) {
    list.innerHTML =
      '<div class="empty-state">No tasks yet. Use <strong>+ New Task</strong> or chat: "add task Build login page urgent"</div>';
    return;
  }

  list.innerHTML = tasks
    .map((t) => {
      const pc = priorityClass(t.priority_score);
      const dl = t.deadline || t.suggested_deadline;
      return `
        <article class="task-card ${highlightId === t.id ? "highlight" : ""}" data-id="${t.id}">
          <div class="task-card-head">
            <h4>#${t.id} ${escapeHtml(t.title)}</h4>
            <span class="priority-pill ${pc}">${priorityLabel(t.priority_score)} ${t.priority_score}</span>
          </div>
          ${t.description ? `<p style="margin:0.4rem 0 0;font-size:0.8rem;color:var(--text-muted)">${escapeHtml(t.description.slice(0, 120))}</p>` : ""}
          <div class="task-meta">
            <span class="status-dot status-${t.status}">${formatStatus(t.status)}</span>
            ${dl ? `<span>Due ${dl}${!t.deadline && t.suggested_deadline ? " (suggested)" : ""}</span>` : ""}
            <span>${t.effort_hours}h</span>
            ${t.assignee ? `<span>${escapeHtml(t.assignee)}</span>` : ""}
          </div>
          <div class="task-actions">
            <button type="button" class="btn btn-sm btn-ghost" data-action="edit" data-id="${t.id}">Edit</button>
            <button type="button" class="btn btn-sm btn-ghost" data-action="explain" data-id="${t.id}">Why priority?</button>
            <button type="button" class="btn btn-danger" data-action="delete" data-id="${t.id}">Delete</button>
          </div>
        </article>`;
    })
    .join("");
}

function setAiModeBadge(config) {
  const badge = document.getElementById("aiModeBadge");
  if (!badge || !config) return;
  if (config.openai_configured) {
    badge.textContent = "GPT";
    badge.className = "badge badge-ai gpt";
    badge.title = `OpenAI ${config.openai_model} active`;
  } else {
    badge.textContent = "Built-in";
    badge.className = "badge badge-ai";
    badge.title = "Built-in AI (add OPENAI_API_KEY in .env for GPT)";
  }
}

function renderDashboard() {
  const stats = state.stats;
  if (!stats) {
    document.getElementById("statsRow").innerHTML =
      '<div class="dashboard-empty">Click <strong>Demo Data</strong> to load tasks, then return here for progress charts.</div>';
    document.getElementById("statusBars").innerHTML = "";
    document.getElementById("priorityGrid").innerHTML = "";
    document.getElementById("priorityQueue").innerHTML = "";
    document.getElementById("donutLabel").textContent = "0%";
    return;
  }

  document.getElementById("statsRow").innerHTML = `
    <div class="stat-card"><div class="value">${stats.completion_pct}%</div><div class="label">Completion</div></div>
    <div class="stat-card"><div class="value">${stats.total}</div><div class="label">Total Tasks</div></div>
    <div class="stat-card"><div class="value">${stats.in_progress}</div><div class="label">In Progress</div></div>
    <div class="stat-card"><div class="value">${stats.blocked}</div><div class="label">Blocked</div></div>
    <div class="stat-card"><div class="value">${stats.avg_priority}</div><div class="label">Avg Priority (active)</div></div>
    <div class="stat-card"><div class="value">${stats.critical_count}</div><div class="label">Critical</div></div>
  `;

  const pct = stats.completion_pct;
  const circumference = 314;
  document.getElementById("donutFg").style.strokeDashoffset =
    circumference - (pct / 100) * circumference;
  document.getElementById("donutLabel").textContent = `${pct}%`;

  const maxBar = Math.max(stats.todo, stats.in_progress, stats.done, stats.blocked, 1);
  const bars = [
    { label: "Todo", val: stats.todo, color: "var(--text-muted)" },
    { label: "In Progress", val: stats.in_progress, color: "var(--accent)" },
    { label: "Done", val: stats.done, color: "var(--success)" },
    { label: "Blocked", val: stats.blocked, color: "var(--danger)" },
  ];
  document.getElementById("statusBars").innerHTML = bars
    .map(
      (b) => `
    <div class="bar-row">
      <span>${b.label}</span>
      <div class="bar-track"><div class="bar-fill" style="width:${(b.val / maxBar) * 100}%;background:${b.color}"></div></div>
      <span>${b.val}</span>
    </div>`
    )
    .join("");

  const active = state.tasks.filter((t) => t.status !== "done");
  const buckets = { critical: 0, high: 0, medium: 0, low: 0 };
  active.forEach((t) => buckets[priorityClass(t.priority_score)]++);
  document.getElementById("priorityGrid").innerHTML = Object.entries(buckets)
    .map(
      ([k, n]) => `
    <div class="priority-box">
      <div class="num">${n}</div>
      <div style="font-size:0.75rem;color:var(--text-muted)">${k}</div>
    </div>`
    )
    .join("");

  const queue = [...active].sort((a, b) => b.priority_score - a.priority_score).slice(0, 8);
  document.getElementById("priorityQueue").innerHTML = queue.length
    ? queue
        .map(
          (t, i) => `
      <div class="queue-item">
        <span class="queue-rank">#${i + 1}</span>
        <div style="flex:1">
          <strong>${escapeHtml(t.title)}</strong>
          <div style="font-size:0.75rem;color:var(--text-muted)">${priorityLabel(t.priority_score)} · ${formatStatus(t.status)}</div>
        </div>
        <span class="priority-pill ${priorityClass(t.priority_score)}">${t.priority_score}</span>
      </div>`
        )
        .join("")
    : '<div class="empty-state">No active tasks in queue</div>';
}

async function refresh() {
  const [tasksRes, dashRes] = await Promise.all([API.tasks(), API.dashboard()]);
  state.tasks = tasksRes.tasks || [];
  state.stats = dashRes.stats;
  renderTasks();
  renderDashboard();
  renderActivity();
}

async function loadChatHistory() {
  const { messages } = await API.chatHistory();
  const el = document.getElementById("chatMessages");
  el.innerHTML = "";
  if (!messages || !messages.length) {
    addMessage(
      "assistant",
      "Welcome back! I am your **TaskPilot** assistant.\n\n" +
        "Ask me **anything** — features, how-to, tasks, priorities, dashboard, team chat, OpenAI, install.\n" +
        "Type **help** for all topics, or try: `add task Prepare demo urgent due tomorrow` · **Demo Data** button."
    );
    return;
  }
  messages.forEach((m) => {
    if (m.role === "user" || m.role === "assistant") addMessage(m.role, m.content);
  });
}

function showView(name) {
  const views = ["workspace", "dashboard", "team"];
  if (!views.includes(name)) name = "workspace";

  document.getElementById("viewWorkspace").classList.toggle("hidden", name !== "workspace");
  document.getElementById("viewDashboard").classList.toggle("hidden", name !== "dashboard");
  document.getElementById("viewTeam").classList.toggle("hidden", name !== "team");

  document.querySelectorAll(".nav-tab").forEach((t) => {
    t.classList.toggle("active", t.dataset.view === name);
  });

  window.scrollTo({ top: 0, behavior: "smooth" });

  stopTeamPoll();
  if (name === "dashboard") {
    refresh()
      .then(() => {
        renderDashboard();
        renderActivity();
      })
      .catch(showError);
  } else if (name === "team") {
    Promise.all([renderTeam(), renderTeamChat()]).then(startTeamPoll).catch(showError);
  } else if (name === "workspace") {
    renderTasks();
  }
}

function stopTeamPoll() {
  if (state.teamPollTimer) {
    clearInterval(state.teamPollTimer);
    state.teamPollTimer = null;
  }
}

function startTeamPoll() {
  stopTeamPoll();
  state.teamPollTimer = setInterval(pollTeamMessages, 5000);
}

async function pollTeamMessages() {
  if (document.getElementById("viewTeam")?.classList.contains("hidden")) return;
  try {
    const since = state.lastTeamMsgId || 0;
    if (!since) return;
    const data = await API.teamMessages(since);
    if (data.messages?.length) {
      const others = data.messages.filter(
        (m) => m.sender_name !== state.currentUser
      );
      if (others.length) {
        const last = others[others.length - 1];
        showToast(`Team: ${last.sender_name} — ${last.content.slice(0, 60)}`, "team-toast");
      }
      await renderTeamChat();
    }
    if (data.latest_id) state.lastTeamMsgId = data.latest_id;
  } catch (_) {
    /* ignore poll errors */
  }
}

function formatDateForInput(value) {
  if (!value) return "";
  const text = String(value).trim().slice(0, 10);
  return /^\d{4}-\d{2}-\d{2}$/.test(text) ? text : "";
}

function dateWithOffset(days) {
  const d = new Date();
  d.setDate(d.getDate() + days);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function setDeadlineValue(isoDate) {
  const input = document.getElementById("taskDeadline");
  input.value = isoDate || "";
  updateDeadlineHint();
}

function updateDeadlineHint() {
  const hint = document.getElementById("deadlineHint");
  const val = document.getElementById("taskDeadline").value;
  if (!hint) return;
  if (!val) {
    hint.textContent = "No deadline set. Use quick buttons or pick a date.";
    return;
  }
  const today = dateWithOffset(0);
  if (val < today) hint.textContent = "Warning: deadline is in the past (overdue).";
  else if (val === today) hint.textContent = "Due today.";
  else hint.textContent = `Due on ${val} (saved as YYYY-MM-DD).`;
}

function openTaskModal(task) {
  const modal = document.getElementById("taskModal");
  document.getElementById("modalTitle").textContent = task ? "Edit Task" : "New Task";
  document.getElementById("taskId").value = task ? task.id : "";
  document.getElementById("taskTitle").value = task ? task.title : "";
  document.getElementById("taskDesc").value = task ? task.description || "" : "";
  document.getElementById("taskStatus").value = task ? task.status : "todo";
  document.getElementById("taskEffort").value = task ? task.effort_hours : 4;
  setDeadlineValue(formatDateForInput(task?.deadline || task?.suggested_deadline || ""));
  document.getElementById("taskAssignee").value = task?.assignee || "";
  document.getElementById("taskTags").value = task?.tags || "";
  modal.showModal();
  setTimeout(() => document.getElementById("taskDeadline").focus(), 100);
}

async function renderTeam() {
  const data = await API.team();
  state.teamMembers = data.members || [];
  document.getElementById("teamCount").textContent = `${data.occupied} / ${data.max} Occupied`;
  const ul = document.getElementById("teamList");
  if (!data.members.length) {
    ul.innerHTML = '<li class="empty-state" style="list-style:none">No team members yet — join to appear in the roster</li>';
    return;
  }
  ul.innerHTML = data.members
    .map(
      (m) => `
    <li>
      <span><strong>${escapeHtml(m.name)}</strong> <span style="color:var(--text-muted);font-size:0.8rem">${m.role}</span></span>
      <button type="button" class="btn btn-danger" data-remove="${m.id}">Remove</button>
    </li>`
    )
    .join("");
}

function formatTeamTime(iso) {
  if (!iso) return "";
  try {
    const d = new Date(iso.replace("Z", ""));
    return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  } catch {
    return iso.slice(0, 16);
  }
}

async function renderTeamChat() {
  const box = document.getElementById("teamChatMessages");
  if (!box) return;
  const data = await API.teamMessages();
  const messages = data.messages || [];
  if (data.latest_id) state.lastTeamMsgId = data.latest_id;
  if (!messages.length) {
    box.innerHTML =
      '<div class="empty-state">No messages yet. Use <strong>@Name</strong> to mention a teammate.</div>';
    return;
  }
  const me = state.currentUser || "";
  box.innerHTML = messages
    .map((m) => {
      const mine = me && m.sender_name === me;
      return `<div class="team-msg${mine ? " mine" : ""}">
        <div class="team-msg-meta"><strong>${escapeHtml(m.sender_name)}</strong> · ${formatTeamTime(m.created_at)}</div>
        <div>${renderTeamMessageHtml(m.content)}</div>
      </div>`;
    })
    .join("");
  box.scrollTop = box.scrollHeight;
}

function setChatLoading(loading) {
  const btn = document.querySelector("#chatForm button[type=submit]");
  const input = document.getElementById("chatInput");
  if (btn) btn.disabled = loading;
  if (input) input.disabled = loading;
}

let uiBound = false;

function bindUi() {
  if (uiBound) return;
  uiBound = true;

  document.querySelectorAll(".nav-tab").forEach((tab) => {
    tab.addEventListener("click", (e) => {
      e.preventDefault();
      showView(tab.dataset.view);
    });
  });

  document.querySelectorAll("[data-footer-view]").forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      showView(link.dataset.footerView);
    });
  });

  document.getElementById("btnNewTask").addEventListener("click", () => openTaskModal(null));

  const deadlineInput = document.getElementById("taskDeadline");
  deadlineInput.addEventListener("change", updateDeadlineHint);
  deadlineInput.addEventListener("input", updateDeadlineHint);

  document.getElementById("btnDeadlinePicker").addEventListener("click", () => {
    deadlineInput.focus();
    try {
      deadlineInput.showPicker();
    } catch {
      deadlineInput.click();
    }
  });

  document.getElementById("deadlineQuick").addEventListener("click", (e) => {
    const btn = e.target.closest("button");
    if (!btn) return;
    if (btn.dataset.deadlineClear !== undefined) {
      setDeadlineValue("");
      return;
    }
    if (btn.dataset.deadlineSuggest !== undefined) {
      const id = document.getElementById("taskId").value;
      const task = id ? state.tasks.find((t) => String(t.id) === id) : null;
      const suggested = task?.suggested_deadline;
      if (suggested) setDeadlineValue(formatDateForInput(suggested));
      else showError("No AI suggested date yet. Save the task first or use AI Suggest on the board.");
      return;
    }
    const offset = btn.dataset.deadlineOffset;
    if (offset !== undefined) setDeadlineValue(dateWithOffset(parseInt(offset, 10)));
  });

  document.getElementById("btnCancelModal").addEventListener("click", () => {
  document.getElementById("taskModal").close();
});

document.getElementById("taskForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("taskId").value;
  const body = {
    title: document.getElementById("taskTitle").value.trim(),
    description: document.getElementById("taskDesc").value,
    status: document.getElementById("taskStatus").value,
    effort_hours: parseFloat(document.getElementById("taskEffort").value) || 4,
    deadline: document.getElementById("taskDeadline").value.trim() || null,
    assignee: document.getElementById("taskAssignee").value,
    tags: document.getElementById("taskTags").value,
  };
  if (!body.title) {
    showError("Task title is required.");
    return;
  }
  try {
    if (id) await API.updateTask(id, body);
    else await API.createTask(body);
    document.getElementById("taskModal").close();
    await refresh();
  } catch (err) {
    showError(err.message);
  }
});

document.getElementById("taskList").addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-action]");
  if (!btn) return;
  const id = parseInt(btn.dataset.id, 10);
  try {
    if (btn.dataset.action === "edit") {
      openTaskModal(state.tasks.find((t) => t.id === id));
    } else if (btn.dataset.action === "delete") {
      if (confirm("Delete this task?")) {
        await API.deleteTask(id);
        await refresh();
      }
    } else if (btn.dataset.action === "explain") {
      const { explanation } = await API.explain(id);
      addMessage("assistant", explanation);
      showView("workspace");
    }
  } catch (err) {
    showError(err.message);
  }
});

document.getElementById("chatForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = document.getElementById("chatInput");
  const msg = input.value.trim();
  if (!msg) return;
  input.value = "";
  addMessage("user", msg);
  const typing = document.createElement("div");
  typing.className = "msg assistant typing";
  typing.id = "chatTyping";
  typing.textContent = "TaskPilot is thinking...";
  document.getElementById("chatMessages").appendChild(typing);
  setChatLoading(true);
  try {
    const res = await API.chat(msg);
    typing.remove();
    if (!res.reply) {
      throw new Error("No response from assistant.");
    }
    addMessage("assistant", res.reply);
    if (res.tasks) state.tasks = res.tasks;
    if (res.stats) state.stats = res.stats;
    renderTasks(res.meta?.task_id);
    renderDashboard();
    if (res.meta?.highlight === "dashboard") showView("dashboard");
  } catch (err) {
    typing.remove();
    addMessage("assistant", "Sorry - " + err.message);
    showError(err.message);
  } finally {
    setChatLoading(false);
  }
});

document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    document.getElementById("chatInput").value = chip.dataset.prompt;
    document.getElementById("chatForm").requestSubmit();
  });
});

document.getElementById("taskSearch").addEventListener("input", () => {
  if (state.boardMode === "kanban") renderKanban();
  else renderTasks();
});
document.getElementById("filterStatus").addEventListener("change", () => {
  if (state.boardMode === "kanban") renderKanban();
  else renderTasks();
});

document.getElementById("btnBoardList")?.addEventListener("click", () => setBoardMode("list"));
document.getElementById("btnBoardKanban")?.addEventListener("click", () => setBoardMode("kanban"));

document.getElementById("btnTheme")?.addEventListener("click", toggleTheme);

document.getElementById("btnExport")?.addEventListener("click", () => {
  const fmt = confirm("Export as CSV? (Cancel for JSON)") ? "csv" : "json";
  window.location.href = `/api/tasks/export?format=${fmt}`;
});

document.getElementById("btnRecalc").addEventListener("click", async () => {
  try {
    await API.recalculate();
    await refresh();
    addMessage("assistant", "Priority scores recalculated for all tasks.");
  } catch (err) {
    showError(err.message);
  }
});

document.getElementById("btnSuggest").addEventListener("click", async () => {
  try {
    const res = await API.applySuggestions();
    addMessage("assistant", `Applied AI-suggested deadlines to **${res.updated}** task(s).`);
    state.tasks = res.tasks;
    await refresh();
  } catch (err) {
    showError(err.message);
  }
});

document.getElementById("btnSeed").addEventListener("click", async () => {
  const btn = document.getElementById("btnSeed");
  const hadTasks = state.tasks.length > 0;
  if (hadTasks) {
    const ok = confirm(
      "Replace your current tasks with the official demo sample set? (Recommended for judging.)"
    );
    if (!ok) return;
  }
  btn.disabled = true;
  try {
    const res = await API.seed(true);
    state.tasks = res.tasks || [];
    if (res.stats) state.stats = res.stats;
    renderTasks();
    renderDashboard();
    const msg =
      res.message ||
      `Loaded ${state.tasks.length} demo tasks. Open the **Dashboard** tab to see progress.`;
    addMessage("assistant", msg);
    const toast = document.getElementById("appToast");
    if (toast) {
      toast.textContent = msg.replace(/\*\*/g, "");
      toast.classList.add("visible");
      setTimeout(() => toast.classList.remove("visible"), 4000);
    }
    showView("workspace");
  } catch (err) {
    showError(err.message);
  } finally {
    btn.disabled = false;
  }
});

document.getElementById("teamForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = document.getElementById("memberName").value.trim();
  const role = document.getElementById("memberRole").value;
  try {
    await API.addTeam({ name, role });
    document.getElementById("memberName").value = "";
    await renderTeam();
  } catch (err) {
    showError(err.message);
  }
});

document.getElementById("teamList").addEventListener("click", async (e) => {
  const id = e.target.dataset.remove;
  if (id) {
    try {
      await API.removeTeam(id);
      await renderTeam();
    } catch (err) {
      showError(err.message);
    }
  }
});

const teamChatForm = document.getElementById("teamChatForm");
if (teamChatForm) {
  teamChatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const input = document.getElementById("teamChatInput");
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    try {
      await API.sendTeamMessage(text);
      await renderTeamChat();
    } catch (err) {
      showError(err.message);
    }
  });
}

}

async function initApp() {
  initTheme();
  try {
    bindUi();
    await API.health();
    setConnectionStatus(true, "Backend connected");
    const config = await API.config();
    setAiModeBadge(config);
    const userPill = document.querySelector(".user-pill");
    if (userPill) state.currentUser = userPill.textContent.trim();
    await refresh();
    await loadChatHistory();
    await renderTeam();
    showView("workspace");
  } catch (err) {
    setConnectionStatus(false, err.message);
    showError(`Cannot connect to backend: ${err.message}. Start server: python run.py`);
    try {
      bindUi();
    } catch (_) {
      /* already bound */
    }
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initApp);
} else {
  initApp();
}
