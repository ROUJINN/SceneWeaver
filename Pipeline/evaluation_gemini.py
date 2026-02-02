import base64
import json
import os
import time

import numpy as np
from app.llm import LLM
from app.utils import dict2str


class Gemini4:
    """
    Gemini wrapper class that matches GPT4's interface for scene evaluation.
    """

    def __init__(self, version="2.5-pro"):
        """
        Initialize Gemini LLM.

        Args:
            version (str): Model version (e.g., "2.5-pro", "3-flash-preview", "3-flash-exp")
        """
        # Map version to actual model names
        model_map = {
            "2.5-pro": "gemini-2.5-pro",
            "3-flash-preview": "gemini-3-flash-preview",
            "3-flash-exp": "gemini-3-flash-exp",
        }

        self.version = version
        self.MODEL = model_map.get(version, version)
        # Use the default config for LLM
        self.llm = LLM(config_name="default")

    def __call__(self, payload, verbose=False):
        """
        Query Gemini with the provided payload.

        Args:
            payload (dict): Payload containing messages
            verbose (bool): Whether to be verbose during query

        Returns:
            str: Response content from Gemini
        """
        if verbose:
            print(f"Querying Gemini-{self.version} API...")

        # Extract messages from payload
        messages = payload.get("messages", [])

        # Send request via LLM's ask_with_images method
        # The payload format is already compatible with our LLM class
        try:
            # The payload has messages with content that may contain base64 images
            # We need to extract the image and text separately for ask_with_images
            user_msg = messages[-1]
            content = user_msg.get("content", [])

            text_content = ""
            images = []

            for item in content:
                if item.get("type") == "text":
                    text_content += item.get("text", "")
                elif item.get("type") == "image_url":
                    # Extract base64 data from data URL
                    url = item.get("image_url", {}).get("url", "")
                    if url.startswith("data:image/jpeg;base64,"):
                        base64_data = url.replace("data:image/jpeg;base64,", "")
                        images.append({"base64": base64_data})
                    elif url.startswith("data:image/png;base64,"):
                        base64_data = url.replace("data:image/png;base64,", "")
                        images.append({"base64": base64_data})

            # Use ask_with_images
            messages_list = [{"role": "user", "content": text_content}]
            response = self.llm.ask_with_images(
                messages=messages_list,
                images=images,
                stream=False,
            )

            if verbose:
                print(f"Finished querying Gemini-{self.version}.")

            return response

        except Exception as e:
            print(f"Got error while querying Gemini-{self.version} API! Error:\n\n{e}")
            raise

    def encode_image(self, image_path):
        """
        Encodes image located at @image_path to base64.

        Args:
            image_path (str): Absolute path to image to encode

        Returns:
            str: Encoded image as base64 string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def get_payload_eval(self, prompting_text_user, render_path=None):
        """
        Create payload for evaluation with optional image.

        Args:
            prompting_text_user (str): User prompt text
            render_path (str, optional): Path to render image

        Returns:
            dict: Payload formatted for Gemini API
        """
        if render_path is not None:
            imgs_base64 = self.encode_image(render_path)
            img_dict = {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{imgs_base64}"},
            }

            content_user = [{"type": "text", "text": prompting_text_user}, img_dict]
        else:
            content_user = [{"type": "text", "text": prompting_text_user}]

        payload = {
            "model": self.MODEL,
            "messages": [
                {"role": "user", "content": content_user},
            ],
            "temperature": 1,
            "max_tokens": 8192,
        }
        return payload


def eval_general_score(iter, user_demand, gemini_version="2.5-pro"):
    """
    Evaluate scene using Gemini model.

    Args:
        iter (int): Iteration number to evaluate
        user_demand (str): User's demand/prompt for the scene
        gemini_version (str): Gemini model version to use

    Returns:
        tuple: (grades dict, grading dict)
    """
    save_dir = os.getenv("save_dir")
    if not os.path.exists(f"{save_dir}/pipeline/"):
        os.mkdir(f"{save_dir}/pipeline/")

    image_path_1 = f"{save_dir}/record_scene/render_{iter}_marked.jpg"
    with open(f"{save_dir}/record_scene/layout_{iter}.json", "r") as f:
        layout = json.load(f)
        layout = layout["objects"]
        layout = dict2str(layout)

    gpt = Gemini4(version=gemini_version)

    example_json = """
{
  "realism": {
    "grade": your grade as int,
    "comment": "Your comment and suggestion."
  },
  "functionality": {
    "grade": your grade as int,
    "comment": "Your comment and suggestion."
  },
  "layout": {
    "grade": your grade as int,
    "comment": "Your comment and suggestion."
  },
  "completion": {
    "grade": your grade as int,
    "comment": "Your comment and suggestion."
  }
}
    """

    prompting_text_user = f"""
You are given a top-down room render image and the corresponding layout of each object.
Your task is to evaluate how well they align with the user's preferences (provided in triple backticks) across the four criteria listed below.
For each criterion, assign a score from 0 to 10, and provide a brief justification for your rating.

