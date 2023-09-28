import nest_asyncio
from langchain.agents import AgentType, initialize_agent
from langchain.agents.agent_toolkits import PlayWrightBrowserToolkit
from langchain.chat_models import ChatAnthropic
from langchain.tools.playwright.utils import create_async_playwright_browser

nest_asyncio.apply()
DEFAULT_STARTER_URL = {
    "url": "https://web.archive.org/web/20230428131116/https://www.cnn.com/world"
}


async def init_agent_chain(starter_url, llm):
    # tools
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=async_browser)
    tools = toolkit.get_tools()
    tools_by_name = {tool.name: tool for tool in tools}
    navigate_tool = tools_by_name["navigate_browser"]
    get_elements_tool = tools_by_name["get_elements"]  #

    await navigate_tool.arun(starter_url)
    # action
    # The browser is shared across tools, so the agent can interact in a stateful manner
    await get_elements_tool.arun(
        {"selector": ".container__headline", "attributes": ["innerText"]}
    )

    agent_chain = initialize_agent(
        tools,
        llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
    )
    return agent_chain


async def run(agent_chain, prompt):
    result = await agent_chain.arun(prompt)
    return result


if __name__ == "__main__":
    async_browser = create_async_playwright_browser()
    llm = ChatAnthropic(temperature=0)  # or any other LLM, e.g., ChatOpenAI(), OpenAI()
    init_agent_chain(async_browser, llm)
