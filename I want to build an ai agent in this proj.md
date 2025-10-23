I want to build an ai agent in this project market-mind. On folder frontend would be the frontend of the chat in react. The backend is in folder backend. In folder charts would be the helm charts template to deploy the frontend and backend to my k3s.

Create Dockerfile and docker-compose files where you find it fit.

On the root folder create a devcontainer to handle my frontend and backend using vscode.

Update the .gitignore file when you find it fit.

Fill it the README.md file with important information about the project, how to run it locally, using docker and devcontainer. Also steps to deploy to k3s. Other information you think is relevant.

For the backend, use python 3.12 with uv. Create a pyproject.toml file. The ai agent need to be stateful and use langchaing, langgraph, duckduckgo search for request information over the internet. If a vector database is need it use chromadb with persistent storage, if a normal database is needed to store chat history use postgresql. Assume the ai will work with openai, using the model gpt-4o. Create a .env file to handle credentials. Use langfuse to monitor the ai workflow, assume we use the cloud version. Make limitations for how many requests a user can do in hour/day.

The ai should answer:
Fetch and summarize real-time financial or crypto data
Generate insights or predictions (“based on X, Y, Z, sentiment is bullish”)
Give advise if I should invest in a stock based on real-time insights

For the frontend, use react. Create a chat interface and taildwindcss to create a light/dark theme. The user could create multiple chats conversation, each chat room should load the conversation history. If needed use zustand.

Write unit test for the frontend and backend and tell in README how to run them.

[152372 ms] Start: Run in container:
Running the postCreateCommand from Feature 'ghcr.io/devcontainers/features/git-lfs:1'...

[152746 ms] Start: Run in container:
Fetching git lfs artifacts...
Could not pull

Errors logged to '/workspaces/market-mind/.git/lfs/logs/20251023T161400.174823616.log'.
Use `git lfs logs last` to view the log.
[152836 ms] postCreateCommand from Feature 'ghcr.io/devcontainers/features/git-lfs:1' failed with exit code 2. Skipping any further user-provided commands.