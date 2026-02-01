#!/usr/bin/env python
import json
import os
import sys

# Add SceneWeaver to path
sys.path.insert(0, "/home/lj/3D/SceneWeaver")

import open_clip
from sentence_transformers import SentenceTransformer

from GPT.objaverse_retriever import ObjathorRetriever


def main():
    save_dir = sys.argv[1]

    # Load retriever
    print("Loading retriever models...")
    clip_model, _, clip_preprocess = open_clip.create_model_and_transforms(
        "ViT-L-14", pretrained="laion2b_s32b_b82k"
    )
    clip_tokenizer = open_clip.get_tokenizer("ViT-L-14")
    sbert_model = SentenceTransformer("all-mpnet-base-v2")

    retriever = ObjathorRetriever(
        clip_model=clip_model,
        clip_preprocess=clip_preprocess,
        clip_tokenizer=clip_tokenizer,
        sbert_model=sbert_model,
        retrieval_threshold=28,
    )
    print("Retriever loaded successfully.")

    # Read categories to retrieve
    with open(f"{save_dir}/objav_cnts.json", "r") as f:
        LoadObjavCnts = json.load(f)

    # Retrieve for each category
    LoadObjavFiles = dict()
    print(LoadObjavCnts.items())
    for category, cnt in LoadObjavCnts.items():
        print(f"\nRetrieving for category: {category}")
        try:
            candidates = retriever.retrieve(
                [f"a 3D model of a single {category}"], threshold=30
            )
            if candidates:
                asset_id = candidates[0][0]
                # Map to local asset path (.pkl.gz format)
                asset_path = f"/home/lj/.objathor-assets/2023_09_23/assets/{asset_id}/{asset_id}.pkl.gz"
                if os.path.exists(asset_path):
                    LoadObjavFiles[category] = [asset_path]
                    print(f"  Found: {asset_id}")
                else:
                    print(f"  Asset file not found: {asset_path}")
            else:
                print(f"  No candidates found for {category}")
        except Exception as e:
            print(f"  Error retrieving {category}: {e}")
            LoadObjavFiles[category] = []

    # Save results in same format as retrieve_idesign.py
    with open(f"{save_dir}/objav_files.json", "w") as f:
        json.dump(LoadObjavFiles, f, indent=4)
    print(f"\nSaved results to {save_dir}/objav_files.json")


if __name__ == "__main__":
    main()
