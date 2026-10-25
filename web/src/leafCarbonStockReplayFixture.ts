export const LEAF_CARBON_STOCK_FIXTURE = {
  "schema_version": "leaf-carbon-stock-research-artifact-v1",
  "scope": "software_research_only",
  "claim_scope": "synthetic_leaf_carbon_stock_replay_only",
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
    "warm-day-individual-stock": {
      "artifact_sha256": "975830a05b9289d4c4cb233c7e5f3da39e08aa9015a56d223dac6725bccdae9d",
      "index_sha256": "9d0179927ee1257ae778a2e3e1f11239a6d1c0282e82e4fee44c04699a7c3426",
      "frames": 17,
      "leaf_curve_sha256": {
        "own-leaf-0": "78a85421dc8bea6bb598d2d6cc5aba9a2f553bc31062df564c8b95ec2a0c6315",
        "own-leaf-1": "86e4b9288cc6ac2c53cfb2fb73adfd15bf99412b64ee457af6a673ba24243874",
        "own-leaf-2": "0e84993699a6d14a6ae25ccfe2d16ced63db16d7aa801a9343150f7294e1fc00"
      }
    },
    "reverse-individual-stock": {
      "artifact_sha256": "17ce1e45172b10d51b1b4b705817b4baacf1aea8161960aaff54192c32e77ced",
      "index_sha256": "1b03fe3cc1435d42f70ffd14e9528674275c8ae9fba2736458ea9247ec19f31e",
      "frames": 17,
      "leaf_curve_sha256": {
        "own-leaf-0": "78a85421dc8bea6bb598d2d6cc5aba9a2f553bc31062df564c8b95ec2a0c6315",
        "own-leaf-1": "86e4b9288cc6ac2c53cfb2fb73adfd15bf99412b64ee457af6a673ba24243874",
        "own-leaf-2": "0e84993699a6d14a6ae25ccfe2d16ced63db16d7aa801a9343150f7294e1fc00"
      }
    },
    "cool-dark-individual-stock": {
      "artifact_sha256": "79fb65ce0e344d5cbfed0fa57b4983b7d788376515577f2db178e8e42516760e",
      "index_sha256": "3322ed8b4fa5e01e1a27f72946e38f8dd805f1f3dc11681aaf71314285a1bbfa",
      "frames": 17,
      "leaf_curve_sha256": {
        "own-leaf-0": "78a85421dc8bea6bb598d2d6cc5aba9a2f553bc31062df564c8b95ec2a0c6315",
        "own-leaf-1": "86e4b9288cc6ac2c53cfb2fb73adfd15bf99412b64ee457af6a673ba24243874",
        "own-leaf-2": "0e84993699a6d14a6ae25ccfe2d16ced63db16d7aa801a9343150f7294e1fc00"
      }
    },
    "warm-reference30-individual-stock": {
      "artifact_sha256": "e180a053c1486993fabdce29f55689fe34cddf9453e020789b62634a710105ff",
      "index_sha256": "70018e62693000b63dcafae1ca46b3c276455cb62d65872bb327d857ed1ee34c",
      "frames": 17,
      "leaf_curve_sha256": {
        "own-leaf-0": "78a85421dc8bea6bb598d2d6cc5aba9a2f553bc31062df564c8b95ec2a0c6315",
        "own-leaf-1": "86e4b9288cc6ac2c53cfb2fb73adfd15bf99412b64ee457af6a673ba24243874",
        "own-leaf-2": "0e84993699a6d14a6ae25ccfe2d16ced63db16d7aa801a9343150f7294e1fc00"
      }
    },
    "warm-reference22-individual-stock": {
      "artifact_sha256": "d38d3db364b9b9aac7e941865c780efffeeb322453d6896579c6bdb46e3bca79",
      "index_sha256": "2dc436e293884bc8948e2b8b27246f04933e2ace0602595bc837caf7cca3e81a",
      "frames": 17,
      "leaf_curve_sha256": {
        "own-leaf-0": "78a85421dc8bea6bb598d2d6cc5aba9a2f553bc31062df564c8b95ec2a0c6315",
        "own-leaf-1": "86e4b9288cc6ac2c53cfb2fb73adfd15bf99412b64ee457af6a673ba24243874",
        "own-leaf-2": "0e84993699a6d14a6ae25ccfe2d16ced63db16d7aa801a9343150f7294e1fc00"
      }
    },
    "empty-entry-individual-stock": {
      "artifact_sha256": "a3096c431fc16f9571ade80d1ecb3676cdb3706aa2ef3704d10dc0f2ffe96f2f",
      "index_sha256": "78eeda1ce5f218d081bd06796fd5b83158bde9dc78144a7099666967415d87d1",
      "frames": 17,
      "leaf_curve_sha256": {
        "own-leaf-0": "78a85421dc8bea6bb598d2d6cc5aba9a2f553bc31062df564c8b95ec2a0c6315",
        "own-leaf-1": "86e4b9288cc6ac2c53cfb2fb73adfd15bf99412b64ee457af6a673ba24243874",
        "own-leaf-2": "0e84993699a6d14a6ae25ccfe2d16ced63db16d7aa801a9343150f7294e1fc00"
      }
    }
  },
  "code_sha256": {
    "backend/app/content_access.py": "fbc59919453a79dd84481d31a0728b7acef9ecfa55df0e3c477baa433473375e",
    "backend/app/crop_area_canopy_energy.py": "8a6c7b8fb772d550bcda63d13185f180ad082c9f5e6e05937cce20bb3edebba8",
    "backend/app/crop_canopy_energy_transport.py": "389f8c68c5259d20d3bb5d61e191791c6df112eb8b24c7cd1d5020e7da4e579c",
    "backend/app/crop_canopy_exchange.py": "e3092000d405e5033126df5bbb506016fd502ff59b3ef14ae4d762e03d79a8e7",
    "backend/app/crop_explicit_lai_carbon_cohorts.py": "5c3e305f317205b36bac037aaf8a4a0c2342d5ed44a1169a0cffdd0905873541",
    "backend/app/crop_explicit_lai_climate_rhs.py": "92298f609d5225955ed153e5c2c194a012697ed38ca4b6d032dc552475f713f0",
    "backend/app/crop_explicit_lai_photosynthesis.py": "74c12d319768a877c12b3a55f4e60eaf04e08b9298aac81b785600c87d0ffbd8",
    "backend/app/crop_fruit_allocation.py": "4ef0ad3ce30116e1499b017ab46bad7e60641a8dfb1eafe7765b58844d4d949c",
    "backend/app/crop_fruit_cohorts.py": "b4f5a6e1ce2e7c993e21956f6c526aaa83c901814bc13603dfa72f9115d2a740",
    "backend/app/crop_fruit_startup.py": "3d9f6b038d97e5de85cef11275410d2f47035c5804954b1fe72b1755c95fadde",
    "backend/app/crop_fruit_transport.py": "5f2999ad240048035a9fd41e5862ee3f95caa73f7a53eb9594d2b55e517cc2a3",
    "backend/app/crop_growing_geometry_climate.py": "5cf58d1dea92e59e1059d5e5cd359a81b8dde950fed2ac575911a4be90788a0a",
    "backend/app/crop_growth_rates.py": "d8270e642dc80a747dd7d449094351369abb135a4663c3bf9fcdb1be5cd75858",
    "backend/app/crop_leaf_area.py": "a8e1182a5630df592ae98cf0fe79c840207bd478a30391280f837f092232c5a6",
    "backend/app/crop_leaf_area_change.py": "3f5b8f21df8911f3dfc70b63ff1d231d6a85e5f36f2a0fddc265ed3a01bfcfdd",
    "backend/app/crop_leaf_carbon_partition.py": "6b80b6611ac1f972158fe00fea92c9b0b99af3d94f942ec2710b6fea26c81266",
    "backend/app/crop_leaf_carbon_stock_artifact_producer.py": "98f5997eefd0857402a782cf39d0e1db729b38b4678f71d25115c4000cc8f679",
    "backend/app/crop_leaf_carbon_stock_artifact_reader.py": "37d6cc94f20d85a1d5e37ae0ff3f4466c3ab3b563768543f2d40e204cb2f0225",
    "backend/app/crop_leaf_carbon_stock_continuation.py": "62b7ba4c8dbcf56297fde3e2c8ef78e55efe283eab85b9f26640f917236e8f0d",
    "backend/app/crop_leaf_carbon_stock_dynamics.py": "0e2a51a23b95b10cfc15d46f5668266f2b7981a769d966a167f9a4a9cafdf80d",
    "backend/app/crop_leaf_carbon_stock_rhs.py": "1da1cfef06860893b9ef4f661b15e5d7b4bc099a8d6563c4a9c6bd23156ab4be",
    "backend/app/crop_leaf_expansion.py": "7dfbc855b619d01139ae0dab84b7097cbc33a5b8d4e472ae143c442d124d53a6",
    "backend/app/crop_leaf_partition_climate_rhs.py": "a708f13ed9290f4353e61310959aeab8f2f4bf0c3c4f02d5f9d0181fc3aebab3",
    "backend/app/crop_morphology_artifact_io.py": "217c98d6d24596882d9cf36a4465b75edcfce31ff82bf5acb7a0b348df111c79",
    "backend/app/crop_morphology_artifact_reader.py": "89e1a23526edc951aec39f1ac647cee407ee515590537902afa17d34b04ad2b2",
    "backend/app/crop_morphology_thermal_clock.py": "3f72d0bb4699232d9c3a264e9e3e61a10eb84530bd50caa84905fdf5d0b55334",
    "backend/app/crop_plant_cohort_rates.py": "fb84e52281c4b8fc05457ca724d3b7fec4c0794a1281480b267aac695fc795a6",
    "backend/app/job_store.py": "9b54b6be6765b62c1ba66f8938f8023bf5e882193d580ee3fd0c6d5ba1f80ca7",
    "backend/app/thermal_run_store.py": "3d3fbaee88e4d60ea95f574dfff57d1b32ac2d12eb8d2512ccfa4e4e3705a6c8"
  },
  "engine_identity": {
    "byteorder": "little",
    "component_code_sha256": {
      "app.crop_area_canopy_energy": "8a6c7b8fb772d550bcda63d13185f180ad082c9f5e6e05937cce20bb3edebba8",
      "app.crop_canopy_energy_transport": "389f8c68c5259d20d3bb5d61e191791c6df112eb8b24c7cd1d5020e7da4e579c",
      "app.crop_canopy_exchange": "e3092000d405e5033126df5bbb506016fd502ff59b3ef14ae4d762e03d79a8e7",
      "app.crop_explicit_lai_carbon_cohorts": "5c3e305f317205b36bac037aaf8a4a0c2342d5ed44a1169a0cffdd0905873541",
      "app.crop_explicit_lai_climate_rhs": "92298f609d5225955ed153e5c2c194a012697ed38ca4b6d032dc552475f713f0",
      "app.crop_explicit_lai_photosynthesis": "74c12d319768a877c12b3a55f4e60eaf04e08b9298aac81b785600c87d0ffbd8",
      "app.crop_fruit_cohorts": "b4f5a6e1ce2e7c993e21956f6c526aaa83c901814bc13603dfa72f9115d2a740",
      "app.crop_fruit_startup": "3d9f6b038d97e5de85cef11275410d2f47035c5804954b1fe72b1755c95fadde",
      "app.crop_fruit_transport": "5f2999ad240048035a9fd41e5862ee3f95caa73f7a53eb9594d2b55e517cc2a3",
      "app.crop_growing_geometry_climate": "5cf58d1dea92e59e1059d5e5cd359a81b8dde950fed2ac575911a4be90788a0a",
      "app.crop_growth_rates": "d8270e642dc80a747dd7d449094351369abb135a4663c3bf9fcdb1be5cd75858",
      "app.crop_leaf_carbon_partition": "6b80b6611ac1f972158fe00fea92c9b0b99af3d94f942ec2710b6fea26c81266",
      "app.crop_leaf_carbon_stock_rhs": "1da1cfef06860893b9ef4f661b15e5d7b4bc099a8d6563c4a9c6bd23156ab4be",
      "app.crop_leaf_partition_climate_rhs": "a708f13ed9290f4353e61310959aeab8f2f4bf0c3c4f02d5f9d0181fc3aebab3",
      "app.crop_plant_cohort_rates": "fb84e52281c4b8fc05457ca724d3b7fec4c0794a1281480b267aac695fc795a6",
      "crop_leaf_area": "a8e1182a5630df592ae98cf0fe79c840207bd478a30391280f837f092232c5a6",
      "crop_leaf_area_change": "3f5b8f21df8911f3dfc70b63ff1d231d6a85e5f36f2a0fddc265ed3a01bfcfdd",
      "crop_leaf_expansion": "7dfbc855b619d01139ae0dab84b7097cbc33a5b8d4e472ae143c442d124d53a6",
      "crop_morphology_thermal_clock": "3f72d0bb4699232d9c3a264e9e3e61a10eb84530bd50caa84905fdf5d0b55334"
    },
    "engine_code_sha256": "62b7ba4c8dbcf56297fde3e2c8ef78e55efe283eab85b9f26640f917236e8f0d",
    "engine_version": "leaf-carbon-stock-dynamics-continuation-research-v1",
    "float_mant_dig": 53,
    "float_radix": 2,
    "platform_machine": "x86_64",
    "platform_system": "Linux",
    "policies": {
      "capacity_policy": "declared_outflow_plus_area_capacity_derivative_v1",
      "leaf_stock_policy": "leaf-stocks-uniform-maintenance-explicit-removal-v1",
      "normalization": "zero_lower_asymptote_sigmoid_v1",
      "thermal_age_policy": "dynamic_indoor_air_no_clip_v1"
    },
    "profile_sha256": {
      "cohort": "b453b4ffe618f26041e4ec6a1b1b7d2e5f38edb3d42adaaad4fa3cd4fbb99cbb",
      "exchange": "1e032ced2ffdaf8ba713184e89b628cce4173c9e7231f30710afeda8fbf20110",
      "growth": "d606d44c5ea6494820d0b182d08536524acdb88508a9f676788523b1248e83ca",
      "transport": "09ea5e176bc745361e8e3ec8945b0f8abb0b2b427b4e9c459d0663cf390e9070"
    },
    "python_version": "3.12.3",
    "short_code_sha256": "0e2a51a23b95b10cfc15d46f5668266f2b7981a769d966a167f9a4a9cafdf80d",
    "state_schema": "individual-leaf-carbon-area-vector-v1"
  },
  "notice_sha256": "96ce8c1f3d7b5473f473417c2785c63b74148edaddc2b9b6d40a6bbe3b7f4b6a",
  "exporter_sha256": "df2c3e65cbcd6fbd5b30a337c5983a1198db14d5c5edb62df6cbe707a5c1a839"
} as const;
