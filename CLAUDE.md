# CLAUDE.md

对我所用的服务器环境的介绍：
在.bashrc里有加alias lg="source /home/lj/mylogin.sh"
在mylogin.sh里设置了我常用的API key，以及服务器代理的设置，所以跑任何python代码前，都需要
`lg <conda_env_name>`
来activate虚拟环境，并且顺便设置好环境变量

## Project Overview

SceneWeaver is an "All-in-One 3D Scene Synthesis with an Extensible and Self-Reflective Agent" - a system for generating complex 3D indoor scenes using AI agents. It combines:
- An AI-powered SceneDesigner agent that uses LLMs for planning and decision-making
- Infinigen as the procedural 3D content generation engine (based on Blender)
- Multiple asset sources: MetaScenes, 3D FUTURE, Infinigen-generated assets, Objaverse
- A tool-based architecture for scene initialization, implementation, and modification

## Environment Setup

SceneWeaver requires **two separate conda environments**:

### 1. SceneWeaver Planner Environment (`sceneweaver`)
```bash
conda env create --prefix /path/to/anaconda3/envs/sceneweaver -f environment_sceneweaver.yml
conda activate sceneweaver
```

This environment contains Python 3.8 with OpenAI/transformers dependencies for the agent.

### 2. Infinigen Executor Environment (`infinigen`)
```bash
conda create --name infinigen python=3.10.14
conda activate infinigen
# Install required packages (see env.sh for full list)
pip install bpy==3.6.0 --extra-index-url https://download.blender.org/pypi/
pip install gin-config trimesh scipy scikit-learn python-fcl Rtree shapely ...
```

Then run the Infinigen installer:
```bash
# Minimal installation (recommended)
INFINIGEN_MINIMAL_INSTALL=True bash scripts/install/interactive_blender.sh

# Normal installation
bash scripts/install/interactive_blender.sh

# With OpenGL ground truth
INFINIGEN_INSTALL_CUSTOMGT=True bash scripts/install/interactive_blender.sh
```

## Configuration

Before running, set up your LLM API key:

1. **API Key**: Save your Azure/OpenAI API key in `Pipeline/key.txt` (first line)
2. **Config**: Edit `Pipeline/config/config.json` with your Azure endpoint, model, and deployment details:
   ```json
   {
     "llm": {
       "api_type": "azure",
       "model": "gpt-4.1-2025-04-14",
       "base_url": "{YOUR_AZURE_ENDPOINT.rstrip('/')}/openai/deployments/{AZURE_DEPLOYMENT_ID}",
       "api_key": "key.txt",
       "max_tokens": 8096,
       "temperature": 0.3,
       "api_version": "2025-03-01-preview"
     }
   }
   ```

## Running the System

### Mode 1: Background Blender (Recommended)
```bash
cd Pipeline
conda activate sceneweaver
python main.py --prompt "Design me a bedroom." --cnt 1 --basedir PATH/TO/SAVE
```

### Mode 2: Foreground Blender (Interactive)
Requires two terminals:

**Terminal 1** (Infinigen):
```bash
cd SceneWeaver
conda activate infinigen
python -m infinigen.launch_blender -m infinigen_examples.generate_indoors_vis \
  --save_dir debug/ -- \
  --seed 0 --task coarse --output_folder debug/ \
  -g fast_solve.gin overhead.gin studio.gin \
  -p compose_indoors.terrain_enabled=False
```

**Terminal 2** (SceneWeaver):
```bash
cd SceneWeaver/Pipeline
conda activate sceneweaver
python main.py --prompt "Design me a bedroom." --cnt 1 --basedir PATH/TO/SAVE --socket
```

## Architecture

### Agent System (`Pipeline/app/`)

The core is the **SceneDesigner** agent (`app/agent/scenedesigner.py`) which:

1. **Maintains tool collections** organized by phase:
   - `available_tools0`: Initializers (InitGPTExecute, InitMetaSceneExecute, InitPhySceneExecute)
   - `available_tools1`: Implementers (AddAcdcExecute, AddGPTExecute, AddCrowdExecute, AddRelationExecute, UpdateLayoutExecute, UpdateRotationExecute, UpdateSizeExecute, RemoveExecute)
   - `available_tools2`: Termination (Terminate)

2. **Uses LLM-based planning**: Each step, the agent observes the current scene state, uses the LLM to decide which tool to call, and executes it

3. **Self-reflective loop**: After each tool execution, the scene is evaluated (physics + GPT-based grading) to determine if improvements are needed

4. **Tool execution flow**:
   - Agent selects tool → Tool executes → Scene updated in Blender → Scene evaluated → Memory updated → Next iteration

### Tool Categories

- **Initializer Tools**: Set up initial room layout using GPT generation, MetaScenes dataset, or PhyScene/DiffuScene/ATISS models
- **Implementer Tools**: Add objects to the scene using various methods:
  - `AddAcdcExecute`: Visual generation using Stable Diffusion + Tabletop Digital Cousin
  - `AddGPTExecute`: LLM-based sparse or crowded object placement
  - `AddCrowdExecute`: Rule-based dense object placement
  - `AddRelationExecute`: Add object relationships
- **Modifier Tools**: Update layout, rotation, size, or remove objects
- **Termination Tool`: Marks scene as complete

### Asset Sources

Different tools use different asset sources:

| Tool/Stage | Asset Source |
|------------|--------------|
| MetaScenes initializer | MetaScenes dataset (with meshes and layout) |
| PhyScene/DiffuScene/ATISS initializer | 3D FUTURE dataset |
| Most other tools | Infinigen procedural generation |
| Specialized categories (clock, laptop, etc.) | Objaverse via OpenShape or Holodeck pipelines |

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

## Export to USD (for Isaac Sim)

```bash
python -m infinigen.tools.export --input_folder BLENDER_FILE_FOLDER \
  --output_folder USD_SAVE_FOLDER -f usdc -r 1024 --omniverse
```
