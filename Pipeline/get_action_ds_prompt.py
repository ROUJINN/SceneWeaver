
from get_action_prompt import (
  system_prompt,
  methods_prompt,
  feedback_reflections_prompt,
  feedback_reflections_prompt_system,
  feedback_reflections_prompt_user,
  idea_example
)

sceneinfo_prompt = """
Scene Layout: {scene_layout}.
Layout of door and windows: {structure}
"None" means the scene is empty.
"""