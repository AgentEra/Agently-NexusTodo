const STATUS_CONFIG = [
  { key: "待办", label: "待办" },
  { key: "进行中", label: "进行中" },
  { key: "已完成", label: "已完成" },
  { key: "已延期", label: "已延期" },
  { key: "已取消", label: "已取消" }
];

const STORAGE_KEYS = {
  baseUrl: "nt_base_url",
  agentBaseUrl: "nt_agent_base_url",
  deviceId: "nt_device_id",
  userId: "nt_user_id",
  reviewTime: "nt_review_time",
  lastReviewDone: "nt_last_review_done",
  cachedTasks: "nt_tasks_cache",
  lastSync: "nt_last_sync"
};

const state = {
  baseUrl: "http://localhost:8080/api",
  agentBaseUrl: "",
  deviceId: "",
  userId: "",
  tasks: [],
  filtered: [],
  filters: {
    status: "全部",
    tags: new Set(),
    search: ""
  },
  sort: "createdAt:desc",
  editingTaskId: null,
  reviewTime: "18:00",
  reviewActive: false,
  reviewMode: false,
  lastReviewDone: "",
  viewMode: "tasks",
  chatSessionId: "",
  chatMessages: [],
  chatRunning: false,
  chatAbortController: null
};

const els = {};

const todayString = () => new Date().toISOString().slice(0, 10);

const escapeHtml = (value) =>
  String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");

const createUuid = () => {
  if (crypto?.randomUUID) return crypto.randomUUID();
  const template = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx";
  return template.replace(/[xy]/g, (char) => {
    const rand = (Math.random() * 16) | 0;
    const value = char === "x" ? rand : (rand & 0x3) | 0x8;
    return value.toString(16);
  });
};

const parseTags = (input) => {
  if (!input) return [];
  const raw = input
    .split(/[\s,]+/)
    .map((item) => item.trim())
    .filter(Boolean)
    .map((item) => item.replace(/^#/, ""));
  return Array.from(new Set(raw));
};

const formatTime = (value) => {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
};

const getStorage = (key) => {
  try {
    return localStorage.getItem(key);
  } catch (error) {
    return null;
  }
};

const setStorage = (key, value) => {
  try {
    localStorage.setItem(key, value);
  } catch (error) {
    // ignore storage errors
  }
};

const removeStorage = (key) => {
  try {
    localStorage.removeItem(key);
  } catch (error) {
    // ignore storage errors
  }
};

const showToast = (message) => {
  if (!message) return;
  els.toast.textContent = message;
  els.toast.classList.add("show");
  setTimeout(() => {
    els.toast.classList.remove("show");
  }, 2500);
};

const setBanner = (message) => {
  if (!message) {
    els.banner.textContent = "";
    els.banner.classList.remove("show");
    return;
  }
  els.banner.textContent = message;
  els.banner.classList.add("show");
};

const updateDeviceMeta = () => {
  if (!state.deviceId || !state.userId) {
    els.deviceMeta.textContent = "设备未注册";
    return;
  }
  const shortUser = state.userId.slice(0, 8);
  const shortDevice = state.deviceId.slice(0, 8);
  els.deviceMeta.textContent = `用户 ${shortUser} · 设备 ${shortDevice}`;
};

const authHeaders = () => ({
  Authorization: "Bearer default-token",
  "X-User-ID": state.userId,
  "X-Device-ID": state.deviceId
});

const deriveAgentBaseUrl = (baseUrl) => {
  const trimmed = baseUrl.replace(/\/$/, "");
  if (trimmed.endsWith("/api")) {
    return `${trimmed.slice(0, -4)}/agent`;
  }
  return `${trimmed}/agent`;
};

const getAgentBaseUrl = () =>
  state.agentBaseUrl || deriveAgentBaseUrl(state.baseUrl);

const requestApi = async ({ url, method, headers, body }) => {
  const bridge = window?.nexusTodoBridge;
  if (bridge?.request) {
    return bridge.request({ url, method, headers, body });
  }
  const response = await fetch(url, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined
  });
  const text = await response.text();
  return {
    ok: response.ok,
    status: response.status,
    statusText: response.statusText,
    text
  };
};

const apiFetch = async (path, { method = "GET", body, auth = true } = {}) => {
  const base = state.baseUrl.replace(/\/$/, "");
  const url = `${base}${path}`;
  const headers = { "Content-Type": "application/json" };
  if (auth) {
    Object.assign(headers, authHeaders());
  }

  const response = await requestApi({ url, method, headers, body });

  const text = response.text || "";
  let payload = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch (error) {
      payload = { message: text };
    }
  }

  if (!response.ok) {
    const message =
      payload?.error?.message ||
      payload?.message ||
      response.statusText ||
      "请求失败";
    throw new Error(message);
  }

  return payload;
};

