// Public synthetic response from the recorded, cleaned-up SCRAM/TLS acceptance test.
// Not live user history; import only from tests or the explicit dev demo.
export const cropReferenceArtifactSha256='bf71b4c4bb3b7a7ebc460744622cbc5af5f77ccfb255037c355cabd07eb135ab';
const recorded={
  "result_id": "crop-result-v1:3289adab5b96bcdcdb01176edf5f3c61c6e3efd253caef9b7cba3f9ce7bd561d",
  "recorded_at": "2026-10-04T13:09:26.768872Z",
  "study_id": "study-1",
  "revision": "r1",
  "farm": {
    "scenario_id": "farm-1",
    "scenario_revision": "r1",
    "registration_sha256": "bc7b497922ece37822071f85cbd08866ab8949e3c173e45f4f2f66872601497b",
    "crop_id": "crop-1"
  },
  "batch_id": "batch-1",
  "zone_id": "zone-1",
  "farm_sha256": "dd3f9e8894d75236026d6a08c2e475424bb747b073cd2a9fd97ee6bf50f2030b",
  "source_binding_sha256": "fcb6e94ae95fed50fdc977a1f3680ded3ae3b632949a7a5cb22fd18d3151faa4",
  "storage_status": "stored_unpublished_research",
  "claim_scope": "synthetic_crop_math_only",
  "scope": "software_research_only",
  "gates": "not_assessed",
  "normalization": "per_m2_floor",
  "profile_applicability": "unvalidated_for_registered_crop",
  "temporal_provenance": "synthetic_research_program",
  "start_utc": "2026-10-01T00:00:00Z",
  "end_utc": "2026-10-01T00:05:00Z",
  "status": "completed",
  "steps": 30,
  "planned_steps": 30,
  "manifest": {
    "integrator_version": "crop-rk4-research-v1",
    "rate_model_version": "vanthoor-greenlight-carbon-rates-v1",
    "domain_policy": "vanthoor-bounded-photosynthesis-v1",
    "profile_id": "vanthoor-greenlight-reference-rates-v1",
    "profile_sha256": "d606d44c5ea6494820d0b182d08536524acdb88508a9f676788523b1248e83ca",
    "code_sha256": {
      "integrator": "dbcff4fc502b562ebe148356abe88eceed86273d58feaa18ee91c9222fad2e8a",
      "rates": "d8270e642dc80a747dd7d449094351369abb135a4663c3bf9fcdb1be5cd75858"
    },
    "storage_code_sha256": "912f2e3daf993bc3b39e51c87f16d4d05c9c56a68269fbfb119b8ea1f962365a",
    "input_sha256": "36bde9d426d97945bd25bf5d1c17c9a1273dc6f0f614d4fa31edf67b230d490a",
    "raw_program_sha256": "8eb55f00420fc75047e7f474834e8fdb3e0c9e4f5e493a1ec9d3ccce5b8f3d86",
    "result_sha256": "74f1daeed78510562eeca0727186378216e9130dc69dd5104d9efc0f80e25157",
    "payload_sha256": "2ce5cd3a0e2123f80ea9c9a1b44c0fe1ae3dedba38bc13f8314d2f4ca0432d9f",
    "notice_sha256": "96ce8c1f3d7b5473f473417c2785c63b74148edaddc2b9b6d40a6bbe3b7f4b6a",
    "solver": {
      "method": "rk4-fixed-v1",
      "max_step_seconds": 10,
      "max_steps": 10000,
      "roundoff_rule": "64-ulp-per-operation-v1"
    },
    "time_rule": "UTC_POSIX_whole_seconds_v1",
    "python_version": "3.12.3",
    "convergence": "not_evaluated_for_this_program",
    "temperature_sum_method": "analytic_piecewise_constant_fraction_v1"
  },
  "samples": [
    {
      "at": "2026-10-01T00:00:00Z",
      "state": {
        "buffer": {
          "value": 20000.0,
          "unit": "mg_CH2O/m2_floor"
        },
        "leaf": {
          "value": 4368.0,
          "unit": "mg_CH2O/m2_floor"
        },
        "stem_root": {
          "value": 1560.0,
          "unit": "mg_CH2O/m2_floor"
        },
        "fruit": {
          "value": 312.0,
          "unit": "mg_CH2O/m2_floor"
        },
        "temperature_filtered_24h": {
          "value": 20.5,
          "unit": "degC"
        },
        "temperature_sum": {
          "value": 0.0,
          "unit": "degC_day"
        }
      },
      "lai": {
        "value": 0.1161888,
        "unit": "m2_leaf/m2_floor"
      },
      "cumulative": {
        "photosynthesis": {
          "value": 0.0,
          "unit": "mg_CH2O/m2_floor"
        },
        "growth_respiration": {
          "value": 0.0,
          "unit": "mg_CH2O/m2_floor"
        },
        "maintenance_leaf": {
          "value": 0.0,
          "unit": "mg_CH2O/m2_floor"
        },
        "maintenance_stem_root": {
          "value": 0.0,
          "unit": "mg_CH2O/m2_floor"
        },
        "maintenance_fruit": {
          "value": 0.0,
          "unit": "mg_CH2O/m2_floor"
        },
        "removal_leaf": {
          "value": 0.0,
          "unit": "mg_CH2O/m2_floor"
        },
        "removal_stem_root": {
          "value": 0.0,
          "unit": "mg_CH2O/m2_floor"
        },
        "removal_fruit": {
          "value": 0.0,
          "unit": "mg_CH2O/m2_floor"
        }
      },
      "carbon_residual": {
        "value": 0.0,
        "unit": "mg_CH2O/m2_floor"
      },
      "carbon_residual_budget": {
        "value": 2.3283064365386963e-10,
        "unit": "mg_CH2O/m2_floor"
      }
    },
    {
      "at": "2026-10-01T00:01:00Z",
      "state": {
        "buffer": {
          "value": 19989.47189805538,
          "unit": "mg_CH2O/m2_floor"
        },
        "leaf": {
          "value": 4373.735066806805,
          "unit": "mg_CH2O/m2_floor"
        },
        "stem_root": {
          "value": 1564.509110835354,
          "unit": "mg_CH2O/m2_floor"
        },
        "fruit": {
          "value": 312.09808531697723,
          "unit": "mg_CH2O/m2_floor"
        },
        "temperature_filtered_24h": {
          "value": 20.499652898313144,
          "unit": "degC"
        },
        "temperature_sum": {
          "value": 0.013888888888888888,
          "unit": "degC_day"
        }
      },
      "lai": {
        "value": 0.11634135277706101,
        "unit": "m2_leaf/m2_floor"
      },
      "cumulative": {
        "photosynthesis": {
          "value": 2.89957719984378,
          "unit": "mg_CH2O/m2_floor"
        },
        "growth_respiration": {
          "value": 3.0071385347210544,
          "unit": "mg_CH2O/m2_floor"
        },
        "maintenance_leaf": {
          "value": 0.06660327479150845,
          "unit": "mg_CH2O/m2_floor"
        },
        "maintenance_stem_root": {
          "value": 0.010084807152487297,
          "unit": "mg_CH2O/m2_floor"
        },
        "maintenance_fruit": {
          "value": 0.0015895686605226138,
          "unit": "mg_CH2O/m2_floor"
        },
        "removal_leaf": {
          "value": 0.0,
          "unit": "mg_CH2O/m2_floor"
        },
        "removal_stem_root": {
          "value": 0.0,
          "unit": "mg_CH2O/m2_floor"
        },
        "removal_fruit": {
          "value": 0.0,
          "unit": "mg_CH2O/m2_floor"
        }
      },
      "carbon_residual": {
        "value": -1.4653276422110784e-12,
        "unit": "mg_CH2O/m2_floor"
      },
      "carbon_residual_budget": {
        "value": 1.6298145055770874e-09,
        "unit": "mg_CH2O/m2_floor"
      }
    },
    {
      "at": "2026-10-01T00:02:00Z",
      "state": {
        "buffer": {
          "value": 19978.95520399632,
          "unit": "mg_CH2O/m2_floor"
        },
        "leaf": {
          "value": 4379.46996211711,
          "unit": "mg_CH2O/m2_floor"
        },
        "stem_root": {
          "value": 1569.0181260424274,
          "unit": "mg_CH2O/m2_floor"
        },
        "fruit": {
          "value": 312.19630320862177,
          "unit": "mg_CH2O/m2_floor"
        },
        "temperature_filtered_24h": {
          "value": 20.499306037585452,
          "unit": "degC"
        },
        "temperature_sum": {
          "value": 0.027777777777777776,
          "unit": "degC_day"
        }
      },
      "lai": {
        "value": 0.11649390099231513,
        "unit": "m2_leaf/m2_floor"
      },
      "cumulative": {
        "photosynthesis": {
          "value": 5.810534738154382,
          "unit": "mg_CH2O/m2_floor"
        },
        "growth_respiration": {
          "value": 6.014268960979349,
          "unit": "mg_CH2O/m2_floor"
        },
        "maintenance_leaf": {
          "value": 0.13329233526678616,
          "unit": "mg_CH2O/m2_floor"
        },
        "maintenance_stem_root": {
          "value": 0.020198478371309628,
          "unit": "mg_CH2O/m2_floor"
        },
        "maintenance_fruit": {
          "value": 0.003179599060250177,
          "unit": "mg_CH2O/m2_floor"
        },
        "removal_leaf": {
          "value": 0.0,
          "unit": "mg_CH2O/m2_floor"
        },
        "removal_stem_root": {
          "value": 0.0,
          "unit": "mg_CH2O/m2_floor"
        },
        "removal_fruit": {
          "value": 0.0,
          "unit": "mg_CH2O/m2_floor"
        }
      },
      "carbon_residual": {
        "value": 2.845882383917253e-12,
        "unit": "mg_CH2O/m2_floor"
      },
      "carbon_residual_budget": {
        "value": 3.026798367500305e-09,
        "unit": "mg_CH2O/m2_floor"
      }
    },
    {
      "at": "2026-10-01T00:03:00Z",
      "state": {
        "buffer": {
          "value": 19967.551337954807,
          "unit": "mg_CH2O/m2_floor"
        },
        "leaf": {
          "value": 4284.604942982472,
          "unit": "mg_CH2O/m2_floor"
        },
        "stem_root": {
          "value": 1573.5272453109808,
          "unit": "mg_CH2O/m2_floor"
        },
        "fruit": {
          "value": 312.2945433628674,
          "unit": "mg_CH2O/m2_floor"
        },
        "temperature_filtered_24h": {
          "value": 20.50104202777077,
          "unit": "degC"
        },
        "temperature_sum": {
          "value": 0.04375,
          "unit": "degC_day"
        }
      },
      "lai": {
        "value": 0.11397049148333374,
        "unit": "m2_leaf/m2_floor"
      },
      "cumulative": {
        "photosynthesis": {
          "value": 7.834742684323699,
          "unit": "mg_CH2O/m2_floor"
        },
        "growth_respiration": {
          "value": 9.021493695068772,
          "unit": "mg_CH2O/m2_floor"
        },
        "maintenance_leaf": {
          "value": 0.2000674269477034,
          "unit": "mg_CH2O/m2_floor"
        },
        "maintenance_stem_root": {
          "value": 0.030341744776683135,
          "unit": "mg_CH2O/m2_floor"
        },
        "maintenance_fruit": {
          "value": 0.004770206407359913,
          "unit": "mg_CH2O/m2_floor"
        },
        "removal_leaf": {
          "value": 100.6,
          "unit": "mg_CH2O/m2_floor"
        },
        "removal_stem_root": {
          "value": 0.0,
          "unit": "mg_CH2O/m2_floor"
        },
        "removal_fruit": {
          "value": 0.0,
          "unit": "mg_CH2O/m2_floor"
        }
      },
      "carbon_residual": {
        "value": 3.086046175548862e-12,
        "unit": "mg_CH2O/m2_floor"
      },
      "carbon_residual_budget": {
        "value": 4.6566128730773926e-09,
        "unit": "mg_CH2O/m2_floor"
      }
    },
    {
      "at": "2026-10-01T00:04:00Z",
      "state": {
        "buffer": {
          "value": 19956.09544367603,
          "unit": "mg_CH2O/m2_floor"
        },
        "leaf": {
          "value": 4289.741790096504,
          "unit": "mg_CH2O/m2_floor"
        },
        "stem_root": {
          "value": 1578.036668051777,
          "unit": "mg_CH2O/m2_floor"
        },
        "fruit": {
          "value": 312.39294515178443,
          "unit": "mg_CH2O/m2_floor"
        },
        "temperature_filtered_24h": {
          "value": 20.502776812825843,
          "unit": "degC"
        },
        "temperature_sum": {
          "value": 0.059722222222222225,
          "unit": "degC_day"
        }
      },
      "lai": {
        "value": 0.11410713161656699,
        "unit": "m2_leaf/m2_floor"
      },
      "cumulative": {
        "photosynthesis": {
          "value": 9.808111018586018,
          "unit": "mg_CH2O/m2_floor"
        },
        "growth_respiration": {
          "value": 12.02898238848316,
          "unit": "mg_CH2O/m2_floor"
        },
        "maintenance_leaf": {
          "value": 0.2654048037715507,
          "unit": "mg_CH2O/m2_floor"
        },
        "maintenance_stem_root": {
          "value": 0.0405153442257092,
          "unit": "mg_CH2O/m2_floor"
        },
        "maintenance_fruit": {
          "value": 0.00636150601317159,
          "unit": "mg_CH2O/m2_floor"
        },
        "removal_leaf": {
          "value": 101.19999999999996,
          "unit": "mg_CH2O/m2_floor"
        },
        "removal_stem_root": {
          "value": 0.0,
          "unit": "mg_CH2O/m2_floor"
        },
        "removal_fruit": {
          "value": 0.0,
          "unit": "mg_CH2O/m2_floor"
        }
      },
      "carbon_residual": {
        "value": 2.1878800854358005e-12,
        "unit": "mg_CH2O/m2_floor"
      },
      "carbon_residual_budget": {
        "value": 6.05359673500061e-09,
        "unit": "mg_CH2O/m2_floor"
      }
    },
    {
      "at": "2026-10-01T00:05:00Z",
      "state": {
        "buffer": {
          "value": 19942.66628681699,
          "unit": "mg_CH2O/m2_floor"
        },
        "leaf": {
          "value": 4295.47846984229,
          "unit": "mg_CH2O/m2_floor"
        },
        "stem_root": {
          "value": 1582.5459948642695,
          "unit": "mg_CH2O/m2_floor"
        },
        "fruit": {
          "value": 289.4914262646866,
          "unit": "mg_CH2O/m2_floor"
        },
        "temperature_filtered_24h": {
          "value": 20.500345173345035,
          "unit": "degC"
        },
        "temperature_sum": {
          "value": 0.07152777777777777,
          "unit": "degC_day"
        }
      },
      "lai": {
        "value": 0.11425972729780491,
        "unit": "m2_leaf/m2_floor"
      },
      "cumulative": {
        "photosynthesis": {
          "value": 9.808111018586018,
          "unit": "mg_CH2O/m2_floor"
        },
        "growth_respiration": {
          "value": 15.0364463367365,
          "unit": "mg_CH2O/m2_floor"
        },
        "maintenance_leaf": {
          "value": 0.33082345622610865,
          "unit": "mg_CH2O/m2_floor"
        },
        "maintenance_stem_root": {
          "value": 0.0507178103629542,
          "unit": "mg_CH2O/m2_floor"
        },
        "maintenance_fruit": {
          "value": 0.00794562702594541,
          "unit": "mg_CH2O/m2_floor"
        },
        "removal_leaf": {
          "value": 101.19999999999996,
          "unit": "mg_CH2O/m2_floor"
        },
        "removal_stem_root": {
          "value": 0.0,
          "unit": "mg_CH2O/m2_floor"
        },
        "removal_fruit": {
          "value": 23.0,
          "unit": "mg_CH2O/m2_floor"
        }
      },
      "carbon_residual": {
        "value": 2.98853997104942e-12,
        "unit": "mg_CH2O/m2_floor"
      },
      "carbon_residual_budget": {
        "value": 7.683411240577698e-09,
        "unit": "mg_CH2O/m2_floor"
      }
    }
  ],
  "events": [
    {
      "at": "2026-10-01T00:03:00Z",
      "removals": {
        "leaf": {
          "value": 100.0,
          "unit": "mg_CH2O/m2_floor"
        },
        "stem_root": {
          "value": 0.0,
          "unit": "mg_CH2O/m2_floor"
        },
        "fruit": {
          "value": 0.0,
          "unit": "mg_CH2O/m2_floor"
        }
      },
      "before": {
        "buffer": {
          "value": 19967.551337954807,
          "unit": "mg_CH2O/m2_floor"
        },
        "leaf": {
          "value": 4384.604942982472,
          "unit": "mg_CH2O/m2_floor"
        },
        "stem_root": {
          "value": 1573.5272453109808,
          "unit": "mg_CH2O/m2_floor"
        },
        "fruit": {
          "value": 312.2945433628674,
          "unit": "mg_CH2O/m2_floor"
        },
        "temperature_filtered_24h": {
          "value": 20.50104202777077,
          "unit": "degC"
        },
        "temperature_sum": {
          "value": 0.04375,
          "unit": "degC_day"
        }
      },
      "after": {
        "buffer": {
          "value": 19967.551337954807,
          "unit": "mg_CH2O/m2_floor"
        },
        "leaf": {
          "value": 4284.604942982472,
          "unit": "mg_CH2O/m2_floor"
        },
        "stem_root": {
          "value": 1573.5272453109808,
          "unit": "mg_CH2O/m2_floor"
        },
        "fruit": {
          "value": 312.2945433628674,
          "unit": "mg_CH2O/m2_floor"
        },
        "temperature_filtered_24h": {
          "value": 20.50104202777077,
          "unit": "degC"
        },
        "temperature_sum": {
          "value": 0.04375,
          "unit": "degC_day"
        }
      }
    },
    {
      "at": "2026-10-01T00:05:00Z",
      "removals": {
        "leaf": {
          "value": 0.0,
          "unit": "mg_CH2O/m2_floor"
        },
        "stem_root": {
          "value": 0.0,
          "unit": "mg_CH2O/m2_floor"
        },
        "fruit": {
          "value": 20.0,
          "unit": "mg_CH2O/m2_floor"
        }
      },
      "before": {
        "buffer": {
          "value": 19942.66628681699,
          "unit": "mg_CH2O/m2_floor"
        },
        "leaf": {
          "value": 4295.47846984229,
          "unit": "mg_CH2O/m2_floor"
        },
        "stem_root": {
          "value": 1582.5459948642695,
          "unit": "mg_CH2O/m2_floor"
        },
        "fruit": {
          "value": 309.4914262646866,
          "unit": "mg_CH2O/m2_floor"
        },
        "temperature_filtered_24h": {
          "value": 20.500345173345035,
          "unit": "degC"
        },
        "temperature_sum": {
          "value": 0.07152777777777777,
          "unit": "degC_day"
        }
      },
      "after": {
        "buffer": {
          "value": 19942.66628681699,
          "unit": "mg_CH2O/m2_floor"
        },
        "leaf": {
          "value": 4295.47846984229,
          "unit": "mg_CH2O/m2_floor"
        },
        "stem_root": {
          "value": 1582.5459948642695,
          "unit": "mg_CH2O/m2_floor"
        },
        "fruit": {
          "value": 289.4914262646866,
          "unit": "mg_CH2O/m2_floor"
        },
        "temperature_filtered_24h": {
          "value": 20.500345173345035,
          "unit": "degC"
        },
        "temperature_sum": {
          "value": 0.07152777777777777,
          "unit": "degC_day"
        }
      }
    }
  ],
  "hold": null
};
export const cropReferenceSelection={result_id:recorded.result_id,...recorded.farm};
export function cropReferenceResponse():unknown{return structuredClone(recorded);}

