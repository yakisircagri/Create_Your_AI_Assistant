"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import {useEffect, useRef, useState} from "react";
import {
  Agent,
  AgentTool,
  Conversation,
  createAgent,
  deleteAgent,
  Message,
  createConversation,
  deleteConversation,
  getAgents,
  getAgentTools,
  deleteAgentTool,
  getConversations,
  getMessages,
  sendMessage,
  MCPServer,
  MCPTool,
  discoverMcpServer,
  connectMcpServer,
  getMcpServers,
  updateAgentTools,
  loginUser,
  registerUser,
  getCurrentUser,
  CurrentUser,
} from "../lib/api";

export default function Home() {

  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [agentsOpen, setAgentsOpen] = useState(false);

  const [agentTools, setAgentTools] = useState<AgentTool[]>([]);
  const [toolsOpen, setToolsOpen] = useState(false);

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);

  const [messages, setMessages] = useState<Message[]>([]);
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);

  const [agentModalOpen, setAgentModalOpen] = useState(false);

  const [agentName, setAgentName] = useState("");
  const [agentDescription, setAgentDescription] = useState("");
  const [agentSystemPrompt, setAgentSystemPrompt] = useState("");
  const [agentModel, setAgentModel] = useState("gpt-5.2");

  const [creatingAgent, setCreatingAgent] = useState(false);
  type MCPModalView = "search" | "tools";

  const [isMcpModalOpen, setIsMcpModalOpen] =
    useState(false);

  const [mcpModalView, setMcpModalView] =
    useState<MCPModalView>("search");

  const [mcpServers, setMcpServers] =
    useState<MCPServer[]>([]);

  const [mcpSearch, setMcpSearch] =
    useState("");

  const [
    selectedMcpServer,
    setSelectedMcpServer,
  ] = useState<MCPServer | null>(null);

  const [mcpTools, setMcpTools] =
    useState<MCPTool[]>([]);

  const [
    selectedMcpToolIds,
    setSelectedMcpToolIds,
  ] = useState<number[]>([]);

  const [
    existingAgentToolIds,
    setExistingAgentToolIds,
  ] = useState<number[]>([]);

  const [isLoadingMcpTools, setIsLoadingMcpTools] =
    useState(false);

  const [isAddingTools, setIsAddingTools] =
    useState(false);

  const [mcpSuccessMessage, setMcpSuccessMessage] =
  useState<string | null>(null);

  const [authMode, setAuthMode] =
  useState<"login" | "register">("login");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [authToken, setAuthToken] =
    useState<string | null>(null);

  const [currentUser, setCurrentUser] =
    useState<CurrentUser | null>(null);

  const [authError, setAuthError] =
    useState<string | null>(null);

  const [isAuthenticating, setIsAuthenticating] =
    useState(false);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const [authLoading, setAuthLoading] = useState(true);

  useEffect(() => {
    async function loadAgents() {
      try {
        if (!authToken) {
          return;
        }

        const data = await getAgents(authToken);

        setAgents(data);

        if (data.length > 0) {
          setSelectedAgent(data[0]);
        }
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    }

    loadAgents();
  }, [authToken]);


  useEffect(() => {
    if (!selectedAgent) {
      setAgentTools([]);
      return;
    }

    async function loadAgentTools() {
      try {
        if (!authToken) {
          return;
        }

        const data = await getAgentTools(
          selectedAgent.id,
          authToken,
        );
        setAgentTools(data);
      } catch (error) {
        console.error(error);
        setAgentTools([]);
      }
    }

    loadAgentTools();
  }, [selectedAgent,authToken]);


  async function handleDeleteTool(toolId:number){
    if (!selectedAgent || !authToken) {
    return;
    }

    const tool = agentTools.find(
        (item) => item.id == toolId
    );

    if (!tool) {
    return;
    }

    const confirmed = window.confirm(
    `Remove tool "${tool.name}" from this agent?`,
    );

    if(!confirmed){
      return;
    }

    try{
      await deleteAgentTool(
          selectedAgent.id,
          toolId,
          authToken,
      );

      setAgentTools((current) =>
      current.filter(
        (item) => item.id !== toolId,
      ),
    );

    }catch(error){
      console.error(error);
      alert("Tool could not be removed.");
    }

  }


    useEffect(() => {
  if (!selectedAgent) {
    setConversations([]);
    setSelectedConversation(null);
    setMessages([]);
    return;
  }

  async function loadConversations() {
    try {
      if (!authToken) {
        return;
      }

      const data = await getConversations(
        selectedAgent.id,
        authToken,
      );

      setConversations(data);

      if (data.length > 0) {
        setSelectedConversation(data[0]);
      } else {
        const conversation = await createConversation(
          selectedAgent.id,

          "New Conversation",
          authToken,
        );

        setConversations([conversation]);
        setSelectedConversation(conversation);
        setMessages([]);
      }
    } catch (error) {
      console.error(error);
      setConversations([]);
      setSelectedConversation(null);
      setMessages([]);
    }
  }

  loadConversations();
}, [selectedAgent,authToken]);


  useEffect(() => {
    if (!selectedConversation) {
      setMessages([]);
      return;
    }

    async function loadMessages() {
      try {
        if (!authToken) {
        return;
      }

      const data = await getMessages(
        selectedConversation.id,
        authToken,
      );
        setMessages(data);
      } catch (error) {
        console.error(error);
        setMessages([]);
      }
    }

    loadMessages();
  }, [selectedConversation,authToken]);


useEffect(() => {
  function handleGlobalKeyDown(event: KeyboardEvent) {
    if (
      !selectedConversation ||
      sending ||
      event.ctrlKey ||
      event.metaKey ||
      event.altKey
    ) {
      return;
    }

    const target = event.target as HTMLElement | null;

    if (
      target?.tagName === "INPUT" ||
      target?.tagName === "TEXTAREA" ||
      target?.isContentEditable
    ) {
      return;
    }

    if (event.key.length === 1) {
      textareaRef.current?.focus();
    }
  }

  window.addEventListener("keydown", handleGlobalKeyDown);

  return () => {
    window.removeEventListener("keydown", handleGlobalKeyDown);
  };
}, [selectedConversation,sending]);


useEffect(() => {
  if (messages.length === 0) {
    return;
  }

  messagesEndRef.current?.scrollIntoView({
    behavior: "instant",
    block: "end",
  });
}, [messages]);


  async function handleNewConversation() {
  if (!selectedAgent || !authToken) {
    alert("You must choose at least one agent!");
    return;
  }

  try {
    const conversation = await createConversation(
      selectedAgent.id,
      "New Conversation",
      authToken,
    );

    setConversations((current) => [
      conversation,
      ...current.filter(
        (item) => item.id !== conversation.id,
      ),
    ]);

    setSelectedConversation(conversation);
    setMessages([]);
  } catch (error) {
    console.error(error);
    alert("Conversation couldnt be established!");
  }
}


  async function handleDeleteConversation(
  conversationId: number,
) {
  const confirmed = window.confirm(
    "Are you sure you want to delete this conversation?",
  );

  if (!confirmed) {
    return;
  }

  try {
      if (!authToken) {
      return;
    }

    await deleteConversation(
      conversationId,
      authToken,
    );

    setConversations((current) =>
      current.filter(
        (conversation) =>
          conversation.id !== conversationId,
      ),
    );

    if (
      selectedConversation?.id === conversationId
    ) {
      setSelectedConversation(null);
      setMessages([]);
    }
  } catch (error) {
    console.error(error);
    alert("Conversation could not be deleted.");
  }
}


  async function handleSendMessage() {
    if (!selectedConversation || !message.trim() || sending ||!authToken) {
      return;
    }

    const content = message.trim();

    setMessage("");
    setSending(true);

    const temporaryUserMessage: Message = {
      id: Date.now(),
      conversation_id: selectedConversation.id,
      role: "user",
      content,
    };

    setMessages((current) => [
      ...current,
      temporaryUserMessage,
    ]);

    try {
      const response = await sendMessage(
          selectedConversation.id,
          content,
          authToken,
      );

      if (response.conversation_title) {
        setConversations((current) =>
          current.map((conversation) =>
            conversation.id === selectedConversation.id
              ? {
                  ...conversation,
                  title: response.conversation_title,
                }
              : conversation,
          ),
        );
      }

      const assistantMessage: Message = {
        id: Date.now() + 1,
        conversation_id: selectedConversation.id,
        role: "assistant",
        content: response.message,
      };

      setMessages((current) => [
        ...current,
        assistantMessage,
      ]);
    } catch (error) {
      console.error(error);

      setMessage(content);
      alert("Message couldnt be sent");
    } finally {
      setSending(false);
    }
  }

  async function handleDeleteAgent(agentId: number) {
    const agent = agents.find(
        (item) => item.id == agentId
    );

    if (!agent) {
      return;
    }

    const confirmed = window.confirm(
        `Delete agent "${agent.name}"? This will also delete its conversations.`,
    );

    if (!confirmed) {
      return;
    }

    try {
      if (!authToken) {
      return;
    }

    await deleteAgent(
      agentId,
      authToken,
    );

      setAgents((current) =>
          current.filter((item) => item.id !== agentId),
      );

      if (selectedAgent?.id === agentId) {
        setSelectedAgent(null);
        setSelectedConversation(null);
        setConversations([]);
        setMessages([]);
      }
    } catch (error) {
      console.error(error);
      alert("Agent could not be deleted.");
    }
  }


  async function handleCreateAgent() {
  if (!agentName.trim()) {
    return;
  }

  setCreatingAgent(true);

  try {
    if (!authToken) {
      return;
    }

    const agent = await createAgent(
      agentName.trim(),
      agentDescription.trim(),
      agentSystemPrompt.trim(),
      agentModel,
      authToken,
    );

    setAgents((current) => [
      agent,
      ...current.filter((item) => item.id !== agent.id),
    ]);

    setAgentModalOpen(false);
    setAgentName("");
    setAgentDescription("");

    setSelectedAgent(agent);
  } catch (error) {
    console.error(error);
    alert("Agent could not be created.");
  } finally {
    setCreatingAgent(false);
  }
}

  async function handleOpenMcpSearch(){
      try{
        const servers = await getMcpServers();

        setMcpServers(servers);
        setMcpModalView("search");
        setSelectedMcpServer(null);
        setMcpTools([]);
        setSelectedMcpToolIds([]);
        setIsMcpModalOpen(true);
      }catch (error) {
      console.error(error);
    }}

  async function handleViewMcpTools(
      server : MCPServer,
  ){
    try{
      setIsLoadingMcpTools(true);
      setSelectedMcpServer(server);

      if (!authToken) {
        return;
      }

      const result = await discoverMcpServer(
        server.id,
        authToken,
      );

      if (
        result.auth_required &&
        !result.connected
      ) {
        const connectionResult =
          await connectMcpServer(
            server.id,
            authToken,
          );

        if (connectionResult.authorization_url) {
          window.location.href =
            connectionResult.authorization_url;

          return;
        }
      }

      setMcpTools(result.tools);

      if(selectedAgent){
        const agentTools = await getAgentTools(
            selectedAgent.id,
            authToken,
        );

        const agentToolIds = agentTools.map(
            (tool) => tool.id,
        );

        setExistingAgentToolIds(
            agentToolIds,
        );

        const selectedIds = result.tools
          .filter((tool) =>
          agentToolIds.includes(tool.id),
          ).map((tool) => tool.id)

        setSelectedMcpToolIds(
            selectedIds,
        );
      }else{
        setSelectedMcpToolIds([])
      }

      setMcpModalView("tools")

    }catch (error) {
    console.error(error);
  } finally {
    setIsLoadingMcpTools(false);
  }
  }

  function handleToggleMcpTool(
    toolId: number,
  ) {
    setSelectedMcpToolIds((current) =>
      current.includes(toolId)
        ? current.filter(
            (id) => id !== toolId,
          )
        : [...current, toolId],
    );
  }

  async function handleApplyMcpTools(){
    if(!selectedAgent || !selectedMcpServer || !authToken){
      return;
    }

    try {
      setIsAddingTools(true);

      const currentAgentTools =
          await getAgentTools(selectedAgent.id,authToken);

      const currentServerToolIds =
          mcpTools.map((tool) => tool.id);

      const otherServerToolIds =
          currentAgentTools.filter(
              (tool) =>
                  !currentServerToolIds.includes(tool.id),
          ).map((tool) => tool.id)

      const finalToolIds = [
      ...otherServerToolIds,
      ...selectedMcpToolIds,
    ];

      await updateAgentTools(
          selectedAgent.id,
          finalToolIds,
          authToken,
      );

      const updatedTools =
          await getAgentTools(selectedAgent.id,authToken)

      setAgentTools(updatedTools);

      setExistingAgentToolIds(
          updatedTools.map((tool) => tool.id),
      )

      setMcpSuccessMessage("Tool selection updated successfully.");

      setTimeout(() => {
        setMcpSuccessMessage(null);
      },2000);

    }catch(error){
      console.error(error);
    }
    finally{
      setIsAddingTools(false);
    }
  }

  function handleBackToMcpSearch(){
    setMcpModalView("search");
    setSelectedMcpServer(null);
    setMcpTools([]);
    setSelectedMcpToolIds([]);
  }

  const filteredMcpServers =
      mcpServers.filter((server) => {
        const query =
            mcpSearch.toLowerCase();

        return (
        server.name
          .toLowerCase()
          .includes(query) ||
        server.description
          ?.toLowerCase()
          .includes(query)
        );
      });


useEffect(() => {
  async function checkAuth() {
    const token =
      localStorage.getItem("access_token");

    if (!token) {
      setAuthLoading(false);
      return;
    }

    try {
      const user =
        await getCurrentUser(token);

      setAuthToken(token);
      setCurrentUser(user);
    } catch {
      localStorage.removeItem("access_token");
      setAuthToken(null);
      setCurrentUser(null);
    } finally {
      setAuthLoading(false);
    }
  }

  checkAuth();
}, []);


  async function handleAuthSubmit() {
    try {
      setIsAuthenticating(true);
      setAuthError(null);

      const result =
          authMode === "login"
          ? await loginUser(email, password)
          : await registerUser(email, password);

      localStorage.setItem(
      "access_token",
      result.access_token,
    );

      setAuthToken(result.access_token);

      const user = await getCurrentUser(
          result.access_token
      );

      setCurrentUser(user);

      setEmail("");
      setPassword("");

    }catch(error){
      console.error(error);

      setAuthError(
        authMode === "login"
          ? "Invalid email or password."
          : "Account could not be created.",
      );
    }
    finally{
      setIsAuthenticating(false)
    }
  }

  function handleLogout() {
  localStorage.removeItem("access_token");

  setAuthToken(null);
  setCurrentUser(null);

  setAgents([]);
  setSelectedAgent(null);
  setConversations([]);
  setSelectedConversation(null);
  setMessages([]);
  setAgentTools([]);
}

  if (authLoading) {
    return (
      <main className="flex h-screen items-center justify-center bg-white">
        <p className="text-sm text-gray-400">
          Loading...
        </p>
      </main>
    );
  }
  
  if (!currentUser) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-white">
        <div className="w-full max-w-sm px-6">

          <h1 className="mb-2 text-2xl font-semibold">
            Build Your AI Agent
          </h1>

          <p className="mb-6 text-sm text-gray-500">
            {authMode === "login"
              ? "Sign in to continue."
              : "Create your account."}
          </p>

          {authError && (
            <div className="mb-4 rounded-lg bg-gray-100 px-3 py-2 text-sm">
              {authError}
            </div>
          )}

          <div className="space-y-3">

            <input
              type="email"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              placeholder="Email"
              className="w-full rounded-lg border px-3 py-2.5"
            />

            <input
              type="password"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              placeholder="Password"
              className="w-full rounded-lg border px-3 py-2.5"
            />

            <button
              onClick={handleAuthSubmit}
              disabled={
                !email ||
                !password ||
                isAuthenticating
              }
              className="w-full rounded-lg bg-black px-3 py-2.5 text-sm text-white disabled:opacity-40"
            >
              {isAuthenticating
                ? "Please wait..."
                : authMode === "login"
                  ? "Sign In"
                  : "Create Account"}
            </button>

          </div>

          <button
            onClick={() => {
              setAuthMode(
                authMode === "login"
                  ? "register"
                  : "login",
              );

              setAuthError(null);
            }}
            className="mt-4 text-sm text-gray-600 hover:text-black"
          >
            {authMode === "login"
              ? "Don't have an account? Sign Up"
              : "Already have an account? Sign In"}
          </button>

        </div>
      </main>
    );
  }

  if (loading) {
    return (
        <main className="flex h-screen items-center justify-center">
          <p className="text-sm text-gray-500">
            Loading...
          </p>
        </main>
    );
  }


  return (
      <main className="flex h-screen bg-white text-gray-900">
        {/* SIDEBAR */}
        <aside className="flex h-screen w-72 flex-col border-r border-gray-200 bg-gray-50">
          <div className="shrink-0 px-5 py-5">
            <h1 className="text-xl font-semibold">
              Build Your Intelligent Assistant
            </h1>
          </div>

          <div className="sidebar-scroll min-h-0 flex-1 overflow-y-scroll">

            <div className="px-3">

              {/* MCP Search */}
              <button
                onClick={handleOpenMcpSearch}
                className="mb-1 flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-left text-sm hover:bg-gray-200 disabled:cursor-not-allowed disabled:text-gray-400"
              >
                MCP Server
              </button>

              {/* Tools */}
              <button
                onClick={() =>
                  setToolsOpen((current) => !current)
                }
                disabled={!selectedAgent}
                className="mb-1 flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-left text-sm hover:bg-gray-200 disabled:cursor-not-allowed disabled:text-gray-400"
              >
                <span>Tools</span>

                <span className="text-xs">
                  {toolsOpen ? "⌃" : "⌄"}
                </span>
              </button>

              {/* Tools List */}
              {toolsOpen && (
                <div className="mb-3 space-y-1 px-2">
                  {agentTools.length === 0 ? (
                    <p className="px-2 py-2 text-xs text-gray-400">
                      No tools added to this agent.
                    </p>
                  ) : (
                    agentTools.map((tool) => (
                      <div
                        key={tool.id}
                        className="flex items-center rounded-lg px-2 py-2 hover:bg-gray-100"
                      >
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium text-gray-700">
                            {tool.name}
                          </p>

                          {tool.description && (
                            <p className="mt-0.5 line-clamp-2 text-xs text-gray-400">
                              {tool.description}
                            </p>
                          )}
                        </div>

                        <button
                          onClick={() =>
                            handleDeleteTool(tool.id)
                          }
                          className="ml-2 flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-gray-400 hover:bg-gray-200 hover:text-red-600"
                          title="Remove tool"
                        >
                          −
                        </button>
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* My Agents */}
              <button
                onClick={() =>
                  setAgentsOpen((current) => !current)
                }
                className="mb-1 flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-left text-sm font-medium hover:bg-gray-200"
              >
                <span>My Agents</span>

                <span className="text-xs">
                  {agentsOpen ? "⌃" : "⌄"}
                </span>
              </button>

              {/* Agents List */}
              {agentsOpen && (
                <div className="mb-2 space-y-1 px-2">
                  {agents.length === 0 ? (
                    <p className="px-2 py-2 text-xs text-gray-400">
                      No agents available.
                    </p>
                  ) : (
                    agents.map((agent) => (
                      <div
                        key={agent.id}
                        className={`flex items-center rounded-lg ${
                          selectedAgent?.id === agent.id
                            ? "bg-gray-200"
                            : "hover:bg-gray-200"
                        }`}
                      >
                        <button
                          onClick={() =>
                            setSelectedAgent(agent)
                          }
                          className="min-w-0 flex-1 truncate px-3 py-2.5 text-left text-sm"
                        >
                          {agent.name}
                        </button>

                        <button
                          onClick={() =>
                            handleDeleteAgent(agent.id)
                          }
                          className="mr-2 flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-gray-400 hover:bg-gray-300 hover:text-red-600"
                          title="Delete agent"
                        >
                          🗑
                        </button>
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Add New Agent */}
              <button
                onClick={() => setAgentModalOpen(true)}
                className="mb-3 w-full rounded-lg px-3 py-2.5 text-left text-sm font-medium hover:bg-gray-200"
              >
                + Add New Agent
              </button>

              {/* New Conversation */}
              <button
                onClick={handleNewConversation}
                disabled={!selectedAgent}
                className="mb-4 w-full rounded-lg bg-gray-900 px-3 py-2.5 text-left text-sm font-medium text-white hover:bg-gray-800 disabled:cursor-not-allowed disabled:bg-gray-300"
              >
                + New Conversation
              </button>

              {/* Recent Chats */}
              <p className="px-3 py-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
                Recent Chats
              </p>

              {conversations.length === 0 ? (
                <p className="px-3 py-2 text-sm text-gray-400">
                  No conversations yet.
                </p>
              ) : (
                conversations.map((conversation) => (
                  <div
                    key={conversation.id}
                    className={`mb-1 flex items-center rounded-lg ${
                      selectedConversation?.id === conversation.id
                        ? "bg-gray-200"
                        : "hover:bg-gray-200"
                    }`}
                  >
                    <button
                      onClick={() =>
                        setSelectedConversation(conversation)
                      }
                      className="min-w-0 flex-1 truncate px-3 py-2 text-left text-sm"
                    >
                      {conversation.title || "New Conversation"}
                    </button>

                    <button
                      onClick={() =>
                        handleDeleteConversation(conversation.id)
                      }
                      className="mr-2 flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-gray-400 hover:bg-gray-300 hover:text-red-600"
                      title="Delete conversation"
                    >
                      🗑
                    </button>
                  </div>
                ))
              )}

            </div>
          </div>
        </aside>

        {/* MAIN CHAT */}
        <section className="flex min-w-0 flex-1 flex-col">

          {/* Header */}
          <header className="flex h-16 items-center border-b border-gray-200 px-6">
            <div>

              <h2 className="font-semibold">
                {selectedAgent?.name || "Choose an agent"}
              </h2>

              <p className="text-xs text-gray-500">
                {selectedConversation
                    ? selectedConversation.title
                    : "Add new conversation"}
              </p>

            </div>
          </header>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-6 py-8">

            <div className="mx-auto flex max-w-3xl flex-col gap-6">

              {/* No conversation */}
              {!selectedConversation && (
                  <div className="flex flex-1 items-center justify-center py-32">

                    <div className="text-center">

                      <h3 className="text-xl font-semibold">
                        {selectedAgent
                            ? "Add new conversation"
                            : "Choose an agent"}
                      </h3>

                      <p className="mt-2 text-sm text-gray-500">
                        {selectedAgent
                            ? "You can start to chat by pressing the New Conversation button."
                            : "You must choose at least one agent to chat."}
                      </p>

                    </div>

                  </div>
              )}

              {/* Messages */}
              {messages
                .filter(
                  (item) =>
                    item.role === "user" ||
                    item.role === "assistant",
                ).map((item) => (
                  <div
                      key={item.id}
                      className={
                        item.role === "user"
                            ? "flex justify-end"
                            : "flex justify-start"
                      }
                  >

                    <div
                      className={
                        item.role === "user"
                          ? "max-w-xl rounded-2xl bg-gray-900 px-4 py-3 text-sm text-white"
                          : "min-w-0 max-w-xl text-sm leading-6 text-gray-700"
                      }
                    >
                      {item.role === "user" ? (
                        item.content
                      ) : (
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            p: ({children}) => (
                              <p className="my-2 break-words">
                                {children}
                              </p>
                            ),

                            ul: ({children}) => (
                              <ul className="my-2 list-disc space-y-1 pl-5">
                                {children}
                              </ul>
                            ),

                            ol: ({children}) => (
                              <ol className="my-2 list-decimal space-y-1 pl-5">
                                {children}
                              </ol>
                            ),

                            li: ({children}) => (
                              <li className="break-words">
                                {children}
                              </li>
                            ),

                            h1: ({children}) => (
                              <h1 className="my-3 text-lg font-semibold">
                                {children}
                              </h1>
                            ),

                            h2: ({children}) => (
                              <h2 className="my-3 text-base font-semibold">
                                {children}
                              </h2>
                            ),

                            h3: ({children}) => (
                              <h3 className="my-2 font-semibold">
                                {children}
                              </h3>
                            ),

                            table: ({ children }) => (
                              <div className="my-3 w-full overflow-x-auto">
                                <table className="w-full table-auto border-collapse text-xs">
                                  {children}
                                </table>
                              </div>
                            ),

                            th: ({ children }) => (
                              <th className="border px-2 py-2 text-left align-top font-semibold">
                                {children}
                              </th>
                            ),

                            td: ({ children }) => (
                              <td className="border px-2 py-2 text-left align-top">
                                {children}
                              </td>
                            ),

                            pre: ({children}) => (
                              <pre className="my-3 max-w-full overflow-x-auto rounded-lg bg-gray-100 p-3 text-sm">
                                {children}
                              </pre>
                            ),

                            code: ({children}) => (
                              <code className="break-words">
                                {children}
                              </code>
                            ),
                          }}
                        >
                          {item.content || ""}
                        </ReactMarkdown>
                      )}
                    </div>

                  </div>
              ))}

              <div ref={messagesEndRef} />

              {/* Thinking */}
              {sending && (
                  <div className="flex justify-start">

                    <div className="flex items-center gap-2 text-sm text-gray-500">

                      <span>Thinking</span>

                      <span className="flex gap-1">

                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.3s]"/>

                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.15s]"/>

                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400"/>

                </span>

                    </div>

                  </div>
              )}

            </div>
          </div>

          {/* Message Input */}
          <div className="border-t border-gray-200 px-6 py-4">

            <div
                className="mx-auto flex max-w-3xl items-end rounded-2xl border border-gray-300 bg-white px-4 py-3 shadow-sm">

          <textarea
              value={message}
              ref={textareaRef}
              onChange={(event) =>
                  setMessage(event.target.value)
              }
              onKeyDown={(event) => {
                if (
                    event.key === "Enter" &&
                    !event.shiftKey
                ) {
                  event.preventDefault();
                  handleSendMessage();
                }
              }}
              placeholder={
                selectedConversation
                    ? "Send your message..."
                    : "Start a conversation first..."
              }
              disabled={
                  !selectedConversation || sending
              }
              rows={1}
              className="max-h-32 flex-1 resize-none bg-transparent text-sm outline-none placeholder:text-gray-400 disabled:cursor-not-allowed"
          />

              <button
                  onClick={handleSendMessage}
                  disabled={
                      !message.trim() ||
                      !selectedConversation ||
                      sending
                  }
                  className="ml-3 flex h-9 w-9 items-center justify-center rounded-full bg-gray-900 text-white disabled:cursor-not-allowed disabled:bg-gray-300"
              >
                ↑
              </button>

            </div>
          </div>

        </section>

        {/* Add New Agent Modal */}
        {agentModalOpen && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 px-4">

              <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">

                {/* Modal Header */}
                <div className="mb-5">
                  <h2 className="text-lg font-semibold">
                    Add New Agent
                  </h2>

                  <p className="mt-1 text-sm text-gray-500">
                    Give your agent a name and description.
                  </p>
                </div>

                {/* Agent Name */}
                <div className="mb-4">

                  <label className="mb-1.5 block text-sm font-medium text-gray-700">
                    Agent Name
                  </label>

                  <input
                      type="text"
                      value={agentName}
                      onChange={(event) =>
                          setAgentName(event.target.value)
                      }
                      placeholder="e.g. Travel Assistant"
                      className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm outline-none focus:border-gray-500"
                  />

                </div>

                {/* Agent Description */}
                <div className="mb-6">

                  <label className="mb-1.5 block text-sm font-medium text-gray-700">
                    Description
                  </label>

                  <textarea
                      value={agentDescription}
                      onChange={(event) =>
                          setAgentDescription(event.target.value)
                      }
                      placeholder="Describe what this agent does..."
                      rows={4}
                      className="w-full resize-none rounded-lg border border-gray-300 px-3 py-2.5 text-sm outline-none focus:border-gray-500"
                  />

                </div>

                {/* Actions */}
                <div className="flex justify-end gap-2">

                  <button
                      type="button"
                      onClick={() => {
                        setAgentModalOpen(false);
                        setAgentName("");
                        setAgentDescription("");
                      }}
                      disabled={creatingAgent}
                      className="rounded-lg px-4 py-2.5 text-sm font-medium text-gray-600 hover:bg-gray-100 disabled:cursor-not-allowed disabled:text-gray-400"
                  >
                    Cancel
                  </button>

                  <button
                      type="button"
                      onClick={handleCreateAgent}
                      disabled={
                          !agentName.trim() ||
                          creatingAgent
                      }
                      className="rounded-lg bg-gray-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-gray-800 disabled:cursor-not-allowed disabled:bg-gray-300"
                  >
                    {creatingAgent
                        ? "Adding..."
                        : "Add Agent"}
                  </button>

                </div>

              </div>
            </div>
        )}

        {isMcpModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
            <div className="w-full max-w-xl rounded-2xl bg-white p-6 shadow-xl">

              {mcpModalView === "search" && (
                <>
                  <div className="mb-5 flex items-center justify-between">
                    <div>
                      <h2 className="text-xl font-semibold">
                        MCP Servers
                      </h2>

                      <p className="mt-1 text-sm text-gray-500">
                        Search MCP servers and add
                        tools to your agent.
                      </p>
                    </div>

                    <button
                      onClick={() =>
                        setIsMcpModalOpen(false)
                      }
                      className="rounded-lg px-3 py-2 text-sm text-gray-500 hover:bg-gray-100"
                    >
                      Close
                    </button>
                  </div>

                  <input
                    value={mcpSearch}
                    onChange={(event) =>
                      setMcpSearch(
                        event.target.value,
                      )
                    }
                    placeholder="Search MCP servers..."
                    className="mb-4 w-full rounded-xl border px-4 py-3 outline-none focus:ring-2"
                  />

                  <div className="max-h-[420px] space-y-3 overflow-y-auto">
                    {filteredMcpServers.map(
                      (server) => (
                        <div
                          key={server.id}
                          className="rounded-xl border p-4"
                        >
                          <div className="flex items-start justify-between gap-4">
                            <div>
                              <h3 className="font-medium">
                                {server.name}
                              </h3>

                              {server.description && (
                                <p className="mt-1 text-sm text-gray-500">
                                  {
                                    server.description
                                  }
                                </p>
                              )}
                            </div>

                            <button
                              disabled={
                                isLoadingMcpTools
                              }
                              onClick={() =>
                                handleViewMcpTools(
                                  server,
                                )
                              }
                              className="shrink-0 rounded-lg border px-3 py-2 text-sm font-medium hover:bg-gray-50 disabled:opacity-50"
                            >
                              View Tools
                            </button>
                          </div>
                        </div>
                      ),
                    )}
                  </div>
                </>
              )}

              {mcpModalView === "tools" &&
                selectedMcpServer && (
                  <>
                    <div className="mb-5">
                      <button
                        onClick={
                          handleBackToMcpSearch
                        }
                        className="mb-4 flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-black"
                      >
                        ← Back
                      </button>

                      <h2 className="text-xl font-semibold">
                        {selectedMcpServer.name}
                      </h2>

                      {selectedMcpServer.description && (
                        <p className="mt-1 text-sm text-gray-500">
                          {
                            selectedMcpServer.description
                          }
                        </p>
                      )}
                    </div>

                    {mcpSuccessMessage && (
                      <div className="mb-4 rounded-lg bg-gray-100 px-3 py-2 text-sm text-gray-700">
                        {mcpSuccessMessage}
                      </div>
                    )}

                    <div className="max-h-[420px] space-y-3 overflow-y-auto">
                      {mcpTools.map((tool) => {

                        const checked =
                            selectedMcpToolIds.includes(tool.id);

                        return (
                          <label
                            key={tool.id}
                            className="flex cursor-pointer items-start gap-3 rounded-xl border p-4 hover:bg-gray-50"
                          >
                            <input
                              type="checkbox"
                              checked={checked}
                              onChange={() =>
                                handleToggleMcpTool(tool.id)
                              }
                              className="mt-1"
                            />

                            <div>
                              <div className="font-medium">
                                {tool.name}
                              </div>

                              {tool.description && (
                                <p className="mt-1 text-sm text-gray-500">
                                  {tool.description}
                                </p>
                              )}
                            </div>
                          </label>
                        );
                      })}

                    </div>

                    <div className="mt-6 flex justify-end">
                      <button
                        onClick={
                          handleApplyMcpTools
                        }
                        disabled={
                          selectedMcpToolIds.length ===
                            0 ||
                          isAddingTools
                        }
                        className="rounded-xl bg-black px-5 py-3 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        {isAddingTools
                          ? "Applying..."
                          : `Apply `}
                      </button>
                    </div>
                  </>
                )}
            </div>
          </div>
        )}

      </main>
  );
}