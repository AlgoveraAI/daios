The intersection of AI and Crypto is a popular topic these days, with many exploring what the potential use cases may be. For one, it’s hoped that Crypto can bring decentralization to cloud providers like OpenAI. Furthermore, the Crypto world has been interested in autonomous agents and organizations for a relatively long time, and provides infrastructure, frameworks and tooling towards achieving this. On the other hand, recent advances with LLMs in the AI space have enabled agents to do more useful things, such as coding or increasing general productivity. Valory has awarded a grant to Algovera to explore and enhance the benefits of combining Crypto and LLM agent frameworks.

# Background to LLM x Crypto Agent Frameworks

LLMs represent a new computing platform as a result of useful capabilities like in-context learning, generalization to samples outside of the training distribution, and reasoning that emerge above a certain size. LLM programming is the act of building on top of these general personalizable reasoning engines, and frameworks such as LangChain, Llama Index and BabyAGI have been widely adopted for this purpose. Typically, the LLM is just one component of a larger AI system that includes other building blocks such as short-term memory, long-term memory (e.g. vector databases) and tools. These enable the creation of useful apps like chains (workflows), agents and multi-agent systems. Services for deploying these agents are in the early stages of development and tend to focus on centralized approaches, which creates questions around who ultimately owns and governs these apps.

Crypto agent frameworks such as [Open Autonomous Economic Agent (AEA)](https://github.com/valory-xyz/open-aea) and [Open Autonomy](https://docs.autonolas.network/open-autonomy/) have been under development for a relatively long period of time compared to LLM agent frameworks. Open Autonomy is a framework for the creation of agent services: off-chain autonomous services which run as a multi-agent-system and offer enhanced functionalities on-chain. Open Autonomy uses finite state machines (FSMs), which are more flexible and powerful versions of chains or workflows. Most importantly, agent services are decentralized, trust-minimized, transparent, and robust. Recently, Valory awarded a grant to Algovera to facilitate the implementation of new, powerful building blocks of modern AI systems within Open Autonomy.

For a deeper dive on LLM x Crypto agent frameworks, you can watch [this](https://www.youtube.com/watch?v=QvKmVq9micE) recent presentation for Valory’s AI x Crypto mini-conference. 

# Valory Chat & Question Answering Assistant 

To demonstrate what you can build with building blocks such as LLM skills, short-term memory and long-term memory, we created two apps: Chat and Question Answering. Because they use the Olas stack, both of these apps have the capacity to be run in  a decentralized manner. This is a key differentiator between these and other AI chat apps. The Chat app makes use of an LLM with short-term memory to keep track of the chat history of the conversation, which allows users to ask follow up queries and allows the assistant to correct errors in previous responses. The Question Answering app uses an LLM together with a vector database that acts as long-term memory. We created embeddings of Valory’s technical documentation, and stored the result in a vector database on IPFS. When a user query is submitted to the Question Answering app, the vector embedding is retrieved from IPFS. Similarity search is then performed to select appropriate documents, and these documents are used to generate answers.

For more information, check out the [video demo](https://www.loom.com/share/6fa457b271df45328dec5f9c28660315?sid=0f8f386d-6c06-4a77-96c2-be6b41f75f74). 

# Run 

## System requirements

- Python `>=3.7`
- [Tendermint](https://docs.tendermint.com/v0.34/introduction/install.html) `==0.34.19`
- [IPFS node](https://docs.ipfs.io/install/command-line/#official-distributions) `==0.6.0`
- [Pip](https://pip.pypa.io/en/stable/installation/)
- [Poetry](https://python-poetry.org/)
- [Docker Engine](https://docs.docker.com/engine/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)

Alternatively, you can fetch this docker image with the relevant requirements satisfied:

> **_NOTE:_**  Tendermint and IPFS dependencies are missing from the image at the moment.

```bash
docker pull valory/open-autonomy-user:latest
docker container run -it valory/open-autonomy-user:latest
```

## This repository contains:
Connections
- `chat_completion`: connection betweeen OpenAI API calls and the agent

Skills
- `chat_completion_abci`: A skill that adds `embedding` given a file, `chat` over the created embedding, maintains `chat_history` of the chat

Agent
- `chat_completion_agent`: An agent that runs on top of the `chat_completion_abci` skill

Service
- `chat_completion_local`: A service built on top of `chat_completion_agent` 

## How to use

##### The agent
1. Git clone the repository
`git clone git@github.com:AlgoveraAI/daios.git`

2. Sync the third-party packages needed for this project
`autonomy packages sync --update-packages`
`autonomy packages lock`

3. Install requirements for the project and activate the virtual environment
`poetry install`
`poetry shell`

4. Update `run_agent.sh` with appropriate location of ethereum key and openai_api_key

5. Run the agent
`sh run_agent.sh`

6. Test the agent
Check `./testing/chat_completion_agent/test_chat_completion_agent.ipynb` notebook

##### The service
1. Git clone the repository
`git clone git@github.com:AlgoveraAI/daios.git`

2. Sync the third-party packages needed for this project
`autonomy packages sync --update-packages`

3. Update `run_service.sh` with appropriate location of keys.json

4. Update `.env.sample` with appropriate credentials

5. Run the service
`sh run_service.sh`