// Public numeric hold from the actual saved HTTPS/browser acceptance test.
const held={
  "result_id": "crop-result-v1:fcd33e260549db1a10e8c5d0ac05942060d63231a3dd9d5987298a8b9d58ee49",
  "recorded_at": "2026-10-04T13:55:52.959125Z",
  "study_id": "study-1",
  "revision": "web-numeric-hold",
  "farm": {
    "scenario_id": "farm-1",
    "scenario_revision": "r1",
    "registration_sha256": "38e7f861af5f535b4fa955960fa619db106dc5573618c9aa87621a409acc8e83",
    "crop_id": "crop-1"
  },
  "batch_id": "batch-1",
  "zone_id": "zone-1",
  "farm_sha256": "271356bcb0356f96dd6baeec4567e2be549857d63e31733eeda14ac2daf16cf8",
  "source_binding_sha256": "5fcf0e2d81f1163a630b58d0d6246e7db191333f92d0f680327f1bb20ebb480a",
  "storage_status": "stored_unpublished_research",
  "claim_scope": "synthetic_crop_math_only",
  "scope": "software_research_only",
  "gates": "not_assessed",
  "normalization": "per_m2_floor",
  "profile_applicability": "unvalidated_for_registered_crop",
  "temporal_provenance": "synthetic_research_program",
  "start_utc": "2026-10-01T00:00:00Z",
  "end_utc": "2026-10-01T00:05:00Z",
  "status": "hold",
  "steps": 0,
  "planned_steps": 30,
  "manifest": {
    "integrator_version": "crop-rk4-research-v1",
    "rate_model_version": "vanthoor-greenlight-carbon-rates-v1",
    "domain_policy": "vanthoor-bounded-photosynthesis-v1",
    "profile_id": "vanthoor-greenlight-reference-rates-v1",
    "profile_sha256": "d606d44c5ea6494820d0b182d08536524acdb88508a9f676788523b1248e83ca",
    "code_sha256": {
      "integrator": "dbcff4fc502b562ebe148356abe88eceed86273d58feaa18ee91c9222fad2e8a",
      "rates": "d8270e642dc80a747dd7d449094351369abb135a4663c3bf9fcdb1be5cd75858"
    },
    "storage_code_sha256": "912f2e3daf993bc3b39e51c87f16d4d05c9c56a68269fbfb119b8ea1f962365a",
    "input_sha256": "c71dfd5bbd12950190e4c9a3812c7a5862fbd7bd36d9d8ef32da59a622c93fae",
    "raw_program_sha256": "53b62deb4f1813c3a4737cc3886e5c47dc6751cd7baa7875bc5807e25f09be73",
    "result_sha256": "8de29655b6f6c38ee69f084b84e36f0941dce158765d261551980cfd6d68dfd5",
    "payload_sha256": "2797f98f22027b70544bb96a2926a35f3e625336934cac7d838e46d8d14e8281",
    "notice_sha256": "96ce8c1f3d7b5473f473417c2785c63b74148edaddc2b9b6d40a6bbe3b7f4b6a",
    "solver": {
      "method": "rk4-fixed-v1",
      "max_step_seconds": 10,
      "max_steps": 10000,
      "roundoff_rule": "64-ulp-per-operation-v1"
    },
    "time_rule": "UTC_POSIX_whole_seconds_v1",
    "python_version": "3.12.3",
    "convergence": "not_evaluated_for_this_program",
    "temperature_sum_method": "analytic_piecewise_constant_fraction_v1"
  },
  "samples": [],
  "events": [],
  "hold": {
    "reason_code": "DEPLETED_STATE_HOLD",
    "attempted_at": "2026-10-01T00:00:00Z",
    "phase": "boundary",
    "time_meaning": "solver_evaluation_time",
    "last_confirmed": null,
    "failed_state": {
      "buffer": {
        "value": 0.0,
        "unit": "mg_CH2O/m2_floor"
      },
      "leaf": {
        "value": 4368.0,
        "unit": "mg_CH2O/m2_floor"
      },
      "stem_root": {
        "value": 1560.0,
        "unit": "mg_CH2O/m2_floor"
      },
      "fruit": {
        "value": 312.0,
        "unit": "mg_CH2O/m2_floor"
      },
      "temperature_filtered_24h": {
        "value": 20.5,
        "unit": "degC"
      },
      "temperature_sum": {
        "value": 0.0,
        "unit": "degC_day"
      }
    }
  }
};
export const cropHoldReferenceSelection={result_id:held.result_id,...held.farm};
export function cropHoldReferenceResponse():unknown{return structuredClone(held);}
