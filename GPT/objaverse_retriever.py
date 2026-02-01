import os

import compress_json
import compress_pickle
import numpy as np
import torch
import torch.nn.functional as F

from .constants import (
    HOLODECK_THOR_ANNOTATIONS_PATH,
    HOLODECK_THOR_FEATURES_DIR,
    OBJATHOR_ANNOTATIONS_PATH,
    OBJATHOR_ASSETS_DIR,
    OBJATHOR_FEATURES_DIR,
)
from .utils import get_bbox_dims


class ObjathorRetriever:
    def __init__(
        self,
        clip_model,
        clip_preprocess,
        clip_tokenizer,
        sbert_model,
        retrieval_threshold,
    ):
        objathor_annotations = compress_json.load(OBJATHOR_ANNOTATIONS_PATH)
        thor_annotations = compress_json.load(HOLODECK_THOR_ANNOTATIONS_PATH)
        self.database = {**objathor_annotations, **thor_annotations}

        objathor_clip_features_dict = compress_pickle.load(
            os.path.join(OBJATHOR_FEATURES_DIR, "clip_features.pkl")
        )  # clip features
        objathor_sbert_features_dict = compress_pickle.load(
            os.path.join(OBJATHOR_FEATURES_DIR, "sbert_features.pkl")
        )  # sbert features
        assert (
            objathor_clip_features_dict["uids"] == objathor_sbert_features_dict["uids"]
        )

        objathor_uids = objathor_clip_features_dict["uids"]
        objathor_clip_features = objathor_clip_features_dict["img_features"].astype(
            np.float32
        )
        objathor_sbert_features = objathor_sbert_features_dict["text_features"].astype(
            np.float32
        )

        thor_clip_features_dict = compress_pickle.load(
            os.path.join(HOLODECK_THOR_FEATURES_DIR, "clip_features.pkl")
        )  # clip features
        thor_sbert_features_dict = compress_pickle.load(
            os.path.join(HOLODECK_THOR_FEATURES_DIR, "sbert_features.pkl")
        )  # clip features
        assert thor_clip_features_dict["uids"] == thor_sbert_features_dict["uids"]

        thor_uids = thor_clip_features_dict["uids"]
        thor_clip_features = thor_clip_features_dict["img_features"].astype(np.float32)
        thor_sbert_features = thor_sbert_features_dict["text_features"].astype(
            np.float32
        )

        # Filter out missing asset files
        print("[INFO] 检查资产文件可用性...")
        all_uids = objathor_uids + thor_uids
        all_clip_features = np.concatenate(
            [objathor_clip_features, thor_clip_features], axis=0
        )
        all_sbert_features = np.concatenate(
            [objathor_sbert_features, thor_sbert_features], axis=0
        )

        valid_indices = []
        missing_count = 0
        for idx, uid in enumerate(all_uids):
            # THOR assets don't need file checking
            if uid in thor_uids:
                valid_indices.append(idx)
            else:
                # Check if Objaverse asset file exists
                asset_path = os.path.join(OBJATHOR_ASSETS_DIR, uid, f"{uid}.pkl.gz")
                if os.path.exists(asset_path):
                    valid_indices.append(idx)
                else:
                    missing_count += 1

        if missing_count > 0:
            print(f"[INFO] 过滤掉 {missing_count} 个缺失的资产文件")
            print(f"[INFO] 可用资产: {len(valid_indices)}/{len(all_uids)}")

        # Only keep valid assets
        self.asset_ids = [all_uids[i] for i in valid_indices]
        valid_clip_features = all_clip_features[valid_indices]
        valid_sbert_features = all_sbert_features[valid_indices]

        self.clip_features = torch.from_numpy(valid_clip_features)
        self.clip_features = F.normalize(self.clip_features, p=2, dim=-1).cuda()

        self.sbert_features = torch.from_numpy(valid_sbert_features).cuda()

        self.clip_model = clip_model
        self.clip_preprocess = clip_preprocess
        self.clip_tokenizer = clip_tokenizer
        self.sbert_model = sbert_model

        self.retrieval_threshold = retrieval_threshold

        self.use_text = True

    def retrieve(self, queries, threshold=28):
        with torch.no_grad():
            query_feature_clip = self.clip_model.encode_text(
                self.clip_tokenizer(queries)
            )

            query_feature_clip = F.normalize(query_feature_clip, p=2, dim=-1).cuda()

        clip_similarities = 100 * torch.einsum(
            "ij, lkj -> ilk", query_feature_clip, self.clip_features
        )
        clip_similarities = torch.max(clip_similarities, dim=-1).values

        query_feature_sbert = self.sbert_model.encode(
            queries, convert_to_tensor=True, show_progress_bar=False
        )
        sbert_similarities = query_feature_sbert @ self.sbert_features.T

        if self.use_text:
            similarities = clip_similarities + sbert_similarities
        else:
            similarities = clip_similarities

        threshold_indices = torch.where(clip_similarities > threshold)

        unsorted_results = []
        for query_index, asset_index in zip(*threshold_indices):
            score = similarities[query_index, asset_index].item()
            unsorted_results.append((self.asset_ids[asset_index], score))

        # Sorting the results in descending order by score
        results = sorted(unsorted_results, key=lambda x: x[1], reverse=True)

        return results

    def compute_size_difference(self, target_size, candidates):
        candidate_sizes = []
        for uid, _ in candidates:
            size = get_bbox_dims(self.database[uid])
            size_list = [size["x"] * 100, size["y"] * 100, size["z"] * 100]
            size_list.sort()
            candidate_sizes.append(size_list)

        candidate_sizes = torch.tensor(candidate_sizes)

        target_size_list = list(target_size)
        target_size_list.sort()
        target_size = torch.tensor(target_size_list)

        size_difference = abs(candidate_sizes - target_size).mean(axis=1) / 100
        size_difference = size_difference.tolist()

        candidates_with_size_difference = []
        for i, (uid, score) in enumerate(candidates):
            candidates_with_size_difference.append(
                (uid, score - size_difference[i] * 10)
            )

        # sort the candidates by score
        candidates_with_size_difference = sorted(
            candidates_with_size_difference, key=lambda x: x[1], reverse=True
        )

        return candidates_with_size_difference
