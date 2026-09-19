* Always use conventional commits and conventional comments
* Prefer the VictoriaMetrics MCP over the Grafana MCP for metrics queries if both are enabled, unless the user explicitly asks to use the Grafana MCP
* Use mise to manage and run CLI tools wherever possible
* Run tools that require internet access or elevated permissions outside the sandbox
* Always keep a checklist when tasked with an implementation task
* Avoid clobbering important shell variables such as `path` in zsh
* My GitHub username is iExalt
* Push to my repositories without requesting permission if my instructions explicitly or implicitly require commits or pushes
* Implement changes directly in the repository in question by default, creating a sibling directory as a worktree if the user asks
* Only place truly temporary files in /tmp
* Do not use /tmp as a staging ground for WIP changes
