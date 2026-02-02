"""
Standalone script to evaluate a scene using Gemini model.

Usage:
    python evaluate_scene_gemini.py --scene_dir <path> --iter <iter_num> --prompt "<user demand>" [--model <model_version>]

Example:
    python evaluate_scene_gemini.py --scene_dir /home/lj/3D/SceneWeaver/fxxkingresults/Design_me_a_bedroom_0 --iter 6 --prompt "Design me a bedroom." --model 2.5-pro
"""

import argparse
import os

from evaluation_gemini import eval_general_score


def main():
    parser = argparse.ArgumentParser(description="Evaluate a scene using Gemini model")
    parser.add_argument(
        "--scene_dir",
        type=str,
        required=True,
        help="Path to the scene directory",
    )
    parser.add_argument(
        "--iter",
        type=int,
        required=True,
        help="Iteration number to evaluate",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        required=True,
        help="User demand/prompt for the scene",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="2.5-pro",
        choices=["2.5-pro", "3-flash-preview", "3-flash-exp"],
        help="Gemini model version to use (default: 2.5-pro)",
    )

    args = parser.parse_args()

    # Set save_dir environment variable
    os.environ["save_dir"] = args.scene_dir

    # Verify required files exist
    render_path = f"{args.scene_dir}/record_scene/render_{args.iter}_marked.jpg"
    layout_path = f"{args.scene_dir}/record_scene/layout_{args.iter}.json"

    if not os.path.exists(render_path):
        print(f"Error: Render image not found: {render_path}")
        return 1

    if not os.path.exists(layout_path):
        print(f"Error: Layout file not found: {layout_path}")
        return 1

    # Evaluate the scene
    print(f"Evaluating scene at {args.scene_dir}, iteration {args.iter}")
    print(f"User demand: {args.prompt}")
    print(f"Using Gemini model: {args.model}")
    print("-" * 50)

    try:
        grades, grading = eval_general_score(args.iter, args.prompt, args.model)
        print("-" * 50)
        print("Evaluation completed successfully!")
        print("Results saved to:")
        print(f"  - {args.scene_dir}/pipeline/grade_iter_{args.iter}.json")
        print(f"  - {args.scene_dir}/pipeline/eval_iter_{args.iter}.json")
        print("-" * 50)
        print("Scores:")
        for key, value in grades.items():
            print(f"  {key}: {value['mean']} (std: {value['std']})")
        return 0
    except Exception as e:
        print(f"Error during evaluation: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