const agentFetch = async (path, { method = "POST", body } = {}) => {
  const headers = { "Content-Type": "application/json", ...authHeaders() };
  const buildUrl = (base) => `${base.replace(/\/$/, "")}${path}`;
  const tryRequest = async (base) =>
    requestApi({ url: buildUrl(base), method, headers, body });

  const primaryBase = getAgentBaseUrl();
  let response = await tryRequest(primaryBase);

  if (response.status === 404 && !state.agentBaseUrl) {
    const fallbackBase = "http://127.0.0.1:15590/agent";
    if (fallbackBase !== primaryBase) {
      const fallbackResponse = await tryRequest(fallbackBase);
      if (fallbackResponse.ok) {
        state.agentBaseUrl = fallbackBase;
        setStorage(STORAGE_KEYS.agentBaseUrl, fallbackBase);
        showToast("已自动切换 Agent 服务地址");
        response = fallbackResponse;
      } else {
        response = fallbackResponse;
      }
    }
  }

  const text = response.text || "";
  let payload = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch (error) {
      payload = { message: text };
    }
  }
  if (!response.ok) {
    let message =
      payload?.error?.message ||
      payload?.message ||
      response.statusText ||
      "请求失败";
    if (response.status === 404) {
      message =
        "Agent 服务地址未找到，请在设置中配置 Agent Base URL。";
    }
    throw new Error(message);
  }
  return payload;
};

const registerDevice = async () => {
  if (!state.deviceId) {
    state.deviceId = createUuid();
  }
  const payload = await apiFetch("/device/register", {
    method: "POST",
    body: { deviceId: state.deviceId },
    auth: false
  });
  if (payload?.deviceId) {
    state.deviceId = payload.deviceId;
    setStorage(STORAGE_KEYS.deviceId, payload.deviceId);
  }
  if (payload?.userId) {
    state.userId = payload.userId;
    setStorage(STORAGE_KEYS.userId, payload.userId);
  }
};

const cacheTasks = () => {
  setStorage(STORAGE_KEYS.cachedTasks, JSON.stringify(state.tasks));
};

const loadCachedTasks = () => {
  const cached = getStorage(STORAGE_KEYS.cachedTasks);
  if (!cached) return null;
  try {
    const parsed = JSON.parse(cached);
    if (Array.isArray(parsed)) return parsed;
  } catch (error) {
    return null;
  }
  return null;
};

const normalizeTasks = (items) =>
  (items || []).map((task) => ({
    ...task,
    tags: Array.isArray(task.tags) ? task.tags : []
  }));

const syncTasks = async ({ showToast: toast = true } = {}) => {
  try {
    const tasks = await apiFetch("/tasks");
    state.tasks = normalizeTasks(tasks);
    cacheTasks();
    applyFilters();
    renderBoard();
    renderStatusFilters();
    renderTagFilters();
    setBanner("");
    const syncTime = new Date().toLocaleTimeString("zh-CN", {
      hour: "2-digit",
      minute: "2-digit"
    });
    els.syncHint.textContent = `最近同步：${syncTime}`;
    setStorage(STORAGE_KEYS.lastSync, syncTime);
    if (toast) showToast("任务已同步");
  } catch (error) {
    const cached = loadCachedTasks();
    if (cached) {
      state.tasks = normalizeTasks(cached);
      applyFilters();
      renderBoard();
      renderStatusFilters();
      renderTagFilters();
      setBanner("网络连接失败，显示缓存数据（可能不是最新）。");
    } else {
      setBanner("网络连接失败，无法加载任务。");
    }
    if (toast) showToast(error.message);
  }
};

const applyFilters = () => {
  let list = [...state.tasks];

  if (state.filters.status !== "全部") {
    list = list.filter((task) => task.status === state.filters.status);
  }

  if (state.filters.tags.size > 0) {
    list = list.filter((task) =>
      Array.from(state.filters.tags).some((tag) => task.tags.includes(tag))
    );
  }

  if (state.filters.search) {
    const keyword = state.filters.search.toLowerCase();
    list = list.filter((task) => {
      const title = (task.title || "").toLowerCase();
      const description = (task.description || "").toLowerCase();
      return title.includes(keyword) || description.includes(keyword);
    });
  }

  const [field, direction] = state.sort.split(":");
  list.sort((a, b) => {
    const aTime = new Date(a[field] || 0).getTime();
    const bTime = new Date(b[field] || 0).getTime();
    if (direction === "asc") return aTime - bTime;
    return bTime - aTime;
  });

  state.filtered = list;
};

