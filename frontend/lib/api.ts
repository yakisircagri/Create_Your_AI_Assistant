const API_BASE_URL = "http://127.0.0.1:8000";

export type Agent = {
    id: number;
    name: string;
    description?: string | null;
    system_prompt?: string | null;
    model: string;
};

export type AgentTool = {
  id: number;
  name: string;
  description?: string | null;
  input_schema?: Record<string, unknown> | null;
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

function authHeaders(token: string) {
  return {
    Authorization: `Bearer ${token}`,
  };
}

function authJsonHeaders(token: string) {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

export async function getAgents(
    token : string,
): Promise<Agent[]> {

  const response = await fetch(
    `${API_BASE_URL}/api/agents`,
    {
      headers: authHeaders(token),
    },
  );

  if (!response.ok) {
    throw new Error("Agents could not be fetched");
  }

  return response.json();
}

export async function getConversations(
  agentId: number | undefined,
  token: string,
): Promise<Conversation[]> {
  const url = new URL(
    `${API_BASE_URL}/api/conversations`,
  );

  if (agentId !== undefined) {
    url.searchParams.set(
      "agent_id",
      String(agentId),
    );
  }

  const response = await fetch(
    url.toString(),
    {
      headers: authHeaders(token),
    },
  );

  if (!response.ok) {
    throw new Error(
      "Conversations could not be fetched",
    );
  }

  return response.json();
}

export async function createConversation(
  agentId: number,
  title: string = "New Conversation",
  token: string,
):Promise<Conversation> {
  const response = await fetch(`${API_BASE_URL}/api/conversations`,{
    method : "POST",
    headers: authJsonHeaders(token),
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
  token: string,
): Promise<Message[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/conversations/${conversationId}/messages`,
      {
      headers: authHeaders(token),
    },
  );

  if (!response.ok) {
    throw new Error("Messages could not be fetched");
  }

  return response.json();
}

export async function sendMessage(
  conversationId: number,
  content: string,
  token: string,
): Promise<{
  message: string;
  conversation_title?: string | null;
}> {
  const response = await fetch(
    `${API_BASE_URL}/api/conversations/${conversationId}/messages`,
    {
      method: "POST",
      headers: authJsonHeaders(token),
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

export type MCPDiscoverResponse = {
  server_id: number;
  server_name: string;
  connected: boolean;
  auth_required: boolean;
  connect_url?: string | null;
  tools: MCPTool[];
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
  token: string,
): Promise<MCPDiscoverResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/mcp/discover?server_id=${serverId}`,
    {
      method: "POST",
      headers: authHeaders(token),
    },
  );

  if (!response.ok) {
    const errorText = await response.text();

    console.error(
      "MCP DISCOVER ERROR:",
      response.status,
      errorText,
    );

    throw new Error(
      "MCP tools could not be discovered",
    );
  }

  return response.json();
}

export type MCPConnectResponse = {
  connected: boolean;
  authorization_url?: string | null;
  connection_id?: number | null;
};

export async function connectMcpServer(
  serverId: number,
  token: string,
): Promise<MCPConnectResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/mcp/${serverId}/connect`,
    {
      method: "POST",
      headers: authHeaders(token),
    },
  );

  if (!response.ok) {
    const errorText = await response.text();

    console.error(
      "MCP CONNECT ERROR:",
      response.status,
      errorText,
    );

    throw new Error(
      "MCP server connection could not be started",
    );
  }

  return response.json();
}

export async function getAgentTools(
  agentId: number,
  token: string,
): Promise<AgentTool[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/agents/${agentId}/tools`,
      {
          headers: authHeaders(token),
      }
  );

  if (!response.ok) {
    throw new Error("Agent tools could not be fetched");
  }

  return response.json();
}

export async function deleteConversation(
  conversationId: number,
  token: string,
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/conversations/${conversationId}`,
    {
      method: "DELETE",
      headers: authHeaders(token),
    },
  );

  if (!response.ok) {
    throw new Error(
      "Conversation could not be deleted",
    );
  }
}

export async function deleteAgent(
  agentId: number,
  token: string,
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/agents/${agentId}`,
    {
      method: "DELETE",
      headers: authHeaders(token),
    },
  );

  if (!response.ok) {
    throw new Error(
      "Agent could not be deleted",
    );
  }
}

export async function createAgent(
  name: string,
  description: string,
  system_prompt: string,
  model: string,
  token: string,
): Promise<Agent> {
  const response = await fetch(
    `${API_BASE_URL}/api/agents`,
    {
      method: "POST",
      headers: authJsonHeaders(token),
      body: JSON.stringify({
        name,
        description,
        system_prompt,
        model,
      }),
    },
  );

  if (!response.ok) {
    throw new Error(
      "Agent could not be created",
    );
  }

  return response.json();
}

export async function deleteAgentTool(
  agentId: number,
  toolId: number,
  token: string,
) {
  const response = await fetch(
    `${API_BASE_URL}/api/agents/${agentId}/tools/${toolId}`,
    {
      method: "DELETE",
      headers: authHeaders(token),
    },
  );

  if (!response.ok) {
    throw new Error(
      "Failed to delete agent tool",
    );
  }

  return response.json();
}

export async function updateAgentTools(
  agentId: number,
  toolIds: number[],
  token: string,
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/agents/${agentId}/tools`,
    {
      method: "POST",
      headers: authJsonHeaders(token),
      body: JSON.stringify({
        tool_ids: toolIds,
      }),
    },
  );

  if (!response.ok) {
    const errorText =
      await response.text();

    console.error(
      "UPDATE AGENT TOOLS ERROR:",
      response.status,
      errorText,
    );

    throw new Error(
      "Agent tools could not be updated",
    );
  }
}

export type AuthResponse = {
    access_token : string;
    token_type : string;
};

export type CurrentUser = {
    id : number;
    email : string;
};

export async function registerUser(
    email: string,
    password: string,
): Promise<AuthResponse> {
    const response = await fetch(
    `${API_BASE_URL}/api/auth/register`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email,
        password,
      }),
    },
  );

    if (!response.ok){
        const errorText = await response.text();
        console.error("REGISTER ERROR:", errorText);
        throw new Error("Registration failed");
    }

    return response.json();
}

export async function loginUser(
    email : string,
    password : string,
): Promise<AuthResponse> {
    const response = await fetch(
    `${API_BASE_URL}/api/auth/login`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email,
        password,
      }),
    },
  );

    if (!response.ok) {
    const errorText = await response.text();
    console.error("LOGIN ERROR:", errorText);
    throw new Error("Invalid email or password");
  }

    return response.json();
}

export async function getCurrentUser(
    token : string,
): Promise<CurrentUser> {
    const response = await fetch(
    `${API_BASE_URL}/api/auth/me`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  );

    if (!response.ok) {
    throw new Error("User could not be authenticated");
  }

    return response.json();
}