Scoring must be strict. If any critical issue is found (such as missing key objects, obvious layout errors, or unrealistic elements), the score should be significantly lowered, even if other aspects are fine.

**Score Guidelines**:
- Score 10: Fully meets or exceeds expectations; no major improvements needed.
- Score 5: Partially meets expectations; some obvious flaws exist that limit usefulness or quality.
- Score 0: Completely fails to meet expectations; the aspect is absent, wrong, or contradicts user needs.

**Evaluation Criteria**:

1. **Realism**: How realistic the room appears. *Ignore texture, lighting, and doors.*
    - **Good (8-10)**: The layout is believable, and common daily objects make the room feel lived-in.
    - **Bad (0-3)**: Unusual objects or strange placements make the room unrealistic.
    - **Note**: If object types or combinations defy real-world logic (e.g., bathtubs in bedrooms), score should be below 5.

2. **Functionality**: How well the room supports the intended activities (e.g., sleeping, working).
    - **Good (8-10)**: Contains the necessary furniture and setup for the specified function.
    - **Bad (0-3)**: Missing key objects or contains mismatched furniture (e.g., no bed in a bedroom).
    - **Note**: Even one missing critical item should lower the score below 6.

3. **Layout**: Whether the furniture is arranged logically and aligns with the user's preferences.
    - **Good (8-10)**: Objects are neatly placed, relationships are reasonable (e.g., chairs face desks), sufficient space exists for walking, and orientations are correct.
    - **Bad (0-3)**: Floating objects, crowded space, incorrect orientation, or large items placed oddly (e.g., sofa not against the wall).
    - **Note**: If the room has layout issues that affect use, it should not score above 5.

4. **Completion**: How complete and finished the room feels.
    - **Good (8-10)**: All necessary large and small items are present. Has rich details. Each supporter (e.g. table, desk, and shelf) has small objects on it. The room feels done.
    - **Bad (0-3)**: Room is sparse or empty, lacks decor or key elements.
    - **Note**: If more than 30% of the room is blank or lacks detail, score under 5.


Use the following user preferences as reference (enclosed in triple backticks):
User Preference:
```{user_demand}```

Room layout:
{layout}

The Layout include each object's X-Y-Z Position, Z rotation, size (x_dim, y_dim, z_dim), as well as relation info with parents.
Each key in layout is the name for each object, consisting of a random number and the category name, such as "3142143_table".
Note different category name can represent the same category, such as ChairFactory, armchair and chair can represent chair simultaneously.
Count objects carefully! Do not miss any details.
Pay more attention to the orientation of each objects.

Return the results in the following JSON format, the "comment" should be short:
{example_json}

For the image:
Each object is marked with a 3D bounding box and its category label. You must count the object carefully with the given image and layout.

You are working in a 3D scene environment with the following conventions:

- Right-handed coordinate system.
- The X-Y plane is the floor.
- X axis (red) points right, Y axis (green) points top, Z axis (blue) points up.
- For the location [x,y,z], x,y means the location of object's center in x- and y-axis, z means the location of the object's bottom in z-axis.
- All asset local origins are centered in X-Y and at the bottom in Z.
- By default, assets face the +X direction.
- A rotation of [0, 0, 1.57] in Euler angles will turn the object to face +Y.
- All bounding boxes are aligned with the local frame and marked in blue with category labels.
- The front direction of objects are marked with yellow arrow.
- Coordinates in the image are marked from [0, 0] at bottom-left of the room.

"""

    prompt_payload = gpt.get_payload_eval(
        prompting_text_user=prompting_text_user, render_path=image_path_1
    )

    grades = {"realism": [], "functionality": [], "layout": [], "completion": []}
    for _ in range(1):
        try:
            grading_str = gpt(payload=prompt_payload, verbose=True)
        except Exception as e:
            print(f"Error querying Gemini: {e}, retrying...")
            time.sleep(30)
            grading_str = gpt(payload=prompt_payload, verbose=True)
        print(grading_str)
        print("-" * 50)
        import re
        pattern = r"```json(.*?)```"
        matches = re.findall(pattern, grading_str, re.DOTALL)
        json_content = matches[0].strip() if matches else None
        if json_content is None:
            grading = json.loads(grading_str)
        else:
            grading = json.loads(json_content)
        for key in grades:
            grades[key].append(grading[key]["grade"])

    with open(f"{save_dir}/pipeline/grade_iter_{iter}.json", "w") as f:
        json.dump(grading, f, indent=4)
    # Save the mean and std of the grades
    for key in grades:
        grades[key] = {
            "mean": round(sum(grades[key]) / len(grades[key]), 2),
            "std": round(np.std(grades[key]), 2),
        }
    # Save the grades
    with open(f"{save_dir}/pipeline/eval_iter_{iter}.json", "w") as f:
        json.dump(grades, f, indent=4)

    return grades, grading
