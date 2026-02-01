"""
Test script for Holodeck/Objaverse asset retrieval.

This script verifies:
1. Prerequisites are met (conda env, data directories)
2. Required files exist
3. Models can be loaded
4. Retrieval works for sample queries
"""

import json
import os
import subprocess
import sys
import tempfile

# Add parent directory to path
sys.path.insert(0, "/home/lj/3D/SceneWeaver")

from GPT.constants import (
    HOLODECK_BASE_DATA_DIR,
    HOLODECK_THOR_ANNOTATIONS_PATH,
    HOLODECK_THOR_FEATURES_DIR,
    OBJATHOR_ANNOTATIONS_PATH,
    OBJATHOR_ASSETS_DIR,
    OBJATHOR_FEATURES_DIR,
)


def print_section(title):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def check_prerequisites():
    """Check if conda env and data directories exist."""
    print_section("1. Checking Prerequisites")

    all_pass = True

    # Check conda env
    result = subprocess.run(["conda", "env", "list"], capture_output=True, text=True)
    if "holodeck" in result.stdout:
        print("  [PASS] 'holodeck' conda environment exists")
    else:
        print("  [FAIL] 'holodeck' conda environment not found")
        all_pass = False

    # Check data directories
    dirs_to_check = [
        (OBJATHOR_ASSETS_DIR, "objathor assets"),
        (OBJATHOR_FEATURES_DIR, "objathor features"),
        (HOLODECK_BASE_DATA_DIR, "holodeck base data"),
        (HOLODECK_THOR_FEATURES_DIR, "holodeck thor_object_data"),
    ]

    for dir_path, name in dirs_to_check:
        if os.path.exists(dir_path):
            print(f"  [PASS] {name} directory: {dir_path}")
        else:
            print(f"  [FAIL] {name} directory missing: {dir_path}")
            all_pass = False

    return all_pass


def check_files():
    """Check if required files exist."""
    print_section("2. Checking Required Files")

    all_pass = True

    files_to_check = [
        (OBJATHOR_ANNOTATIONS_PATH, "objathor annotations.json.gz"),
        (
            os.path.join(OBJATHOR_FEATURES_DIR, "clip_features.pkl"),
            "objathor clip_features.pkl",
        ),
        (
            os.path.join(OBJATHOR_FEATURES_DIR, "sbert_features.pkl"),
            "objathor sbert_features.pkl",
        ),
        (HOLODECK_THOR_ANNOTATIONS_PATH, "holodeck thor annotations.json.gz"),
        (
            os.path.join(HOLODECK_THOR_FEATURES_DIR, "clip_features.pkl"),
            "holodeck thor clip_features.pkl",
        ),
        (
            os.path.join(HOLODECK_THOR_FEATURES_DIR, "sbert_features.pkl"),
            "holodeck thor sbert_features.pkl",
        ),
    ]

    for file_path, name in files_to_check:
        if os.path.exists(file_path):
            print(f"  [PASS] {name}: {file_path}")
        else:
            print(f"  [FAIL] {name} missing: {file_path}")
            all_pass = False

    return all_pass


def test_model_loading():
    """Test loading CLIP and SBERT models."""
    print_section("3. Testing Model Loading")

    all_pass = True

    try:
        print("  Loading CLIP model (ViT-L-14)...")
        import open_clip

        clip_model, _, clip_preprocess = open_clip.create_model_and_transforms(
            "ViT-L-14", pretrained="laion2b_s32b_b82k"
        )
        clip_tokenizer = open_clip.get_tokenizer("ViT-L-14")
        print("  [PASS] CLIP model loaded successfully")
    except Exception as e:
        print(f"  [FAIL] Failed to load CLIP model: {e}")
        all_pass = False
        return all_pass, None, None, None, None

    try:
        print("  Loading SBERT model (all-mpnet-base-v2)...")
        from sentence_transformers import SentenceTransformer

        sbert_model = SentenceTransformer("all-mpnet-base-v2")
        print("  [PASS] SBERT model loaded successfully")
    except Exception as e:
        print(f"  [FAIL] Failed to load SBERT model: {e}")
        all_pass = False
        return all_pass, None, None, None, None

    return all_pass, clip_model, clip_preprocess, clip_tokenizer, sbert_model


def test_retriever_initialization(
    clip_model, clip_preprocess, clip_tokenizer, sbert_model
):
    """Test initializing ObjathorRetriever."""
    print_section("4. Testing Retriever Initialization")

    try:
        from GPT.objaverse_retriever import ObjathorRetriever

        retriever = ObjathorRetriever(
            clip_model=clip_model,
            clip_preprocess=clip_preprocess,
            clip_tokenizer=clip_tokenizer,
            sbert_model=sbert_model,
            retrieval_threshold=28,
        )
        print("  [PASS] ObjathorRetriever initialized successfully")
        return retriever, True
    except Exception as e:
        print(f"  [FAIL] Failed to initialize ObjathorRetriever: {e}")
        return None, False


