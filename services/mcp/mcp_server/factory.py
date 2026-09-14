from mcp.server.mcpserver import MCPServer

from config.constants import MCP_SERVER_NAME
from mcp_server.tools.background_tools import register_background_tools
from mcp_server.tools.file_tools import register_file_tools
from mcp_server.tools.session_tools import register_session_tools
from mcp_server.tools.shell_tools import register_shell_tools
from mcp_server.tools.system_tools import register_system_tools
from services.container import ServiceContainer


def create_mcp_server(container: ServiceContainer) -> MCPServer:
    mcp = MCPServer(MCP_SERVER_NAME)
    register_background_tools(mcp, container)
    register_file_tools(mcp, container)
    register_session_tools(mcp, container)
    register_shell_tools(mcp, container)
    register_system_tools(mcp, container)
    return mcp