const setViewMode = (mode) => {
  state.viewMode = mode;
  els.taskView.classList.toggle("active", mode === "tasks");
  els.chatView.classList.toggle("active", mode === "chat");
  if (els.chatViewBtn) {
    els.chatViewBtn.classList.toggle("active", mode === "chat");
  }
};

const renderChatMessages = () => {
  els.chatMessages.innerHTML = state.chatMessages
    .map((item) => {
      if (item.type === "tasks") {
        const title = escapeHtml(item.title || "任务列表");
        const tasks = (item.tasks || [])
          .map((task) => {
            const name = escapeHtml(task.title || "(无标题)");
            const status = escapeHtml(task.status || "");
            const tags = Array.isArray(task.tags) ? task.tags : [];
            const tagText = tags.length ? `标签：${escapeHtml(tags.join(" / "))}` : "无标签";
            return `
              <div class="chat-card-item">
                <div class="chat-card-name">${name}</div>
                <div class="chat-card-meta">状态：${status} · ${tagText}</div>
              </div>
            `;
          })
          .join("");
        return `
          <div class="chat-message assistant">
            <div class="chat-card">
              <div class="chat-card-title">${title}</div>
              <div class="chat-card-list">${tasks || ""}</div>
            </div>
          </div>
        `;
      }

      const bubbleClass = item.status ? `chat-bubble ${item.status}` : "chat-bubble";
      return `
        <div class="chat-message ${item.role}">
          <div class="${bubbleClass}">${escapeHtml(item.content).replace(/\n/g, "<br>")}</div>
        </div>
      `;
    })
    .join("");
  els.chatMessages.scrollTop = els.chatMessages.scrollHeight;
};

const appendChatMessage = (role, content, status = "final") => {
  state.chatMessages.push({ role, content, type: "text", status });
  renderChatMessages();
};

const appendTaskCards = (tasks, title) => {
  if (!tasks || tasks.length === 0) return;
  state.chatMessages.push({
    role: "assistant",
    type: "tasks",
    title,
    tasks: normalizeTasks(tasks)
  });
  renderChatMessages();
};

const updateChatSendButton = () => {
  if (!els.chatSendBtn) return;
  if (state.chatRunning) {
    els.chatSendBtn.textContent = "终止任务";
    els.chatSendBtn.classList.add("danger");
  } else {
    els.chatSendBtn.textContent = "发送";
    els.chatSendBtn.classList.remove("danger");
  }
};

const setChatRunning = (running) => {
  state.chatRunning = running;
  updateChatSendButton();
};

const handleChatSend = async (event) => {
  event.preventDefault();
  if (state.chatRunning) {
    const ok = window.confirm("正在执行任务，确认终止吗？");
    if (!ok) return;
    if (state.chatAbortController) {
      state.chatAbortController.abort();
    }
    return;
  }
  const content = els.chatInput.value.trim();
  if (!content) return;
  if (!state.userId || !state.deviceId) {
    showToast("设备未注册，无法发起对话");
    return;
  }
  appendChatMessage("user", content);
  els.chatInput.value = "";
  const pendingIndex = state.chatMessages.length;
  appendChatMessage("assistant", "...", "streaming");
  const controller = new AbortController();
  state.chatAbortController = controller;
  setChatRunning(true);
  try {
    await streamAgentChat({
      content,
      pendingIndex,
      controller
    });
  } catch (error) {
    state.chatMessages[pendingIndex] = {
      role: "assistant",
      content: `请求失败：${error.message}`,
      type: "text",
      status: "final"
    };
    renderChatMessages();
  } finally {
    state.chatAbortController = null;
    setChatRunning(false);
  }
};