def test_asset_retrieval(retriever):
    """Test retrieval for sample categories."""
    print_section("5. Testing Asset Retrieval")

    if retriever is None:
        print("  [SKIP] Retriever not initialized, skipping retrieval test")
        return False

    # Test categories including ones that often have null mappings
    test_categories = ["tv", "rug", "plant", "mirror", "lamp", "chair", "bed"]

    results = {}
    for category in test_categories:
        try:
            query = f"a 3D model of a single {category}"
            candidates = retriever.retrieve([query], threshold=30)

            if candidates:
                uid, score = candidates[0]
                asset_path = os.path.join(OBJATHOR_ASSETS_DIR, uid, f"{uid}.pkl.gz")

                if os.path.exists(asset_path):
                    results[category] = {
                        "uid": uid,
                        "score": score,
                        "path": asset_path,
                        "exists": True,
                    }
                    print(f"  [PASS] {category}: found {uid} (score: {score:.2f})")
                else:
                    results[category] = {
                        "uid": uid,
                        "score": score,
                        "path": asset_path,
                        "exists": False,
                    }
                    print(
                        f"  [WARN] {category}: found {uid} but file missing at {asset_path}"
                    )
            else:
                results[category] = {"found": False}
                print(f"  [WARN] {category}: no candidates found")
        except Exception as e:
            results[category] = {"error": str(e)}
            print(f"  [FAIL] {category}: error during retrieval - {e}")

    # Summary
    found_count = sum(1 for r in results.values() if r.get("exists", False))
    total = len(test_categories)

    print(f"\n  Summary: {found_count}/{total} categories had retrievable assets")

    return found_count > 0


def test_full_workflow(retriever):
    """Optional: Test the full workflow with temp files."""
    print_section("6. Testing Full Workflow (Optional)")

    # Create temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"  Using temp directory: {temp_dir}")

        # Create objav_cnts.json
        objav_cnts = {"tv": 1, "rug": 1, "lamp": 1}
        objav_cnts_path = os.path.join(temp_dir, "objav_cnts.json")
        with open(objav_cnts_path, "w") as f:
            json.dump(objav_cnts, f, indent=4)
        print(f"  Created: {objav_cnts_path}")

        # Run retrieval for each category
        LoadObjavFiles = {}
        for category, cnt in objav_cnts.items():
            print(f"  Retrieving for: {category}")
            try:
                candidates = retriever.retrieve(
                    [f"a 3D model of a single {category}"], threshold=30
                )
                if candidates:
                    uid = candidates[0][0]
                    asset_path = os.path.join(OBJATHOR_ASSETS_DIR, uid, f"{uid}.pkl.gz")
                    if os.path.exists(asset_path):
                        LoadObjavFiles[category] = [asset_path]
                        print(f"    Found: {uid}")
                    else:
                        print(f"    Asset file missing: {asset_path}")
                        LoadObjavFiles[category] = []
                else:
                    print("    No candidates found")
                    LoadObjavFiles[category] = []
            except Exception as e:
                print(f"    Error: {e}")
                LoadObjavFiles[category] = []

        # Verify objav_files.json would be created correctly
        objav_files_path = os.path.join(temp_dir, "objav_files.json")
        with open(objav_files_path, "w") as f:
            json.dump(LoadObjavFiles, f, indent=4)
        print(f"  Created: {objav_files_path}")

        valid_count = sum(1 for v in LoadObjavFiles.values() if v)
        print(
            f"  Workflow test: {valid_count}/{len(objav_cnts)} categories retrieved successfully"
        )

        return valid_count > 0


def main():
    print("\n" + "=" * 60)
    print("  Holodeck/Objaverse Asset Retrieval Test")
    print("=" * 60)

    # Run tests
    pass_prereq = check_prerequisites()
    pass_files = check_files()

    if not (pass_prereq and pass_files):
        print("\n" + "=" * 60)
        print("  [FAIL] Prerequisites not met. Please fix the issues above.")
        print("=" * 60)
        sys.exit(1)

    pass_models, clip_model, clip_preprocess, clip_tokenizer, sbert_model = (
        test_model_loading()
    )
    retriever, pass_retriever = test_retriever_initialization(
        clip_model, clip_preprocess, clip_tokenizer, sbert_model
    )

    if not pass_models:
        print("\n" + "=" * 60)
        print("  [FAIL] Model loading failed. Check if models are downloaded.")
        print("  CLIP (ViT-L-14) and SBERT (all-mpnet-base-v2) need to be available.")
        print("=" * 60)
        sys.exit(1)

    pass_retrieval = test_asset_retrieval(retriever)
    pass_workflow = test_full_workflow(retriever)

    # Final summary
    print_section("Test Summary")
    print(f"  Prerequisites:       {'[PASS]' if pass_prereq else '[FAIL]'}")
    print(f"  Required Files:      {'[PASS]' if pass_files else '[FAIL]'}")
    print(f"  Model Loading:       {'[PASS]' if pass_models else '[FAIL]'}")
    print(f"  Retriever Init:      {'[PASS]' if pass_retriever else '[FAIL]'}")
    print(f"  Asset Retrieval:     {'[PASS]' if pass_retrieval else '[FAIL]'}")
    print(f"  Full Workflow:       {'[PASS]' if pass_workflow else '[FAIL]'}")

    all_pass = all(
        [pass_prereq, pass_files, pass_models, pass_retriever, pass_retrieval]
    )

    print()
    if all_pass:
        print("=" * 60)
        print("  [SUCCESS] All tests passed!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("=" * 60)
        print("  [FAIL] Some tests failed. See details above.")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
