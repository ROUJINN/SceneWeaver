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

### Evaluation System

Located in `Pipeline/evaluation*.py`:
- **Physics validation**: Checks collisions, layout feasibility, interactions
- **GPT-based evaluation**: Grades scene quality and completeness
- Both scores are combined to guide the agent's next actions

## Output Structure

Generated scenes are saved with the following structure:
```
PATH/TO/SAVE/Scene_Name/
  |-- args/                    # Runtime arguments per iteration
  |-- pipeline/                # Agent interaction records
  |   |-- memory_{iter}.json   # Agent memory
  |   |-- metric_{iter}.json   # Evaluation scores
  |   |-- {tool}_results_{iter}.json
  |   |-- ...
  |-- record_files/            # Intermediate Blender files
  |   |-- scene_{iter}.blend
  |   |-- env_{iter}.pkl
  |   |-- ...
  |-- record_scene/            # Layout info and renders
  |   |-- layout_{iter}.json
  |   |-- render_{iter}.jpg
  |-- roominfo.json
```

## Key Configuration Files

- `Pipeline/app/config.py`: Application config (LLM settings, paths)
- `Pipeline/app/schema.py`: Data schemas for agent communication (AgentState, Memory, Message, ToolCall)
- `Pipeline/app/agent/scenedesigner.py`: Main agent - modify `available_tools0/1/2` to enable/disable tools
- `environment_sceneweaver.yml`: Conda environment for planner
- `env.sh`: Bash script for infinigen environment setup

## Adding New Tools

1. Create tool class in `Pipeline/app/tool/` inheriting from base tool pattern
2. Implement `execute()` method with appropriate Blender/Infinigen calls
3. Add to tool collection in `scenedesigner.py`
4. Update tool descriptions/prompts as needed