const streamAgentChat = async ({ content, pendingIndex, controller }) => {
  try {
    const params = new URLSearchParams({
      sessionId: state.chatSessionId || "",
      userId: state.userId,
      deviceId: state.deviceId,
      message: content
    });

    const headers = { Accept: "text/event-stream", ...authHeaders() };
    const buildUrl = (base) =>
      `${base.replace(/\/$/, "")}/chat/stream?${params.toString()}`;

    const primaryBase = getAgentBaseUrl();
    let response = await fetch(buildUrl(primaryBase), {
      headers,
      signal: controller?.signal
    });

    if (response.status === 404 && !state.agentBaseUrl) {
      const fallbackBase = "http://127.0.0.1:15590/agent";
      if (fallbackBase !== primaryBase) {
        const fallbackResponse = await fetch(buildUrl(fallbackBase), {
          headers,
          signal: controller?.signal
        });
        if (fallbackResponse.ok) {
          state.agentBaseUrl = fallbackBase;
          setStorage(STORAGE_KEYS.agentBaseUrl, fallbackBase);
          showToast("已自动切换 Agent 服务地址");
          response = fallbackResponse;
        } else {
          response = fallbackResponse;
        }
      }
    }

    if (!response.ok || !response.body) {
      const text = await response.text();
      let message = text || response.statusText || "请求失败";
      if (response.status === 404) {
        message = "Agent 服务地址未找到，请在设置中配置 Agent Base URL。";
      }
      throw new Error(message);
    }

    let assistantText = "";
    let execution = null;
    let action = null;
    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    let currentEvent = null;
    let currentData = "";

    const flushEvent = async () => {
      if (!currentEvent) return;
      let payload = null;
      try {
        payload = currentData ? JSON.parse(currentData) : null;
      } catch (error) {
        payload = null;
      }

      if (currentEvent === "delta" && payload?.content) {
        assistantText += payload.content;
        state.chatMessages[pendingIndex] = {
          role: "assistant",
          content: assistantText || "...",
          type: "text",
          status: "streaming"
        };
        renderChatMessages();
        if (payload?.sessionId) {
          state.chatSessionId = payload.sessionId;
        }
      } else if (currentEvent === "action") {
        action = payload;
    } else if (currentEvent === "execution") {
      execution = payload;
    } else if (currentEvent === "done") {
        if (payload?.assistantMessage && !assistantText) {
          assistantText = payload.assistantMessage;
        }
        if (payload?.sessionId) {
          state.chatSessionId = payload.sessionId;
        }
        state.chatMessages[pendingIndex] = {
          role: "assistant",
          content: assistantText || payload?.assistantMessage || "已收到请求。",
          type: "text",
          status: "final"
        };
        renderChatMessages();
      if (execution?.status === "success") {
        await syncTasks({ showToast: false });
      }
      if (execution?.status === "success") {
        appendCardsFromExecution(execution, action);
      }
      } else if (currentEvent === "error") {
        const message = payload?.message || "请求失败";
        throw new Error(message);
      }

      currentEvent = null;
      currentData = "";
    };

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split(/\r?\n/);
      buffer = lines.pop() || "";
      for (const line of lines) {
        if (!line) {
          await flushEvent();
          continue;
        }
        if (line.startsWith("event:")) {
          currentEvent = line.slice(6).trim();
          continue;
        }
        if (line.startsWith("data:")) {
          currentData += line.slice(5).trim();
          continue;
        }
      }
    }
  } catch (error) {
    if (error?.name === "AbortError") {
      state.chatMessages[pendingIndex] = {
        role: "assistant",
        content: "已终止任务。",
        type: "text",
        status: "final"
      };
      renderChatMessages();
      return;
    }
    throw error;
  }
};

const appendCardsFromExecution = (execution, action) => {
  if (!execution || execution.status === "failed") return;
  const result = execution.result;
  if (!result) return;
  let tasks = [];
  if (Array.isArray(result)) {
    tasks = result;
  } else if (Array.isArray(result.updated)) {
    tasks = result.updated;
  } else if (Array.isArray(result.deleted)) {
    tasks = result.deleted;
  } else if (result.taskId || result.title) {
    tasks = [result];
  }
  if (tasks.length === 0) return;
  const intent = action?.intent || action?.action;
  const title = intent === "detail" || intent === "get_task" ? "任务详情" : "任务列表";
  appendTaskCards(tasks, title);
};


const updateListHeader = () => {
  if (!els.listTitle || !els.listMeta) return;
  let title = "我的清单";
  if (state.filters.status !== "全部") {
    title = state.filters.status;
  } else if (state.filters.tags.size > 0) {
    title = `#${Array.from(state.filters.tags).join(" #")}`;
  }
  els.listTitle.textContent = title;
  els.listMeta.textContent = `${state.filtered.length} 项`;
};

const renderStatusFilters = () => {
  els.statusFilters.innerHTML = "";
  const counts = STATUS_CONFIG.reduce(
    (acc, status) => ({ ...acc, [status.key]: 0 }),
    {}
  );
  state.tasks.forEach((task) => {
    if (counts[task.status] !== undefined) {
      counts[task.status] += 1;
    }
  });
  const totalCount = state.tasks.length;
  const allChip = document.createElement("button");
  allChip.type = "button";
  allChip.className = "chip";
  allChip.dataset.value = "全部";
  allChip.innerHTML = `<span class="nav-label">我的清单</span><span class="nav-count">${totalCount}</span>`;
  els.statusFilters.appendChild(allChip);

  STATUS_CONFIG.forEach((status) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "chip";
    chip.dataset.value = status.key;
    chip.innerHTML = `<span class="nav-label">${status.label}</span><span class="nav-count">${counts[status.key] || 0}</span>`;
    els.statusFilters.appendChild(chip);
  });

  updateStatusFilterActive();
};

