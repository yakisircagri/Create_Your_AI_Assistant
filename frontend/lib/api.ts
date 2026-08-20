import * as string_decoder from "node:string_decoder";

const API_BASE_URL = "http://127.0.0.1:8000";

export type Agent = {
    id: number;
    name: string;
    description?: string | null;
    system_prompt?: string | null;
    model: string;
};

export type Conversation = {
  id: number;
  agent_id: number;
  title?: string | null;
};

export type Message = {
  id: number;
  conversation_id: number;
  role: string;
  content?: string | null;
}

export async function getAgents(): Promise<Agent[]> {
  const response = await fetch(`${API_BASE_URL}/api/agents`);

  if (!response.ok) {
    throw new Error("Agents could not be fetched");
  }

  return response.json();
}

export async function getConversations(
    agentId?:number,
): Promise<Conversation[]> {
  const url = new URL(`${API_BASE_URL}/api/conversations`);

  if (agentId !== undefined){
    url.searchParams.set("agent_id", String(agentId));
  }

  const response = await fetch(url.toString());

  if (!response.ok) {
    throw new Error("Conversations could not be fetched");
  }

  return response.json();
}

export async function createConversation(
  agentId: number,
  title: string = "New Conversation",
):Promise<Conversation> {
  const response = await fetch(`${API_BASE_URL}/api/conversations`,{
    method : "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body:JSON.stringify(
        {
          agent_id: agentId,
          title,
        }
    ),
  });

   if (!response.ok) {
    throw new Error("Conversation could not be created");
  }

   return response.json();
}

export async function getMessages(
  conversationId: number,
): Promise<Message[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/conversations/${conversationId}/messages`,
  );

  if (!response.ok) {
    throw new Error("Messages could not be fetched");
  }

  return response.json();
}

export async function sendMessage(
  conversationId: number,
  content: string,
): Promise<{ message: string }> {
  const response = await fetch(
    `${API_BASE_URL}/api/conversations/${conversationId}/messages`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        content,
      }),
    },
  );

  if (!response.ok) {
    throw new Error("Message could not be sent");
  }
  return response.json();
}

export type MCPTool = {
  id: number;
  name: string;
  description?: string | null;
  input_schema?: Record<string, unknown> | null;
};

export type MCPServer = {
  id: number;
  name: string;
  url: string;
  description?: string | null;
};

export async function getMcpServers(): Promise<MCPServer[]> {
  const response = await fetch(`${API_BASE_URL}/api/mcp`);

  if (!response.ok) {
    throw new Error("MCP servers could not be fetched");
  }
  return response.json();
}

export async function discoverMcpServer(
  serverId: number,
): Promise<{
  server_id: number;
  server_name: string;
  tools: MCPTool[];
}> {
  const response = await fetch(
    `${API_BASE_URL}/api/mcp/discover?server_id=${serverId}`,
    {
      method: "POST",
    },
  );

  if (!response.ok) {
    throw new Error("MCP tools could not be discovered");
  }
  return response.json();
}

export type AgentTool = {
  id: number;
  name: string;
  description?: string | null;
  input_schema?: Record<string, unknown> | null;
};

export async function getAgentTools(
  agentId: number,
): Promise<AgentTool[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/agents/${agentId}/tools`,
  );

  if (!response.ok) {
    throw new Error("Agent tools could not be fetched");
  }

  return response.json();
}

export async function deleteConversation(
  conversationId: number,
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/conversations/${conversationId}`,
    {
      method: "DELETE",
    },
  );

  if (!response.ok) {
    throw new Error("Conversation could not be deleted");
  }
}

export async function deleteAgent(
    agentId: number,
): Promise<void>{
  const response = await fetch(
      `${API_BASE_URL}/api/agents/${agentId}`,
      {
        method : "DELETE",
      },
  );

  if (!response.ok) {
    throw new Error("Agent could not be deleted");
  }
}

export async function createAgent(
  name: string,
  description: string,
  system_prompt: string,
  model: string,
):Promise<Agent>{
  const response = await fetch(
      `${API_BASE_URL}/api/agents`,
      {
        method : "POST",
        headers: {
        "Content-Type": "application/json",
      },
        body: JSON.stringify({
        name,
        description,
        system_prompt,
        model,
      }),
      },
  );

  if (!response.ok) {
    throw new Error("Agent could not be created");
  }

  return response.json();
}

export async function deleteAgentTool(
    agentId : number,
    toolId : number
){
    const response = await fetch(
        `${API_BASE_URL}/api/agents/${agentId}/tools/${toolId}`,
        {
            method : "DELETE",
        },
    );

    if (!response.ok) {
    throw new Error("Failed to delete agent tool");
  }

    return response.json();
}



