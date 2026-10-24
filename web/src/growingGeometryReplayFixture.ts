export const GROWING_GEOMETRY_FIXTURE = {
  "schema_version": "growing-geometry-research-artifact-v1",
  "scope": "software_research_only",
  "claim_scope": "synthetic_growing_geometry_replay_only",
  "G0_G4": "not_assessed",
  "status": "completed_software_fixture",
  "time_kind": "synthetic_model_clock_not_observation",
  "parameter_scope": "synthetic_inputs_with_pinned_research_reference_profiles",
  "display_policy": {
    "geometry_authority": "stored_leaf_area",
    "stem_pose_attachment": "separate_authored_asset_required",
    "fruit_height_yield_margin_ranking": "not_derived"
  },
  "scenarios": {
    "warm-day": {
      "artifact_sha256": "8d553a2f72dc53a0cdb469102777cc062c3013ea7a1cf04bdea46e8a931d0efa",
      "index_sha256": "dff515a320fea7f67b017c66773934fe30d86441359e013d01b680014a167343",
      "frames": 17
    },
    "reverse": {
      "artifact_sha256": "91ec7efa2654a65418ccd5e089ec9dac9eaaca2ccc39f3136a404db554703de9",
      "index_sha256": "c5c41d4eb82f0606ba5f1fc8d48cb315902cc925ec2df7150b3667b2124438ee",
      "frames": 17
    },
    "cool-dark": {
      "artifact_sha256": "da0a9cf702f031fb47009180b362ee8d3b73fd4867c4d7d688a0acc190f59d66",
      "index_sha256": "ebeac0959964ca14897cd0b60d74316b04d257b126a2e030b869b659f445d08a",
      "frames": 17
    },
    "warm-reference30": {
      "artifact_sha256": "3806785832eab125654e5510ea3125b76df8ffef83bad349d07c3d33bbdfb26d",
      "index_sha256": "dfcb18e5d44e4096fcd4f68159dc0f5f5cd52cc826c95c7c48fcf904c7098249",
      "frames": 17
    },
    "warm-reference22": {
      "artifact_sha256": "d95dc6e10aacbf50775ceeab98dd2cc08cc7b5b73f381765338eea9655799681",
      "index_sha256": "c0506a76bb10281a0dca5ef69b8b7776054194f3b9b4cb9890da7cfd7d3f0a47",
      "frames": 17
    },
    "empty-entry": {
      "artifact_sha256": "ff5bc64a32f5f28e93177cd07c4c69b295b42d68773c07cb54a0799888dfbf28",
      "index_sha256": "bc7b2679d82b1aa55690d74be7617094891640b2e260cabe0694088fed56385e",
      "frames": 17
    }
  }
} as const;