const updateStatusFilterActive = () => {
  Array.from(els.statusFilters.children).forEach((chip) => {
    chip.classList.toggle(
      "active",
      chip.dataset.value === state.filters.status
    );
  });
};

const renderTagFilters = () => {
  const tags = new Set();
  state.tasks.forEach((task) => {
    task.tags.forEach((tag) => tags.add(tag));
  });

  const tagArray = Array.from(tags).sort((a, b) => a.localeCompare(b, "zh-CN"));
  els.tagFilters.innerHTML = "";
  let filtersChanged = false;
  state.filters.tags.forEach((tag) => {
    if (!tags.has(tag)) {
      state.filters.tags.delete(tag);
      filtersChanged = true;
    }
  });

  if (tagArray.length === 0) {
    const empty = document.createElement("div");
    empty.className = "small";
    empty.textContent = "暂无标签";
    els.tagFilters.appendChild(empty);
    if (filtersChanged) {
      applyFilters();
      renderBoard();
    }
    return;
  }

  tagArray.forEach((tag) => {
    const wrapper = document.createElement("label");
    wrapper.className = "tag-filter";
    const input = document.createElement("input");
    input.type = "checkbox";
    input.value = tag;
    input.checked = state.filters.tags.has(tag);
    const span = document.createElement("span");
    span.textContent = `#${tag}`;
    wrapper.appendChild(input);
    wrapper.appendChild(span);
    els.tagFilters.appendChild(wrapper);
  });

  if (filtersChanged) {
    applyFilters();
    renderBoard();
  }
};

const buildTaskCard = (task) => {
  const isDone = task.status === "已完成";
  const tags = task.tags.length
    ? task.tags.map((tag) => `<span class="tag">#${escapeHtml(tag)}</span>`).join("")
    : `<span class="task-meta">无标签</span>`;
  const description = task.description
    ? `<p>${escapeHtml(task.description)}</p>`
    : "";

  const options = STATUS_CONFIG.map(
    (status) =>
      `<option value="${status.key}"${
        status.key === task.status ? " selected" : ""
      }>${status.label}</option>`
  ).join("");

  return `
    <article class="task-item" data-id="${escapeHtml(task.taskId)}" data-status="${escapeHtml(
      task.status
    )}">
      <div class="task-left">
        <span class="task-circle ${isDone ? "done" : ""}">${isDone ? "✓" : ""}</span>
        <div class="task-info">
          <h3>${escapeHtml(task.title)}</h3>
          ${description}
          <div class="task-tags">${tags}</div>
          <div class="task-meta">更新 ${formatTime(task.updatedAt || task.createdAt)}</div>
        </div>
      </div>
      <div class="task-right">
        <select class="status-select">${options}</select>
        <div class="task-actions">
          <button class="ghost" data-action="edit">编辑</button>
          <button class="ghost" data-action="delete">删除</button>
        </div>
      </div>
    </article>
  `;
};

const renderBoard = () => {
  els.board.innerHTML = "";
  if (state.filtered.length === 0) {
    els.board.innerHTML = `<div class="empty">暂无任务</div>`;
  } else {
    els.board.innerHTML = state.filtered.map((task) => buildTaskCard(task)).join("");
  }
  updateListHeader();
  updateReviewMode();
};

const resetEditor = () => {
  state.editingTaskId = null;
  els.editorTitle.textContent = "新建任务";
  els.editorHint.textContent = "用 #标签 快速归档任务";
  els.taskForm.reset();
  els.statusSelect.value = "待办";
  els.statusSelect.disabled = true;
  els.statusHelper.textContent = "新任务将以“待办”创建，保存后可调整状态。";
};

const openEditorModal = () => {
  els.editorModal.classList.add("open");
  els.editorModal.setAttribute("aria-hidden", "false");
};

const closeEditorModal = () => {
  els.editorModal.classList.remove("open");
  els.editorModal.setAttribute("aria-hidden", "true");
};

const fillEditor = (task) => {
  openEditorModal();
  state.editingTaskId = task.taskId;
  els.editorTitle.textContent = "编辑任务";
  els.editorHint.textContent = `更新任务：${task.title}`;
  els.titleInput.value = task.title || "";
  els.descriptionInput.value = task.description || "";
  els.tagsInput.value = task.tags.map((tag) => `#${tag}`).join(" ");
  els.statusSelect.disabled = false;
  els.statusSelect.value = task.status;
  els.statusHelper.textContent = "编辑模式下可直接调整状态。";
};

const openQuickModal = () => {
  els.quickTitleInput.value = "";
  els.quickTagsInput.value = "";
  els.quickModal.classList.add("open");
  els.quickModal.setAttribute("aria-hidden", "false");
  setTimeout(() => els.quickTitleInput.focus(), 0);
};

