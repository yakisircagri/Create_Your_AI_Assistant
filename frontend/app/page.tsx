"use client";

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


  useEffect(() => {
    async function loadAgents() {
      try {
        const data = await getAgents();

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
  }, []);


  useEffect(() => {
    if (!selectedAgent) {
      setAgentTools([]);
      return;
    }

    async function loadAgentTools() {
      try {
        const data = await getAgentTools(selectedAgent.id);
        setAgentTools(data);
      } catch (error) {
        console.error(error);
        setAgentTools([]);
      }
    }

    loadAgentTools();
  }, [selectedAgent]);


  async function handleDeleteTool(toolId:number){
    if (!selectedAgent) {
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
      const data = await getConversations(selectedAgent.id);

      setConversations(data);

      if (data.length > 0) {
        setSelectedConversation(data[0]);
      } else {
        const conversation = await createConversation(
          selectedAgent.id,
          "New Conversation",
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
}, [selectedAgent]);


  useEffect(() => {
    if (!selectedConversation) {
      setMessages([]);
      return;
    }

    async function loadMessages() {
      try {
        const data = await getMessages(selectedConversation.id);
        setMessages(data);
      } catch (error) {
        console.error(error);
        setMessages([]);
      }
    }

    loadMessages();
  }, [selectedConversation]);


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
}, [selectedConversation]);



  async function handleNewConversation() {
  if (!selectedAgent) {
    alert("You must choose at least one agent!");
    return;
  }

  try {
    const conversation = await createConversation(
      selectedAgent.id,
      "New Conversation",
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
    await deleteConversation(conversationId);

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
    if (!selectedConversation || !message.trim() || sending) {
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
      );

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
      await deleteAgent(agentId);

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
    const agent = await createAgent(
      agentName.trim(),
      agentDescription.trim(),
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
        <aside className="flex w-72 flex-col border-r border-gray-200 bg-gray-50">

          {/* Logo */}
          <div className="px-5 py-5">
            <h1 className="text-xl font-semibold">
              Create Your Own AI Assistant
            </h1>
          </div>

          <div className="px-3">

            {/* MCP Servers */}
            <button
                className="mb-1 w-full rounded-lg px-3 py-2.5 text-left text-sm hover:bg-gray-200"
            >
              MCP Servers
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
                            {/* Agent Select */}
                            <button
                                onClick={() =>
                                    setSelectedAgent(agent)
                                }
                                className="min-w-0 flex-1 truncate px-3 py-2.5 text-left text-sm"
                            >
                              {agent.name}
                            </button>

                            {/* Delete Agent */}
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

          </div>

          {/* Recent Chats */}
          <div className="flex-1 overflow-y-auto px-3">

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
                  {/* Conversation */}
                  <button
                    onClick={() =>
                      setSelectedConversation(conversation)
                    }
                    className="min-w-0 flex-1 truncate px-3 py-2 text-left text-sm"
                  >
                    {conversation.title || "New Conversation"}
                  </button>

                  {/* Delete Conversation */}
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
                              : "max-w-xl text-sm leading-6 text-gray-700"
                        }
                    >
                      {item.content}
                    </div>

                  </div>
              ))}

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

      </main>
  );
}