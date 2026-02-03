# CLAUDE.md

对我所用的服务器环境的介绍：
在.bashrc里有加alias lg="source /home/lj/mylogin.sh"
在mylogin.sh里设置了我常用的API key，以及服务器代理的设置，所以跑任何python代码前，都需要
`lg <conda_env_name>`
来activate虚拟环境，并且顺便设置好环境变量。
如果要单独的开一个bash来跑程序，那么就要在bash的开头先 `source /home/lj/mylogin.sh <conda_env_name>`

## Project Overview

SceneWeaver is an "All-in-One 3D Scene Synthesis with an Extensible and Self-Reflective Agent" - a system for generating complex 3D indoor scenes using AI agents. It combines:
- An AI-powered SceneDesigner agent that uses LLMs for planning and decision-making
- Infinigen as the procedural 3D content generation engine (based on Blender)
- Multiple asset sources: MetaScenes, 3D FUTURE, Infinigen-generated assets, Objaverse
- A tool-based architecture for scene initialization, implementation, and modification


## Running the System

### Background Blender (Recommended)
```bash
cd Pipeline
source run.sh
```

## Architecture

### Agent System (`Pipeline/app/`)

The core is the **SceneDesigner** agent (`app/agent/scenedesigner.py`) which:

2. **Uses LLM-based planning**: Each step, the agent observes the current scene state, uses the LLM to decide which tool to call, and executes it

3. **Self-reflective loop**: After each tool execution, the scene is evaluated (physics + GPT-based grading) to determine if improvements are needed

4. **Tool execution flow**:
   - Agent selects tool → Tool executes → Scene updated in Blender → Scene evaluated → Memory updated → Next iteration