const closeQuickModal = () => {
  els.quickModal.classList.remove("open");
  els.quickModal.setAttribute("aria-hidden", "true");
};

const handleQuickSave = async () => {
  const title = els.quickTitleInput.value.trim();
  const tags = parseTags(els.quickTagsInput.value);
  if (!title) {
    showToast("标题不能为空");
    return;
  }
  try {
    await apiFetch("/tasks", {
      method: "POST",
      body: { title, tags }
    });
    closeQuickModal();
    showToast("任务已创建");
    await syncTasks({ showToast: false });
  } catch (error) {
    showToast(error.message);
  }
};

const handleQuickExpand = () => {
  const title = els.quickTitleInput.value.trim();
  const tagsInput = els.quickTagsInput.value.trim();
  closeQuickModal();
  resetEditor();
  openEditorModal();
  if (title) {
    els.titleInput.value = title;
  }
  if (tagsInput) {
    els.tagsInput.value = tagsInput;
  }
  els.titleInput.focus();
};

const handleCollapseEditor = () => {
  const title = els.titleInput.value.trim();
  const tagsInput = els.tagsInput.value.trim();
  closeEditorModal();
  if (state.editingTaskId) {
    resetEditor();
    openQuickModal();
    return;
  }
  openQuickModal();
  if (title) els.quickTitleInput.value = title;
  if (tagsInput) els.quickTagsInput.value = tagsInput;
  els.quickTitleInput.focus();
};

const handleSaveTask = async (event) => {
  event.preventDefault();
  const title = els.titleInput.value.trim();
  const description = els.descriptionInput.value.trim();
  const tags = parseTags(els.tagsInput.value);

  if (!title) {
    showToast("标题不能为空");
    return;
  }

  if (state.editingTaskId) {
    try {
      const payload = {
        title,
        description: description || undefined,
        tags,
        status: els.statusSelect.value
      };
      await apiFetch(`/tasks/${state.editingTaskId}`, {
        method: "PUT",
        body: payload
      });
      showToast("任务已更新");
      resetEditor();
      await syncTasks({ showToast: false });
    } catch (error) {
      showToast(error.message);
    }
  } else {
    try {
      const payload = {
        title,
        description: description || undefined,
        tags
      };
      await apiFetch("/tasks", {
        method: "POST",
        body: payload
      });
      showToast("任务已创建");
      resetEditor();
      await syncTasks({ showToast: false });
    } catch (error) {
      showToast(error.message);
    }
  }
};

const handleBoardClick = async (event) => {
  const actionBtn = event.target.closest("button[data-action]");
  if (!actionBtn) return;
  const card = actionBtn.closest(".task-item");
  if (!card) return;
  const taskId = card.dataset.id;
  const task = state.tasks.find((item) => item.taskId === taskId);
  if (!task) return;

  if (actionBtn.dataset.action === "edit") {
    fillEditor(task);
    return;
  }

  if (actionBtn.dataset.action === "delete") {
    const confirmed = window.confirm("确定要删除该任务吗？");
    if (!confirmed) return;
    try {
      await apiFetch(`/tasks/${taskId}`, { method: "DELETE" });
      showToast("任务已删除");
      await syncTasks({ showToast: false });
    } catch (error) {
      showToast(error.message);
    }
  }
};

const handleStatusChange = async (event) => {
  const select = event.target;
  if (!select.classList.contains("status-select")) return;
  const card = select.closest(".task-item");
  if (!card) return;
  const taskId = card.dataset.id;
  try {
    await apiFetch(`/tasks/${taskId}`, {
      method: "PUT",
      body: { status: select.value }
    });
    showToast("状态已更新");
    await syncTasks({ showToast: false });
  } catch (error) {
    showToast(error.message);
  }
};

const handleStatusFilterClick = (event) => {
  const chip = event.target.closest(".chip");
  if (!chip) return;
  state.filters.status = chip.dataset.value;
  setViewMode("tasks");
  updateStatusFilterActive();
  applyFilters();
  renderBoard();
};

const handleTagFilterChange = (event) => {
  const input = event.target.closest("input[type=checkbox]");
  if (!input) return;
  if (input.checked) {
    state.filters.tags.add(input.value);
  } else {
    state.filters.tags.delete(input.value);
  }
  setViewMode("tasks");
  applyFilters();
  renderBoard();
};

const clearFilters = () => {
  state.filters.status = "全部";
  state.filters.tags.clear();
  state.filters.search = "";
  els.searchInput.value = "";
  renderStatusFilters();
  renderTagFilters();
  applyFilters();
  renderBoard();
};

const openSettings = () => {
  els.baseUrlInput.value = state.baseUrl;
  els.agentBaseUrlInput.value = getAgentBaseUrl();
  els.reviewTimeInput.value = state.reviewTime;
  els.userIdInput.value = state.userId;
  els.deviceIdInput.value = state.deviceId;
  els.settingsModal.classList.add("open");
  els.settingsModal.setAttribute("aria-hidden", "false");
};

const closeSettings = () => {
  els.settingsModal.classList.remove("open");
  els.settingsModal.setAttribute("aria-hidden", "true");
};

const saveSettings = () => {
  const baseUrl = els.baseUrlInput.value.trim();
  if (baseUrl) {
    state.baseUrl = baseUrl.replace(/\/$/, "");
    setStorage(STORAGE_KEYS.baseUrl, state.baseUrl);
  }
  const agentBaseUrl = els.agentBaseUrlInput.value.trim();
  if (agentBaseUrl) {
    state.agentBaseUrl = agentBaseUrl.replace(/\/$/, "");
    setStorage(STORAGE_KEYS.agentBaseUrl, state.agentBaseUrl);
  } else {
    state.agentBaseUrl = "";
    removeStorage(STORAGE_KEYS.agentBaseUrl);
  }
  state.reviewTime = els.reviewTimeInput.value || "18:00";
  setStorage(STORAGE_KEYS.reviewTime, state.reviewTime);
  closeSettings();
  showToast("设置已保存");
  checkReviewTime();
};

const updateReviewMode = () => {
  if (state.reviewMode) {
    els.appRoot.classList.add("review-mode");
  } else {
    els.appRoot.classList.remove("review-mode");
  }
  els.reviewBtn.classList.toggle("active", state.reviewActive);
  if (els.reviewLabel) {
    els.reviewLabel.textContent = state.reviewActive ? "完成复盘" : "复盘";
  }
};

const checkReviewTime = () => {
  const [hour, minute] = state.reviewTime.split(":").map(Number);
  if (Number.isNaN(hour) || Number.isNaN(minute)) return;
  const now = new Date();
  const reviewMoment = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate(),
    hour,
    minute
  );
  const today = todayString();

  if (now >= reviewMoment && state.lastReviewDone !== today) {
    state.reviewActive = true;
    state.reviewMode = true;
  }

  updateReviewMode();
};

const completeReview = () => {
  state.reviewActive = false;
  state.reviewMode = false;
  state.lastReviewDone = todayString();
  setStorage(STORAGE_KEYS.lastReviewDone, state.lastReviewDone);
  updateReviewMode();
  showToast("复盘完成，继续保持节奏");
};

const toggleReviewMode = () => {
  if (state.reviewActive) {
    completeReview();
    return;
  }
  state.reviewMode = !state.reviewMode;
  updateReviewMode();
};

const initStateFromStorage = () => {
  state.baseUrl = getStorage(STORAGE_KEYS.baseUrl) || state.baseUrl;
  state.agentBaseUrl = getStorage(STORAGE_KEYS.agentBaseUrl) || "";
  state.deviceId = getStorage(STORAGE_KEYS.deviceId) || "";
  state.userId = getStorage(STORAGE_KEYS.userId) || "";
  state.reviewTime = getStorage(STORAGE_KEYS.reviewTime) || state.reviewTime;
  state.lastReviewDone = getStorage(STORAGE_KEYS.lastReviewDone) || "";
  const lastSync = getStorage(STORAGE_KEYS.lastSync);
  if (lastSync) {
    els.syncHint.textContent = `最近同步：${lastSync}`;
  }
};

const bindEvents = () => {
  els.syncBtn.addEventListener("click", () => syncTasks({ showToast: true }));
  els.settingsBtn.addEventListener("click", openSettings);
  els.closeSettingsBtn.addEventListener("click", closeSettings);
  els.saveSettingsBtn.addEventListener("click", saveSettings);
  els.reviewBtn.addEventListener("click", toggleReviewMode);
  els.taskForm.addEventListener("submit", handleSaveTask);
  els.resetTaskBtn.addEventListener("click", resetEditor);
  els.newTaskBtn.addEventListener("click", openQuickModal);
  els.quickSaveBtn.addEventListener("click", handleQuickSave);
  els.quickExpandBtn.addEventListener("click", handleQuickExpand);
  els.closeQuickBtn.addEventListener("click", closeQuickModal);
  els.collapseEditorBtn.addEventListener("click", handleCollapseEditor);
  els.chatViewBtn.addEventListener("click", () => setViewMode("chat"));
  els.backToTasksBtn.addEventListener("click", () => setViewMode("tasks"));
  els.chatForm.addEventListener("submit", handleChatSend);

  els.statusFilters.addEventListener("click", handleStatusFilterClick);
  els.tagFilters.addEventListener("change", handleTagFilterChange);
  els.searchInput.addEventListener("input", (event) => {
    state.filters.search = event.target.value.trim();
    applyFilters();
    renderBoard();
  });
  els.sortSelect.addEventListener("change", (event) => {
    state.sort = event.target.value;
    applyFilters();
    renderBoard();
  });
  els.clearFiltersBtn.addEventListener("click", clearFilters);

  els.board.addEventListener("click", handleBoardClick);
  els.board.addEventListener("change", handleStatusChange);

  els.settingsModal.addEventListener("click", (event) => {
    if (event.target === els.settingsModal) closeSettings();
  });

  els.quickModal.addEventListener("click", (event) => {
    if (event.target === els.quickModal) closeQuickModal();
  });

  els.editorModal.addEventListener("click", (event) => {
    if (event.target === els.editorModal) handleCollapseEditor();
  });
};

const cacheElements = () => {
  els.appRoot = document.getElementById("appRoot");
  els.deviceMeta = document.getElementById("deviceMeta");
  els.syncBtn = document.getElementById("syncBtn");
  els.reviewBtn = document.getElementById("reviewBtn");
  els.reviewDot = document.getElementById("reviewDot");
  els.reviewLabel = document.getElementById("reviewLabel");
  els.settingsBtn = document.getElementById("settingsBtn");
  els.banner = document.getElementById("banner");
  els.taskView = document.getElementById("taskView");
  els.chatView = document.getElementById("chatView");
  els.chatViewBtn = document.getElementById("chatViewBtn");
  els.backToTasksBtn = document.getElementById("backToTasksBtn");
  els.chatMessages = document.getElementById("chatMessages");
  els.chatForm = document.getElementById("chatForm");
  els.chatInput = document.getElementById("chatInput");
  els.chatSendBtn = document.getElementById("chatSendBtn");
  els.listTitle = document.getElementById("listTitle");
  els.listMeta = document.getElementById("listMeta");
  els.statusFilters = document.getElementById("statusFilters");
  els.tagFilters = document.getElementById("tagFilters");
  els.searchInput = document.getElementById("searchInput");
  els.sortSelect = document.getElementById("sortSelect");
  els.clearFiltersBtn = document.getElementById("clearFiltersBtn");
  els.board = document.getElementById("board");
  els.taskForm = document.getElementById("taskForm");
  els.titleInput = document.getElementById("titleInput");
  els.descriptionInput = document.getElementById("descriptionInput");
  els.tagsInput = document.getElementById("tagsInput");
  els.statusSelect = document.getElementById("statusSelect");
  els.statusHelper = document.getElementById("statusHelper");
  els.editorTitle = document.getElementById("editorTitle");
  els.editorHint = document.getElementById("editorHint");
  els.resetTaskBtn = document.getElementById("resetTaskBtn");
  els.syncHint = document.getElementById("syncHint");
  els.collapseEditorBtn = document.getElementById("collapseEditorBtn");
  els.newTaskBtn = document.getElementById("newTaskBtn");
  els.quickModal = document.getElementById("quickModal");
  els.quickTitleInput = document.getElementById("quickTitleInput");
  els.quickTagsInput = document.getElementById("quickTagsInput");
  els.quickSaveBtn = document.getElementById("quickSaveBtn");
  els.quickExpandBtn = document.getElementById("expandQuickBtn");
  els.closeQuickBtn = document.getElementById("closeQuickBtn");
  els.editorModal = document.getElementById("editorModal");
  els.settingsModal = document.getElementById("settingsModal");
  els.closeSettingsBtn = document.getElementById("closeSettingsBtn");
  els.saveSettingsBtn = document.getElementById("saveSettingsBtn");
  els.baseUrlInput = document.getElementById("baseUrlInput");
  els.agentBaseUrlInput = document.getElementById("agentBaseUrlInput");
  els.reviewTimeInput = document.getElementById("reviewTimeInput");
  els.userIdInput = document.getElementById("userIdInput");
  els.deviceIdInput = document.getElementById("deviceIdInput");
  els.toast = document.getElementById("toast");
};

const init = async () => {
  cacheElements();
  initStateFromStorage();
  setViewMode("tasks");
  renderStatusFilters();
  updateChatSendButton();
  bindEvents();

  try {
    await registerDevice();
    updateDeviceMeta();
    await syncTasks({ showToast: false });
  } catch (error) {
    updateDeviceMeta();
    showToast(error.message || "设备注册失败");
  }

  applyFilters();
  renderBoard();
  renderTagFilters();
  updateReviewMode();

  setInterval(checkReviewTime, 30000);
  checkReviewTime();
};

document.addEventListener("DOMContentLoaded", init);
